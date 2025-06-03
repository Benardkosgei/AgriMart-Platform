from django.db import models
from django.conf import settings
from django.utils import timezone


class APIKey(models.Model):
    """API Keys for third-party integrations"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    rate_limit_per_hour = models.IntegerField(default=1000)
    allowed_endpoints = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.key:
            import secrets
            self.key = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."


class APIRequest(models.Model):
    """Track API requests for analytics and rate limiting"""
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    response_status = models.IntegerField()
    response_time_ms = models.IntegerField()
    request_size_bytes = models.IntegerField(default=0)
    response_size_bytes = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]


class WebhookEndpoint(models.Model):
    """Webhook endpoints for real-time notifications"""
    EVENT_TYPES = [
        ('order.created', 'Order Created'),
        ('order.updated', 'Order Updated'),
        ('payment.completed', 'Payment Completed'),
        ('quality.analyzed', 'Quality Analysis Completed'),
        ('shipment.updated', 'Shipment Status Updated'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField()
    event_types = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)
    last_success = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.secret_key:
            import secrets
            self.secret_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ['user', 'url']


class WebhookDelivery(models.Model):
    """Track webhook delivery attempts"""
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    http_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    delivery_attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    is_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    next_retry = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
