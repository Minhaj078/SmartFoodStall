from django.urls import path
from . import views

urlpatterns = [
    path('', views.stall_list, name='stall_list'),
    path('<int:pk>/', views.stall_detail, name='stall_detail'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('api/menu-item/<int:pk>/', views.get_menu_item_api, name='menu_item_api'),
]
