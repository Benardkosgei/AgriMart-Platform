from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()

class Category(models.Model):
    """Product categories (fruits, vegetables, grains, etc.)"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Agricultural products with quality assessment"""
    
    UNIT_CHOICES = (
        ('kg', 'Kilogram'),
        ('lbs', 'Pounds'),
        ('pieces', 'Pieces'),
        ('bunch', 'Bunch'),
        ('bag', 'Bag'),
        ('box', 'Box'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    )
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    quantity_available = models.PositiveIntegerField(default=0)
    minimum_order = models.PositiveIntegerField(default=1)
    harvest_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    origin_location = models.CharField(max_length=200)
    organic = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Quality assessment fields (populated by YOLO model)
    quality_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    quality_grade = models.CharField(max_length=1, blank=True)  # A, B, C, D
    quality_analyzed = models.BooleanField(default=False)
    quality_analysis_date = models.DateTimeField(blank=True, null=True)
    
    # SEO and metadata
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Tracking
    views_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.seller.username}"
    
    @property
    def is_in_stock(self):
        return self.quantity_available > 0
    
    @property
    def quality_label(self):
        """Get quality label based on grade"""
        grades = {
            'A': 'Premium Quality',
            'B': 'Good Quality',
            'C': 'Average Quality',
            'D': 'Below Average Quality'
        }
        return grades.get(self.quality_grade, 'Not Analyzed')

class ProductImage(models.Model):
    """Product images with YOLO analysis"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    
    # YOLO analysis results
    analyzed = models.BooleanField(default=False)
    analysis_date = models.DateTimeField(blank=True, null=True)
    detected_objects = models.JSONField(default=dict, blank=True)  # YOLO detection results
    quality_metrics = models.JSONField(default=dict, blank=True)  # Color, size, defects etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class ProductReview(models.Model):
    """Product reviews and ratings"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'buyer')
    
    def __str__(self):
        return f"Review for {self.product.name} by {self.buyer.username}"
