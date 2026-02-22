from django.contrib import admin
from .models import FoodStall, MenuItem, StallReview


@admin.register(FoodStall)
class FoodStallAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location', 'is_open', 'created_at']
    list_filter = ['is_open']
    search_fields = ['name', 'location']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'stall', 'category', 'price', 'is_available', 'prep_time_minutes']
    list_filter = ['stall', 'category', 'is_available', 'is_vegetarian']
    search_fields = ['name', 'stall__name']


@admin.register(StallReview)
class StallReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'stall', 'rating', 'created_at']
