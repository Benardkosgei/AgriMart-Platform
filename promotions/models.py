from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product, Category
from decimal import Decimal
import uuid

User = get_user_model()

class Promotion(models.Model):
    """Base promotion model"""
    
    PROMOTION_TYPES = (
        ('discount', 'Discount'),
        ('bogo', 'Buy One Get One'),
        ('bundle', 'Bundle Deal'),
        ('cashback', 'Cashback'),
        ('free_shipping', 'Free Shipping'),
        ('loyalty_points', 'Loyalty Points'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    promotion_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    
    # Discount details
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Usage limits
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    # Minimum requirements
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    minimum_quantity = models.PositiveIntegerField(default=1)
    
    # Targeting
    target_products = models.ManyToManyField(Product, blank=True)
    target_categories = models.ManyToManyField(Category, blank=True)
    target_user_types = models.JSONField(default=list, blank=True)  # ['buyer', 'seller']
    
    # Priority and stacking
    priority = models.PositiveIntegerField(default=1)
    stackable = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_promotions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date', 'end_date']),
            models.Index(fields=['promotion_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.promotion_type})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.status == 'active' and 
                self.start_date <= now <= self.end_date and
                (not self.max_uses or self.current_uses < self.max_uses))

class Coupon(models.Model):
    """Coupon codes for promotions"""
    
    coupon_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=50, unique=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='coupons')
    
    # Usage tracking
    uses_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"Coupon: {self.code}"

class PromotionUsage(models.Model):
    """Track promotion usage by users"""
    
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promotion_usages')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    
    # Discount applied
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True)
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['promotion', 'user']),
            models.Index(fields=['user', 'used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} used {self.promotion.name}"

class LoyaltyProgram(models.Model):
    """Loyalty points program"""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Point rates
    points_per_spend = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)  # Points per KES
    points_value = models.DecimalField(max_digits=5, decimal_places=4, default=0.01)  # KES per point
    
    # Bonus multipliers
    signup_bonus = models.PositiveIntegerField(default=100)
    review_bonus = models.PositiveIntegerField(default=50)
    referral_bonus = models.PositiveIntegerField(default=200)
    
    # Tier benefits
    tier_thresholds = models.JSONField(default=dict)  # {tier_name: min_points}
    tier_multipliers = models.JSONField(default=dict)  # {tier_name: multiplier}
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class LoyaltyAccount(models.Model):
    """User loyalty account"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='accounts')
    
    # Points balance
    total_points_earned = models.PositiveIntegerField(default=0)
    points_redeemed = models.PositiveIntegerField(default=0)
    current_balance = models.PositiveIntegerField(default=0)
    
    # Tier information
    current_tier = models.CharField(max_length=50, default='Bronze')
    tier_progress = models.PositiveIntegerField(default=0)
    
    # Statistics
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'program']
    
    def __str__(self):
        return f"{self.user.username} - {self.current_balance} points"

class PointTransaction(models.Model):
    """Track loyalty point transactions"""
    
    TRANSACTION_TYPES = (
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('bonus', 'Bonus Points'),
        ('adjustment', 'Manual Adjustment'),
    )
    
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Positive for earned, negative for redeemed
    
    # Reference information
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    
    # Balance tracking
    balance_before = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.account.user.username} - {self.points} points"

class FlashSale(models.Model):
    """Flash sales with time-limited offers"""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Products on sale
    products = models.ManyToManyField(Product, through='FlashSaleProduct')
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Limits
    max_quantity_per_user = models.PositiveIntegerField(default=5)
    total_quantity_available = models.PositiveIntegerField(null=True, blank=True)
    quantity_sold = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return self.name
    
    @property
    def is_live(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.start_time <= now <= self.end_time and
                (not self.total_quantity_available or 
                 self.quantity_sold < self.total_quantity_available))

class FlashSaleProduct(models.Model):
    """Products in flash sale with specific pricing"""
    
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Pricing
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Stock limits for flash sale
    quantity_available = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['flash_sale', 'product']
    
    def __str__(self):
        return f"{self.product.name} in {self.flash_sale.name}"
    
    @property
    def is_available(self):
        return self.quantity_sold < self.quantity_available

class BundleDeal(models.Model):
    """Product bundle deals"""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Bundle products
    products = models.ManyToManyField(Product, through='BundleProduct')
    
    # Pricing
    total_regular_price = models.DecimalField(max_digits=12, decimal_places=2)
    bundle_price = models.DecimalField(max_digits=12, decimal_places=2)
    savings_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Usage tracking
    times_purchased = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class BundleProduct(models.Model):
    """Products in a bundle with quantities"""
    
    bundle = models.ForeignKey(BundleDeal, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['bundle', 'product']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.bundle.name}"

class SeasonalPromotion(models.Model):
    """Seasonal and holiday promotions"""
    
    SEASON_TYPES = (
        ('christmas', 'Christmas'),
        ('new_year', 'New Year'),
        ('easter', 'Easter'),
        ('harvest', 'Harvest Season'),
        ('rainy', 'Rainy Season'),
        ('dry', 'Dry Season'),
        ('valentine', 'Valentine\'s Day'),
        ('mothers_day', 'Mother\'s Day'),
        ('fathers_day', 'Father\'s Day'),
        ('independence', 'Independence Day'),
        ('custom', 'Custom Event'),
    )
    
    name = models.CharField(max_length=200)
    season_type = models.CharField(max_length=20, choices=SEASON_TYPES)
    description = models.TextField()
    
    # Visual elements
    banner_image = models.URLField(blank=True)
    theme_color = models.CharField(max_length=7, default='#000000')  # Hex color
    
    # Promotion details
    base_promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    
    # Special features
    gift_wrapping_available = models.BooleanField(default=False)
    special_delivery_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.season_type})"

class PromotionAnalytics(models.Model):
    """Daily promotion analytics"""
    
    date = models.DateField(unique=True)
    
    # Active promotions
    active_promotions = models.PositiveIntegerField(default=0)
    total_promotions = models.PositiveIntegerField(default=0)
    
    # Usage metrics
    promotion_uses = models.PositiveIntegerField(default=0)
    discount_amount_given = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    orders_with_promotions = models.PositiveIntegerField(default=0)
    
    # Coupon metrics
    coupons_redeemed = models.PositiveIntegerField(default=0)
    
    # Loyalty metrics
    points_earned = models.PositiveIntegerField(default=0)
    points_redeemed = models.PositiveIntegerField(default=0)
    new_loyalty_members = models.PositiveIntegerField(default=0)
    
    # Flash sale metrics
    flash_sale_orders = models.PositiveIntegerField(default=0)
    flash_sale_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Promotion Analytics - {self.date}"
