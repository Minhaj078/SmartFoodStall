from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.stalls.models import FoodStall, MenuItem


BREAK_SLOT_CHOICES = [
    ('10:00', '10:00 AM - 10:20 AM'),
    ('12:00', '12:00 PM - 12:30 PM'),
    ('13:00', '1:00 PM - 1:30 PM'),
    ('15:00', '3:00 PM - 3:20 PM'),
]

ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('preparing', 'Preparing'),
    ('ready', 'Ready for Pickup'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name='orders')
    break_slot = models.CharField(max_length=5, choices=BREAK_SLOT_CHOICES)
    pickup_date = models.DateField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True)
    token_number = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_ready_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - {self.break_slot}"

    def save(self, *args, **kwargs):
        if not self.token_number:
            from datetime import date
            today_str = date.today().strftime('%d%m')
            count = Order.objects.filter(
                stall=self.stall,
                pickup_date=self.pickup_date
            ).count() + 1
            self.token_number = f"{today_str}{count:03d}"
        super().save(*args, **kwargs)

    def calculate_total(self):
        total = sum(item.subtotal for item in self.order_items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    @property
    def estimated_prep_time(self):
        return sum(item.menu_item.prep_time_minutes * item.quantity for item in self.order_items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)
    customization = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.price_at_order * self.quantity

    def save(self, *args, **kwargs):
        if not self.price_at_order:
            self.price_at_order = self.menu_item.price
        super().save(*args, **kwargs)


class DemandForecast(models.Model):
    """Stores demand forecast data for AI-based prediction"""
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name='forecasts')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    break_slot = models.CharField(max_length=5, choices=BREAK_SLOT_CHOICES)
    forecast_date = models.DateField()
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    predicted_quantity = models.IntegerField(default=0)
    actual_quantity = models.IntegerField(default=0)
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stall', 'menu_item', 'break_slot', 'forecast_date')

    def __str__(self):
        return f"Forecast: {self.stall.name} | {self.break_slot} | {self.forecast_date}"


class OrderAnalytics(models.Model):
    """Daily analytics snapshot"""
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    break_slot = models.CharField(max_length=5, choices=BREAK_SLOT_CHOICES)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_prep_time = models.FloatField(default=0)
    peak_hour = models.BooleanField(default=False)

    class Meta:
        unique_together = ('stall', 'date', 'break_slot')
