from django.contrib import admin
from .models import (PaymentMethod, Payment, MpesaTransaction, PaymentInstallment,
                    Refund, PaymentWebhook, UserPaymentMethod, PaymentAnalytics)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'method_type', 'is_active', 'processing_fee_percentage',
                   'min_amount', 'max_amount']
    list_filter = ['method_type', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']

class MpesaTransactionInline(admin.StackedInline):
    model = MpesaTransaction
    extra = 0
    readonly_fields = ['merchant_request_id', 'checkout_request_id', 'transaction_id',
                      'transaction_date', 'mpesa_receipt_number', 'response_code',
                      'response_description', 'created_at']

class PaymentInstallmentInline(admin.TabularInline):
    model = PaymentInstallment
    extra = 0
    readonly_fields = ['paid_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'payment_method', 'amount', 'currency',
                   'status', 'initiated_at', 'completed_at']
    list_filter = ['status', 'payment_method', 'currency', 'initiated_at']
    search_fields = ['payment_id', 'user__username', 'order__order_number',
                    'gateway_transaction_id', 'mpesa_receipt_number']
    readonly_fields = ['payment_id', 'net_amount', 'gateway_response', 'metadata',
                      'initiated_at', 'completed_at', 'failed_at']
    inlines = [MpesaTransactionInline, PaymentInstallmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment_id', 'order', 'user', 'payment_method')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'processing_fee', 'net_amount', 'status')
        }),
        ('Gateway Information', {
            'fields': ('gateway_transaction_id', 'gateway_reference', 'gateway_response')
        }),
        ('M-Pesa Specific', {
            'fields': ('mpesa_receipt_number', 'mpesa_transaction_date', 'mpesa_phone_number'),
            'classes': ('collapse',)
        }),
        ('Refund Information', {
            'fields': ('refunded_amount', 'refund_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at', 'failed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['payment', 'transaction_id', 'phone_number', 'amount',
                   'transaction_date', 'response_code']
    list_filter = ['transaction_type', 'response_code', 'created_at']
    search_fields = ['transaction_id', 'phone_number', 'merchant_request_id',
                    'checkout_request_id', 'mpesa_receipt_number']
    readonly_fields = ['merchant_request_id', 'checkout_request_id', 'transaction_id',
                      'transaction_date', 'mpesa_receipt_number', 'response_code',
                      'response_description', 'callback_data', 'created_at']

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'payment', 'amount', 'reason', 'status',
                   'requested_at', 'processed_at']
    list_filter = ['reason', 'status', 'requested_at']
    search_fields = ['refund_id', 'payment__payment_id', 'payment__user__username']
    readonly_fields = ['refund_id', 'gateway_response', 'requested_at',
                      'processed_at', 'completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('refund_id', 'payment', 'amount', 'reason', 'description', 'status')
        }),
        ('Approval', {
            'fields': ('requested_by', 'approved_by')
        }),
        ('Gateway Information', {
            'fields': ('gateway_refund_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ['webhook_id', 'gateway', 'event_type', 'status',
                   'received_at', 'processed_at']
    list_filter = ['gateway', 'status', 'received_at']
    search_fields = ['webhook_id', 'event_type']
    readonly_fields = ['webhook_id', 'payload', 'headers', 'received_at',
                      'processed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('webhook_id', 'gateway', 'event_type', 'status')
        }),
        ('Data', {
            'fields': ('payload', 'headers'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('payment', 'processing_error', 'received_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(UserPaymentMethod)
class UserPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_method', 'card_last_four', 'mpesa_phone_number',
                   'is_default', 'is_active', 'created_at']
    list_filter = ['payment_method', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__username', 'card_last_four', 'mpesa_phone_number']
    readonly_fields = ['gateway_payment_method_id', 'created_at']

@admin.register(PaymentAnalytics)
class PaymentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_transactions', 'successful_transactions',
                   'total_amount', 'total_fees', 'refund_count']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Transaction Metrics', {
            'fields': ('total_transactions', 'successful_transactions', 'failed_transactions')
        }),
        ('Payment Methods', {
            'fields': ('mpesa_transactions', 'card_transactions', 'bank_transactions')
        }),
        ('Financial Metrics', {
            'fields': ('total_amount', 'total_fees', 'refund_amount', 'refund_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
