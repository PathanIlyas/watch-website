from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/', views.collection, name='collection'),
    path('product/<slug:slug>/', views.product, name='product'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
