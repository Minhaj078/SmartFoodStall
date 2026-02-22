from django.db import models
from apps.users.models import User


class FoodStall(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stalls')
    image = models.ImageField(upload_to='stalls/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0


class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('snacks', 'Snacks'),
        ('meals', 'Meals'),
        ('beverages', 'Beverages'),
        ('desserts', 'Desserts'),
        ('combos', 'Combos'),
    ]
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='snacks')
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    prep_time_minutes = models.IntegerField(default=10)
    calories = models.IntegerField(null=True, blank=True)
    is_vegetarian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.stall.name}"


class StallReview(models.Model):
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stall', 'user')

    def __str__(self):
        return f"{self.user.username} rated {self.stall.name} - {self.rating}/5"
