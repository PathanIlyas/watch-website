from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    
    # Products
    path('products/', views.product_list, name='dashboard_products'),
    path('products/add/', views.product_create, name='dashboard_product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='dashboard_product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='dashboard_product_delete'),
    
    # Orders
    path('orders/', views.order_list, name='dashboard_orders'),
    path('orders/<int:pk>/update/', views.order_update, name='dashboard_order_update'),
    
    # Users
    path('users/', views.user_list, name='dashboard_users'),
    
    # Categories
    path('categories/', views.category_list, name='dashboard_categories'),
    path('categories/add/', views.category_create, name='dashboard_category_create'),
    
    # Banners
    path('banners/', views.banner_list, name='dashboard_banners'),
    path('banners/add/', views.banner_create, name='dashboard_banner_create'),
    
    # Contacts
    path('contacts/', views.contact_list, name='dashboard_contacts'),
    path('contacts/<int:pk>/read/', views.contact_mark_read, name='dashboard_contact_mark_read'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='dashboard_contact_delete'),

    # Payments
    path('payments/', views.payment_list, name='dashboard_payments'),

    # OTP Logs
    path('otp/', views.otp_dashboard, name='dashboard_otp'),
]
