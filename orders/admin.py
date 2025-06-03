from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Wishlist, OrderStatusHistory

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_items', 'total_price']
    inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product__name']
    readonly_fields = ['total_price', 'added_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price', 'created_at']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['changed_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'buyer__username', 'buyer__email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'total_items']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'buyer', 'status', 'payment_status', 'payment_method')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount')
        }),
        ('Shipping Address', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state',
                      'shipping_postal_code', 'shipping_country')
        }),
        ('Billing Address', {
            'fields': ('billing_address', 'billing_city', 'billing_state',
                      'billing_postal_code', 'billing_country'),
            'classes': ('collapse',)
        }),
        ('Delivery', {
            'fields': ('preferred_delivery_date', 'delivery_instructions',
                      'tracking_number', 'estimated_delivery_date', 'actual_delivery_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'seller', 'quantity', 'unit_price', 'total_price', 'status']
    list_filter = ['status', 'quality_grade', 'created_at']
    search_fields = ['order__order_number', 'product__name', 'seller__username']
    readonly_fields = ['total_price', 'created_at']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['added_at']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'previous_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['previous_status', 'new_status', 'changed_at']
    search_fields = ['order__order_number', 'changed_by__username']
    readonly_fields = ['changed_at']
