"""
Payment Views for AgriMart Platform
"""
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
import json
import logging

from .models import (Payment, PaymentMethod, MpesaTransaction, Refund, 
                    UserPaymentMethod, PaymentWebhook)
from .services import PaymentProcessor, MpesaService, validate_mpesa_phone
from .serializers import (PaymentSerializer, PaymentMethodSerializer, 
                         MpesaTransactionSerializer, RefundSerializer,
                         UserPaymentMethodSerializer)
from orders.models import Order

logger = logging.getLogger(__name__)

class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment methods available on the platform"""
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]

class PaymentViewSet(viewsets.ModelViewSet):
    """Payment management for users"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def initiate_mpesa_payment(self, request):
        """Initiate M-Pesa STK Push payment"""
        try:
            order_id = request.data.get('order_id')
            phone_number = request.data.get('phone_number')
            
            if not order_id or not phone_number:
                return Response({
                    'error': 'Order ID and phone number are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate phone number
            if not validate_mpesa_phone(phone_number):
                return Response({
                    'error': 'Invalid M-Pesa phone number format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get order
            try:
                order = Order.objects.get(id=order_id, buyer=request.user)
            except Order.DoesNotExist:
                return Response({
                    'error': 'Order not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if order is already paid
            if order.payment_status == 'completed':
                return Response({
                    'error': 'Order is already paid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get M-Pesa payment method
            try:
                mpesa_method = PaymentMethod.objects.get(
                    method_type='mpesa', 
                    is_active=True
                )
            except PaymentMethod.DoesNotExist:
                return Response({
                    'error': 'M-Pesa payment method not available'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create payment processor and process payment
            processor = PaymentProcessor()
            payment = processor.create_payment(
                order=order,
                payment_method=mpesa_method,
                amount=order.total_amount
            )
            
            # Process M-Pesa payment
            result = processor.process_mpesa_payment(payment, phone_number)
            
            if result['success']:
                return Response({
                    'success': True,
                    'payment_id': str(result['payment_id']),
                    'checkout_request_id': result['checkout_request_id'],
                    'message': result['message']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"M-Pesa payment initiation error: {e}")
            return Response({
                'error': 'Payment initiation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def check_payment_status(self, request, pk=None):
        """Check payment status"""
        payment = self.get_object()
        
        # If it's an M-Pesa payment and still processing, query status
        if (payment.payment_method.method_type == 'mpesa' and 
            payment.status == 'processing'):
            
            try:
                mpesa_transaction = payment.mpesa_transaction
                mpesa_service = MpesaService()
                
                status_result = mpesa_service.query_transaction_status(
                    mpesa_transaction.checkout_request_id
                )
                
                # Update payment status based on query result
                if status_result.get('ResultCode') == '0':
                    payment.status = 'completed'
                    payment.save()
                elif status_result.get('ResultCode') in ['1032', '1037']:
                    # User cancelled or timeout
                    payment.status = 'cancelled'
                    payment.save()
                
            except Exception as e:
                logger.error(f"Payment status check error: {e}")
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        """Request payment refund"""
        payment = self.get_object()
        
        if not payment.can_be_refunded:
            return Response({
                'error': 'Payment cannot be refunded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', 'customer_request')
        amount = request.data.get('amount')
        
        processor = PaymentProcessor()
        result = processor.refund_payment(payment, amount, reason)
        
        if result['success']:
            return Response({
                'success': True,
                'refund_id': str(result['refund_id']),
                'amount': result['amount'],
                'status': result['status']
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)

class UserPaymentMethodViewSet(viewsets.ModelViewSet):
    """User's saved payment methods"""
    serializer_class = UserPaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserPaymentMethod.objects.filter(
            user=self.request.user, 
            is_active=True
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(View):
    """M-Pesa STK Push callback endpoint"""
    
    def post(self, request):
        try:
            # Parse callback data
            callback_data = json.loads(request.body.decode('utf-8'))
            
            # Log webhook
            webhook = PaymentWebhook.objects.create(
                gateway='mpesa',
                event_type='stk_callback',
                payload=callback_data,
                headers=dict(request.headers)
            )
            
            # Process callback
            mpesa_service = MpesaService()
            success = mpesa_service.process_callback(callback_data)
            
            if success:
                webhook.status = 'processed'
                webhook.processed_at = timezone.now()
            else:
                webhook.status = 'failed'
                webhook.processing_error = 'Callback processing failed'
            
            webhook.save()
            
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Success'
            })
            
        except Exception as e:
            logger.error(f"M-Pesa callback error: {e}")
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': 'Failed'
            }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_card_payment(request):
    """Process credit/debit card payment"""
    # This would integrate with Stripe, PayPal, or local card processors
    try:
        order_id = request.data.get('order_id')
        card_token = request.data.get('card_token')
        
        if not order_id or not card_token:
            return Response({
                'error': 'Order ID and card token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get order
        try:
            order = Order.objects.get(id=order_id, buyer=request.user)
        except Order.DoesNotExist:
            return Response({
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # For now, return success (would integrate with actual payment processor)
        return Response({
            'success': True,
            'message': 'Card payment processing not yet implemented'
        })
        
    except Exception as e:
        logger.error(f"Card payment error: {e}")
        return Response({
            'error': 'Card payment failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """Get user's payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = PaymentSerializer(page_obj, many=True)
    
    return Response({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_analytics(request):
    """Get payment analytics for sellers"""
    if request.user.user_type != 'seller':
        return Response({
            'error': 'Access denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count
    
    # Get date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get seller's payments
    seller_payments = Payment.objects.filter(
        order__items__seller=request.user,
        status='completed',
        created_at__date__range=[start_date, end_date]
    ).distinct()
    
    analytics = {
        'total_revenue': seller_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'total_transactions': seller_payments.count(),
        'average_transaction': (seller_payments.aggregate(
            avg=Sum('amount')
        )['avg'] or 0) / max(seller_payments.count(), 1),
        'payment_methods': seller_payments.values(
            'payment_method__name'
        ).annotate(
            count=Count('id'),
            total=Sum('amount')
        ),
        'daily_revenue': seller_payments.extra(
            select={'day': 'DATE(created_at)'}
        ).values('day').annotate(
            revenue=Sum('amount'),
            transactions=Count('id')
        ).order_by('day')
    }
    
    return Response(analytics)

class RefundViewSet(viewsets.ReadOnlyModelViewSet):
    """User's refund requests"""
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Refund.objects.filter(
            payment__user=self.request.user
        ).order_by('-requested_at')

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_payment_data(request):
    """Validate payment data before processing"""
    payment_method = request.data.get('payment_method')
    amount = request.data.get('amount')
    currency = request.data.get('currency', 'KES')
    
    errors = []
    
    # Validate payment method
    try:
        method = PaymentMethod.objects.get(id=payment_method, is_active=True)
        
        # Check amount limits
        if amount < method.min_amount:
            errors.append(f"Minimum amount is {method.min_amount}")
        
        if method.max_amount and amount > method.max_amount:
            errors.append(f"Maximum amount is {method.max_amount}")
        
        # Check currency support
        if currency not in method.currencies_supported:
            errors.append(f"Currency {currency} not supported")
            
    except PaymentMethod.DoesNotExist:
        errors.append("Invalid payment method")
    
    # Validate M-Pesa specific data
    if payment_method == 'mpesa':
        phone_number = request.data.get('phone_number')
        if not phone_number or not validate_mpesa_phone(phone_number):
            errors.append("Valid M-Pesa phone number required")
    
    if errors:
        return Response({
            'valid': False,
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'valid': True,
        'processing_fee': method.processing_fee_percentage,
        'estimated_fee': float(amount) * float(method.processing_fee_percentage) / 100 + float(method.processing_fee_fixed)
    })
