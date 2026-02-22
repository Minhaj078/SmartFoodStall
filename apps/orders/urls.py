from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('order/stall/<int:stall_id>/', views.place_order, name='place_order'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/update-status/<int:pk>/', views.update_order_status, name='update_order_status'),
    path('api/slot-demand/', views.slot_demand_api, name='slot_demand_api'),
    path('api/order-status/<int:pk>/', views.order_status_api, name='order_status_api'),
]
