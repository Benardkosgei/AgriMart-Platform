from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    """Custom User model with buyer/seller functionality"""
    
    USER_TYPES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='buyer')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number format: '+999999999'")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"

class SellerProfile(models.Model):
    """Additional profile information for sellers"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200)
    business_license = models.CharField(max_length=100, blank=True)
    farm_location = models.TextField()
    farm_size = models.CharField(max_length=100, blank=True)
    organic_certified = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business_name} - {self.user.username}"

class BuyerProfile(models.Model):
    """Additional profile information for buyers"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    preferred_delivery_time = models.CharField(max_length=100, blank=True)
    dietary_preferences = models.TextField(blank=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Buyer Profile - {self.user.username}"
