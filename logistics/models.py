from django.db import models
from django.conf import settings
from django.utils import timezone


class ShippingMethod(models.Model):
    """Available shipping methods"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_cost = models.DecimalField(max_digits=8, decimal_places=2)
    cost_per_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_days_min = models.IntegerField()
    estimated_days_max = models.IntegerField()
    is_active = models.BooleanField(default=True)
    regions_supported = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['base_cost']


class DeliveryZone(models.Model):
    """Delivery zones for logistics planning"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    regions = models.JSONField(default=list)  # List of supported regions/cities
    base_delivery_cost = models.DecimalField(max_digits=8, decimal_places=2)
    delivery_time_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """Warehouse/Distribution center information"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    capacity_cubic_meters = models.FloatField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class Shipment(models.Model):
    """Individual shipment tracking"""
    SHIPMENT_STATUS = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed_delivery', 'Failed Delivery'),
        ('returned', 'Returned'),
    ]
    
    tracking_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.CASCADE)
    
    # Addresses
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    
    # Status and timing
    status = models.CharField(max_length=20, choices=SHIPMENT_STATUS, default='pending')
    estimated_delivery = models.DateTimeField()
    actual_delivery = models.DateTimeField(null=True, blank=True)
    
    # Costs and measurements
    weight_kg = models.FloatField()
    dimensions = models.JSONField(default=dict, blank=True)  # length, width, height
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Carrier information
    carrier_name = models.CharField(max_length=100, blank=True)
    carrier_tracking_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            import uuid
            self.tracking_number = f"AGM{str(uuid.uuid4().hex[:8]).upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class ShipmentEvent(models.Model):
    """Tracking events for shipments"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']


class DeliveryRoute(models.Model):
    """Optimized delivery routes for drivers"""
    name = models.CharField(max_length=100)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    start_location = models.TextField()
    end_location = models.TextField()
    estimated_duration = models.IntegerField()  # in minutes
    actual_duration = models.IntegerField(null=True, blank=True)
    total_distance_km = models.FloatField()
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date']


class RouteShipment(models.Model):
    """Shipments assigned to delivery routes"""
    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE, related_name='shipments')
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)
    sequence_order = models.IntegerField()
    estimated_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['sequence_order']
        unique_together = ['route', 'shipment']
