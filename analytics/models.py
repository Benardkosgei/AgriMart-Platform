from django.db import models
from django.conf import settings
from django.utils import timezone


class AnalyticsEvent(models.Model):
    """Track various analytics events across the platform"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('quality_analysis', 'Quality Analysis'),
        ('purchase', 'Purchase'),
        ('cart_add', 'Add to Cart'),
        ('search', 'Search'),
        ('login', 'Login'),
        ('registration', 'Registration'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]


class SalesAnalytics(models.Model):
    """Daily sales analytics aggregation"""
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    unique_customers = models.IntegerField(default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    top_categories = models.JSONField(default=list, blank=True)
    quality_distribution = models.JSONField(default=dict, blank=True)  # Grade A, B, C, D counts
    
    class Meta:
        ordering = ['-date']


class QualityAnalytics(models.Model):
    """Analytics for AI quality assessment performance"""
    date = models.DateField()
    total_analyses = models.IntegerField(default=0)
    avg_processing_time = models.FloatField(default=0)  # in seconds
    grade_distribution = models.JSONField(default=dict, blank=True)
    accuracy_feedback = models.FloatField(default=0)  # User feedback on accuracy
    error_rate = models.FloatField(default=0)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']


class UserBehaviorAnalytics(models.Model):
    """Track user behavior patterns"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    page_views = models.IntegerField(default=0)
    session_duration = models.IntegerField(default=0)  # in seconds
    products_viewed = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    cart_additions = models.IntegerField(default=0)
    purchases_made = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
