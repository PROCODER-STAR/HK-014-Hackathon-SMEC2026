from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_catalog, name='catalog'),
    path('resource/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/booking/<int:pk>/approve/', views.approve_booking, name='approve_booking'),
    path('dashboard/booking/<int:pk>/reject/', views.reject_booking, name='reject_booking'),
    path('notifications/', views.notifications, name='notifications'),
]
