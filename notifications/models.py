from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

User = get_user_model()

class NotificationTemplate(models.Model):
    """Templates for different notification types"""
    
    NOTIFICATION_TYPES = (
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('payment_successful', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('payment_refunded', 'Payment Refunded'),
        ('product_low_stock', 'Product Low Stock'),
        ('product_out_of_stock', 'Product Out of Stock'),
        ('product_quality_analyzed', 'Product Quality Analyzed'),
        ('review_received', 'Review Received'),
        ('promotion_available', 'Promotion Available'),
        ('welcome', 'Welcome Message'),
        ('password_reset', 'Password Reset'),
        ('account_verification', 'Account Verification'),
        ('vendor_payout', 'Vendor Payout'),
        ('support_ticket', 'Support Ticket'),
    )
    
    CHANNEL_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('system', 'System Notification'),
    )
    
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, unique=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    
    # Email specific
    email_subject = models.CharField(max_length=200, blank=True)
    email_template = models.TextField(blank=True)
    email_html_template = models.TextField(blank=True)
    
    # SMS specific
    sms_template = models.CharField(max_length=160, blank=True)
    
    # Push notification specific
    push_title = models.CharField(max_length=100, blank=True)
    push_body = models.CharField(max_length=200, blank=True)
    
    # In-app notification specific
    in_app_title = models.CharField(max_length=100, blank=True)
    in_app_message = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['notification_type', 'channel']
    
    def __str__(self):
        return f"{self.name} ({self.channel})"

class Notification(models.Model):
    """Individual notification instances"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    notification_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Generic relation to any model (order, payment, product, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Additional context data
    
    channel = models.CharField(max_length=20, choices=NotificationTemplate.CHANNEL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Delivery details
    email_address = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    device_token = models.CharField(max_length=500, blank=True)
    
    # URLs and actions
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['channel', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.channel})"
    
    @property
    def is_read(self):
        return self.status == 'read'

class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    
    # Notification type preferences
    order_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    product_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    system_notifications = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Frequency preferences
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='immediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Preferences - {self.user.username}"

class EmailCampaign(models.Model):
    """Email marketing campaigns"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    )
    
    campaign_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    
    # Content
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Targeting
    target_users = models.ManyToManyField(User, blank=True)
    target_user_types = models.JSONField(default=list, blank=True)  # ['buyer', 'seller']
    target_segments = models.JSONField(default=list, blank=True)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    unsubscribed_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"

class EmailCampaignRecipient(models.Model):
    """Individual email campaign recipients"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('failed', 'Failed'),
    )
    
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_address = models.EmailField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    tracking_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['campaign', 'user']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['email_address', 'status']),
        ]
    
    def __str__(self):
        return f"{self.campaign.name} - {self.email_address}"

class NotificationLog(models.Model):
    """Log of all notification activities"""
    
    ACTION_CHOICES = (
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('failed', 'Failed'),
        ('retried', 'Retried'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['notification', 'action']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.notification.notification_id} - {self.action}"

class DeviceToken(models.Model):
    """Push notification device tokens"""
    
    DEVICE_TYPES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=500, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_id = models.CharField(max_length=100, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'token']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"

class NotificationStats(models.Model):
    """Daily notification statistics"""
    
    date = models.DateField(unique=True)
    
    # Email stats
    emails_sent = models.PositiveIntegerField(default=0)
    emails_delivered = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    emails_bounced = models.PositiveIntegerField(default=0)
    
    # SMS stats
    sms_sent = models.PositiveIntegerField(default=0)
    sms_delivered = models.PositiveIntegerField(default=0)
    sms_failed = models.PositiveIntegerField(default=0)
    
    # Push notification stats
    push_sent = models.PositiveIntegerField(default=0)
    push_delivered = models.PositiveIntegerField(default=0)
    push_clicked = models.PositiveIntegerField(default=0)
    
    # In-app notification stats
    in_app_created = models.PositiveIntegerField(default=0)
    in_app_read = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Notification Stats - {self.date}"
