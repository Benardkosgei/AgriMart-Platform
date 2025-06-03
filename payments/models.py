from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from orders.models import Order

User = get_user_model()

class PaymentMethod(models.Model):
    """Available payment methods"""
    
    METHOD_TYPES = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('wallet', 'Digital Wallet'),
    )
    
    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    is_active = models.BooleanField(default=True)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    processing_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currencies_supported = models.JSONField(default=list)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"

class Payment(models.Model):
    """Payment transactions"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    )
    
    CURRENCY_CHOICES = (
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    )
    
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    gateway_reference = models.CharField(max_length=200, blank=True)
    
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    gateway_response = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # M-Pesa specific fields
    mpesa_receipt_number = models.CharField(max_length=20, blank=True)
    mpesa_transaction_date = models.DateTimeField(null=True, blank=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    
    # Refund tracking
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    refund_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway_transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} {self.currency}"
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def can_be_refunded(self):
        return self.status == 'completed' and self.refunded_amount < self.amount

class MpesaTransaction(models.Model):
    """M-Pesa specific transaction details"""
    
    TRANSACTION_TYPES = (
        ('customer_paybill_online', 'Customer PayBill Online'),
        ('customer_buygoods_online', 'Customer BuyGoods Online'),
        ('b2c_payment', 'B2C Payment'),
        ('account_balance', 'Account Balance'),
        ('transaction_status', 'Transaction Status'),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='mpesa_transaction')
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    transaction_id = models.CharField(max_length=20, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mpesa_receipt_number = models.CharField(max_length=20, blank=True)
    
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.TextField(blank=True)
    customer_message = models.TextField(blank=True)
    
    callback_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return f"M-Pesa {self.transaction_id} - {self.amount}"

class PaymentInstallment(models.Model):
    """Payment installments for buy-now-pay-later"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['installment_number']
        unique_together = ['payment', 'installment_number']
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.amount}"

class Refund(models.Model):
    """Payment refunds"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    REASON_CHOICES = (
        ('customer_request', 'Customer Request'),
        ('order_cancelled', 'Order Cancelled'),
        ('product_return', 'Product Return'),
        ('quality_issue', 'Quality Issue'),
        ('duplicate_payment', 'Duplicate Payment'),
        ('fraudulent', 'Fraudulent Transaction'),
        ('other', 'Other'),
    )
    
    refund_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    gateway_refund_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_refunds')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount}"

class PaymentWebhook(models.Model):
    """Webhook logs for payment gateways"""
    
    STATUS_CHOICES = (
        ('received', 'Received'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    )
    
    webhook_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    gateway = models.CharField(max_length=50)  # mpesa, stripe, paypal, etc.
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    processing_error = models.TextField(blank=True)
    
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['gateway', 'event_type']),
            models.Index(fields=['status', 'received_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.gateway} - {self.event_type}"

class UserPaymentMethod(models.Model):
    """Saved payment methods for users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_payment_methods')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    
    # For card payments
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_expiry_month = models.PositiveIntegerField(null=True, blank=True)
    card_expiry_year = models.PositiveIntegerField(null=True, blank=True)
    
    # For M-Pesa
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    
    # Gateway specific data
    gateway_payment_method_id = models.CharField(max_length=200, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.payment_method.method_type == 'mpesa':
            return f"M-Pesa {self.mpesa_phone_number}"
        elif self.payment_method.method_type == 'card':
            return f"{self.card_brand} ****{self.card_last_four}"
        return f"{self.payment_method.name}"

class PaymentAnalytics(models.Model):
    """Daily payment analytics"""
    
    date = models.DateField(unique=True)
    total_transactions = models.PositiveIntegerField(default=0)
    successful_transactions = models.PositiveIntegerField(default=0)
    failed_transactions = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    mpesa_transactions = models.PositiveIntegerField(default=0)
    card_transactions = models.PositiveIntegerField(default=0)
    bank_transactions = models.PositiveIntegerField(default=0)
    
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    refund_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Payment Analytics - {self.date}"
