from django import forms
from store.models import Watch, Category, WatchImage, HomepageBanner
from orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()

class WatchForm(forms.ModelForm):
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    
    class Meta:
        model = Watch
        fields = ['name', 'brand', 'slug', 'price', 'discount_price', 'description', 'features', 'stock_quantity', 'category', 'is_featured', 'is_trending']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_trending': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WatchImageForm(forms.ModelForm):
    class Meta:
        model = WatchImage
        fields = ['image', 'is_primary']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class BannerForm(forms.ModelForm):
    class Meta:
        model = HomepageBanner
        fields = ['title', 'subtitle', 'image', 'link', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
