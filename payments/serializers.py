"""
Payment Serializers for AgriMart Platform
"""
from rest_framework import serializers
from .models import (Payment, PaymentMethod, MpesaTransaction, Refund, 
                    UserPaymentMethod, PaymentInstallment, PaymentAnalytics)

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'method_type', 'processing_fee_percentage', 
                 'processing_fee_fixed', 'min_amount', 'max_amount', 
                 'currencies_supported']

class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = ['merchant_request_id', 'checkout_request_id', 'transaction_type',
                 'transaction_id', 'transaction_date', 'phone_number', 'amount',
                 'mpesa_receipt_number', 'response_code', 'response_description']

class PaymentInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentInstallment
        fields = ['installment_number', 'amount', 'due_date', 'paid_date',
                 'status', 'late_fee']

class PaymentSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    mpesa_transaction = MpesaTransactionSerializer(read_only=True)
    installments = PaymentInstallmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = ['payment_id', 'order_number', 'payment_method_name', 'amount',
                 'currency', 'status', 'processing_fee', 'net_amount',
                 'gateway_transaction_id', 'mpesa_receipt_number', 
                 'mpesa_phone_number', 'refunded_amount', 'initiated_at',
                 'completed_at', 'mpesa_transaction', 'installments']

class RefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.CharField(source='payment.payment_id', read_only=True)
    order_number = serializers.CharField(source='payment.order.order_number', read_only=True)
    
    class Meta:
        model = Refund
        fields = ['refund_id', 'payment_id', 'order_number', 'amount', 'reason',
                 'description', 'status', 'requested_at', 'processed_at', 'completed_at']

class UserPaymentMethodSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    method_type = serializers.CharField(source='payment_method.method_type', read_only=True)
    
    class Meta:
        model = UserPaymentMethod
        fields = ['id', 'payment_method', 'payment_method_name', 'method_type',
                 'card_last_four', 'card_brand', 'mpesa_phone_number',
                 'is_default', 'created_at']
        read_only_fields = ['card_last_four', 'card_brand']

class PaymentAnalyticsSerializer(serializers.ModelSerializer):
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentAnalytics
        fields = ['date', 'total_transactions', 'successful_transactions',
                 'failed_transactions', 'success_rate', 'total_amount',
                 'total_fees', 'mpesa_transactions', 'card_transactions',
                 'bank_transactions', 'refund_amount', 'refund_count']
    
    def get_success_rate(self, obj):
        if obj.total_transactions > 0:
            return round((obj.successful_transactions / obj.total_transactions) * 100, 2)
        return 0.0

class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()
    phone_number = serializers.CharField(required=False, allow_blank=True)
    card_token = serializers.CharField(required=False, allow_blank=True)
    save_payment_method = serializers.BooleanField(default=False)
    
    def validate(self, data):
        payment_method_id = data.get('payment_method_id')
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id, 
                is_active=True
            )
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Invalid payment method")
        
        # Validate based on payment method type
        if payment_method.method_type == 'mpesa':
            if not data.get('phone_number'):
                raise serializers.ValidationError(
                    "Phone number is required for M-Pesa payments"
                )
        elif payment_method.method_type == 'card':
            if not data.get('card_token'):
                raise serializers.ValidationError(
                    "Card token is required for card payments"
                )
        
        data['payment_method'] = payment_method
        return data
