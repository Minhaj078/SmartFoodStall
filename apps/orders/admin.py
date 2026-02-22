from django.contrib import admin
from .models import Order, OrderItem, DemandForecast, OrderAnalytics


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price_at_order']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'token_number', 'user', 'stall', 'break_slot', 'pickup_date', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'break_slot', 'pickup_date', 'stall']
    search_fields = ['token_number', 'user__username', 'stall__name']
    inlines = [OrderItemInline]
    readonly_fields = ['token_number', 'created_at', 'updated_at']
    actions = ['mark_confirmed', 'mark_preparing', 'mark_ready', 'mark_completed']

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_confirmed.short_description = "Mark as Confirmed"

    def mark_preparing(self, request, queryset):
        queryset.update(status='preparing')
    mark_preparing.short_description = "Mark as Preparing"

    def mark_ready(self, request, queryset):
        queryset.update(status='ready')
    mark_ready.short_description = "Mark as Ready for Pickup"

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = "Mark as Completed"


@admin.register(DemandForecast)
class DemandForecastAdmin(admin.ModelAdmin):
    list_display = ['stall', 'break_slot', 'forecast_date', 'predicted_quantity', 'actual_quantity', 'confidence_score']
    list_filter = ['stall', 'break_slot']


@admin.register(OrderAnalytics)
class OrderAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['stall', 'date', 'break_slot', 'total_orders', 'total_revenue', 'peak_hour']
