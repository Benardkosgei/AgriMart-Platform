from django.db import models
from django.conf import settings
from django.utils import timezone


class SupportTicket(models.Model):
    """Customer support ticket system"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending_customer', 'Pending Customer Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('quality', 'Quality Analysis'),
        ('payment', 'Payment Issues'),
        ('order', 'Order Problems'),
        ('account', 'Account Issues'),
        ('technical', 'Technical Support'),
        ('general', 'General Inquiry'),
    ]
    
    ticket_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Generate unique ticket ID
            import uuid
            self.ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['user', 'created_at']),
        ]


class SupportMessage(models.Model):
    """Messages within support tickets"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal staff notes
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    helpful_votes = models.IntegerField(default=0)
    not_helpful_votes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', '-helpful_votes']


class KnowledgeBaseArticle(models.Model):
    """Knowledge base articles for self-service support"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50)
    tags = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    helpful_votes = models.IntegerField(default=0)
    not_helpful_votes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
