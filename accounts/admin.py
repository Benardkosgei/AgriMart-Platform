from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SellerProfile, BuyerProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_verified', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_image', 'address',
                      'city', 'state', 'postal_code', 'country', 'is_verified')
        }),
    )

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'organic_certified', 'rating', 'total_sales']
    list_filter = ['organic_certified', 'created_at']
    search_fields = ['business_name', 'user__username', 'farm_location']
    readonly_fields = ['rating', 'total_sales', 'created_at']

@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_orders', 'total_spent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_orders', 'total_spent', 'created_at']
