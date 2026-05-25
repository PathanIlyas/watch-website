from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:watch_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('track/', views.track_order, name='track_order'),
]
