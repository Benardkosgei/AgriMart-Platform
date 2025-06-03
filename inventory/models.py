from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product, Category
from decimal import Decimal
import uuid

User = get_user_model()

class Supplier(models.Model):
    """Suppliers for inventory management"""
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
        ('pending_approval', 'Pending Approval'),
    )
    
    supplier_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Business details
    business_license = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    
    # Rating and performance
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_orders = models.PositiveIntegerField(default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Status and terms
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    payment_terms = models.CharField(max_length=100, default='Net 30')
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Relationships
    categories = models.ManyToManyField(Category, related_name='suppliers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Warehouse(models.Model):
    """Warehouse/storage locations"""
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Capacity
    total_capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="In cubic meters")
    temperature_controlled = models.BooleanField(default=False)
    humidity_controlled = models.BooleanField(default=False)
    
    # Contact
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class InventoryItem(models.Model):
    """Inventory tracking for products"""
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_items')
    
    # Stock levels
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reserved_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Reserved for orders
    available_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Current - Reserved
    
    # Reorder management
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    
    # Cost tracking
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    last_reorder_date = models.DateTimeField(null=True, blank=True)
    
    # Settings
    auto_reorder_enabled = models.BooleanField(default=True)
    track_expiry = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'warehouse']
        indexes = [
            models.Index(fields=['current_stock', 'reorder_point']),
            models.Index(fields=['warehouse', 'current_stock']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}"
    
    @property
    def is_low_stock(self):
        return self.available_stock <= self.reorder_point
    
    @property
    def is_out_of_stock(self):
        return self.available_stock <= 0
    
    def update_available_stock(self):
        """Update available stock calculation"""
        self.available_stock = self.current_stock - self.reserved_stock
        self.total_value = self.current_stock * self.unit_cost
        self.save()

class StockMovement(models.Model):
    """Track all stock movements"""
    
    MOVEMENT_TYPES = (
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
        ('waste', 'Waste/Spoilage'),
        ('reservation', 'Reservation'),
        ('release', 'Release Reservation'),
    )
    
    movement_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Before and after stock levels
    stock_before = models.DecimalField(max_digits=10, decimal_places=2)
    stock_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reference information
    reference_type = models.CharField(max_length=50, blank=True)  # order, purchase_order, etc.
    reference_id = models.CharField(max_length=100, blank=True)
    
    # Additional details
    notes = models.TextField(blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_item', 'movement_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.movement_type} - {self.quantity} - {self.inventory_item.product.name}"

class PurchaseOrder(models.Model):
    """Purchase orders to suppliers"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed by Supplier'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchase_orders')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_pos')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"
    
    def calculate_totals(self):
        """Calculate purchase order totals"""
        self.subtotal = sum(item.total_amount for item in self.items.all())
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_amount
        self.save()

class PurchaseOrderItem(models.Model):
    """Items in a purchase order"""
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Quality information
    quality_grade_expected = models.CharField(max_length=1, blank=True)
    quality_grade_received = models.CharField(max_length=1, blank=True)
    
    # Delivery tracking
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['purchase_order', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_ordered}"
    
    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered
    
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.quantity_ordered * self.unit_cost
        super().save(*args, **kwargs)

class StockAlert(models.Model):
    """Alerts for inventory management"""
    
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('reorder_needed', 'Reorder Needed'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    alert_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='alerts')
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    
    # Alert details
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Tracking
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'alert_type']),
            models.Index(fields=['inventory_item', 'status']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.inventory_item.product.name}"

class StockBatch(models.Model):
    """Track product batches for expiry and quality management"""
    
    batch_number = models.CharField(max_length=50)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='batches')
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    production_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(auto_now_add=True)
    
    # Quality information
    quality_grade = models.CharField(max_length=1, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    
    # Supplier information
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['batch_number', 'inventory_item']
        ordering = ['expiry_date']
        indexes = [
            models.Index(fields=['expiry_date', 'is_active']),
            models.Index(fields=['inventory_item', 'is_active']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_number} - {self.inventory_item.product.name}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date and self.expiry_date < timezone.now().date()
    
    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days

class InventoryAnalytics(models.Model):
    """Daily inventory analytics"""
    
    date = models.DateField(unique=True)
    
    # Stock metrics
    total_products = models.PositiveIntegerField(default=0)
    total_stock_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    low_stock_items = models.PositiveIntegerField(default=0)
    out_of_stock_items = models.PositiveIntegerField(default=0)
    overstock_items = models.PositiveIntegerField(default=0)
    
    # Movement metrics
    total_movements = models.PositiveIntegerField(default=0)
    purchases_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sales_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    waste_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Purchase order metrics
    pending_pos = models.PositiveIntegerField(default=0)
    pending_po_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Alert metrics
    active_alerts = models.PositiveIntegerField(default=0)
    critical_alerts = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Inventory Analytics - {self.date}"
