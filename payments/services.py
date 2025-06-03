"""
Payment Services for AgriMart Platform
Includes M-Pesa, Stripe, and other payment gateway integrations
"""
import requests
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Payment, MpesaTransaction, PaymentMethod, PaymentWebhook
from orders.models import Order

logger = logging.getLogger(__name__)

class MpesaService:
    """M-Pesa Daraja API integration service"""
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.environment = settings.MPESA_ENVIRONMENT
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        # Set base URLs based on environment
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
    
    def get_access_token(self) -> Optional[str]:
        """Get OAuth access token from M-Pesa API"""
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create basic auth header
            credentials = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('access_token')
            
        except Exception as e:
            logger.error(f"Failed to get M-Pesa access token: {e}")
            return None
    
    def generate_password(self) -> Tuple[str, str]:
        """Generate password and timestamp for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(data_to_encode.encode()).decode()
        return password, timestamp
    
    def initiate_stk_push(self, phone_number: str, amount: Decimal, 
                         order_id: str, account_reference: str = None) -> Dict:
        """Initiate STK Push payment request"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            password, timestamp = self.generate_password()
            
            # Format phone number (ensure it starts with 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference or f"Order-{order_id}",
                'TransactionDesc': f"Payment for Order {order_id}"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if request was successful
            if data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription'),
                    'customer_message': data.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('ResponseDescription', 'STK Push failed'),
                    'response_code': data.get('ResponseCode')
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"M-Pesa STK Push request failed: {e}")
            return {'success': False, 'error': 'Network error occurred'}
        except Exception as e:
            logger.error(f"M-Pesa STK Push error: {e}")
            return {'success': False, 'error': str(e)}
    
    def query_transaction_status(self, checkout_request_id: str) -> Dict:
        """Query the status of an STK Push transaction"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            password, timestamp = self.generate_password()
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except Exception as e:
            logger.error(f"M-Pesa transaction status query error: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_callback(self, callback_data: Dict) -> bool:
        """Process M-Pesa callback response"""
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            # Find the M-Pesa transaction
            try:
                mpesa_transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                payment = mpesa_transaction.payment
                
                # Update transaction details
                mpesa_transaction.response_code = str(result_code)
                mpesa_transaction.response_description = result_desc
                mpesa_transaction.callback_data = callback_data
                
                if result_code == 0:  # Success
                    # Extract transaction details from callback metadata
                    callback_metadata = stk_callback.get('CallbackMetadata', {})
                    items = callback_metadata.get('Item', [])
                    
                    for item in items:
                        name = item.get('Name')
                        value = item.get('Value')
                        
                        if name == 'Amount':
                            mpesa_transaction.amount = Decimal(str(value))
                        elif name == 'MpesaReceiptNumber':
                            mpesa_transaction.mpesa_receipt_number = value
                            mpesa_transaction.transaction_id = value
                        elif name == 'TransactionDate':
                            # Convert timestamp to datetime
                            timestamp = int(value)
                            mpesa_transaction.transaction_date = datetime.fromtimestamp(timestamp)
                        elif name == 'PhoneNumber':
                            mpesa_transaction.phone_number = str(value)
                    
                    # Update payment status
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                    payment.mpesa_receipt_number = mpesa_transaction.mpesa_receipt_number
                    payment.mpesa_transaction_date = mpesa_transaction.transaction_date
                    payment.mpesa_phone_number = mpesa_transaction.phone_number
                    payment.gateway_transaction_id = mpesa_transaction.transaction_id
                    
                    # Update order status
                    if payment.order:
                        payment.order.payment_status = 'completed'
                        payment.order.status = 'confirmed'
                        payment.order.confirmed_at = timezone.now()
                        payment.order.save()
                else:
                    # Payment failed
                    payment.status = 'failed'
                    payment.failed_at = timezone.now()
                    payment.save()
                
                mpesa_transaction.save()
                payment.save()
                
                logger.info(f"M-Pesa callback processed successfully for payment {payment.payment_id}")
                return True
                
            except MpesaTransaction.DoesNotExist:
                logger.error(f"M-Pesa transaction not found for checkout request: {checkout_request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}")
            return False

class PaymentProcessor:
    """Main payment processing service"""
    
    def __init__(self):
        self.mpesa_service = MpesaService()
    
    def create_payment(self, order: Order, payment_method: PaymentMethod, 
                      amount: Decimal, **kwargs) -> Payment:
        """Create a new payment record"""
        
        # Calculate processing fee
        processing_fee = self._calculate_processing_fee(amount, payment_method)
        net_amount = amount - processing_fee
        
        payment = Payment.objects.create(
            order=order,
            user=order.buyer,
            payment_method=payment_method,
            amount=amount,
            processing_fee=processing_fee,
            net_amount=net_amount,
            currency=kwargs.get('currency', 'KES'),
            metadata=kwargs.get('metadata', {})
        )
        
        return payment
    
    def process_mpesa_payment(self, payment: Payment, phone_number: str) -> Dict:
        """Process M-Pesa payment using STK Push"""
        try:
            # Initiate STK Push
            result = self.mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount=payment.amount,
                order_id=str(payment.order.order_number),
                account_reference=f"AgriMart-{payment.order.id}"
            )
            
            if result['success']:
                # Create M-Pesa transaction record
                mpesa_transaction = MpesaTransaction.objects.create(
                    payment=payment,
                    merchant_request_id=result['merchant_request_id'],
                    checkout_request_id=result['checkout_request_id'],
                    transaction_type='customer_paybill_online',
                    phone_number=phone_number,
                    amount=payment.amount,
                    response_code=result['response_code'],
                    response_description=result['response_description'],
                    customer_message=result['customer_message']
                )
                
                # Update payment status
                payment.status = 'processing'
                payment.gateway_reference = result['checkout_request_id']
                payment.save()
                
                return {
                    'success': True,
                    'payment_id': payment.payment_id,
                    'checkout_request_id': result['checkout_request_id'],
                    'message': result['customer_message']
                }
            else:
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.save()
                
                return {
                    'success': False,
                    'error': result['error']
                }
                
        except Exception as e:
            logger.error(f"M-Pesa payment processing error: {e}")
            payment.status = 'failed'
            payment.failed_at = timezone.now()
            payment.save()
            
            return {
                'success': False,
                'error': 'Payment processing failed'
            }
    
    def _calculate_processing_fee(self, amount: Decimal, 
                                payment_method: PaymentMethod) -> Decimal:
        """Calculate processing fee for a payment"""
        percentage_fee = amount * (payment_method.processing_fee_percentage / 100)
        total_fee = percentage_fee + payment_method.processing_fee_fixed
        return round(total_fee, 2)
    
    def refund_payment(self, payment: Payment, amount: Decimal = None, 
                      reason: str = 'customer_request') -> Dict:
        """Process payment refund"""
        try:
            refund_amount = amount or payment.amount
            
            if refund_amount > (payment.amount - payment.refunded_amount):
                return {
                    'success': False,
                    'error': 'Refund amount exceeds available amount'
                }
            
            # For M-Pesa, we would typically use B2C API
            # For now, we'll mark it as pending manual processing
            from .models import Refund
            
            refund = Refund.objects.create(
                payment=payment,
                amount=refund_amount,
                reason=reason,
                requested_by=payment.user,
                status='pending'
            )
            
            # Update payment refunded amount
            payment.refunded_amount += refund_amount
            if payment.refunded_amount >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'
            payment.save()
            
            return {
                'success': True,
                'refund_id': refund.refund_id,
                'amount': refund_amount,
                'status': refund.status
            }
            
        except Exception as e:
            logger.error(f"Refund processing error: {e}")
            return {
                'success': False,
                'error': 'Refund processing failed'
            }

class PaymentAnalyticsService:
    """Service for payment analytics and reporting"""
    
    @staticmethod
    def update_daily_analytics(date=None):
        """Update daily payment analytics"""
        from .models import PaymentAnalytics
        
        if date is None:
            date = timezone.now().date()
        
        # Get payments for the date
        payments = Payment.objects.filter(created_at__date=date)
        
        # Calculate metrics
        total_transactions = payments.count()
        successful_transactions = payments.filter(status='completed').count()
        failed_transactions = payments.filter(status='failed').count()
        
        total_amount = sum(p.amount for p in payments.filter(status='completed'))
        total_fees = sum(p.processing_fee for p in payments.filter(status='completed'))
        
        mpesa_transactions = payments.filter(
            payment_method__method_type='mpesa'
        ).count()
        card_transactions = payments.filter(
            payment_method__method_type='card'
        ).count()
        bank_transactions = payments.filter(
            payment_method__method_type='bank_transfer'
        ).count()
        
        # Get refund data
        from .models import Refund
        refunds = Refund.objects.filter(requested_at__date=date, status='completed')
        refund_amount = sum(r.amount for r in refunds)
        refund_count = refunds.count()
        
        # Update or create analytics record
        analytics, created = PaymentAnalytics.objects.update_or_create(
            date=date,
            defaults={
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'failed_transactions': failed_transactions,
                'total_amount': total_amount,
                'total_fees': total_fees,
                'mpesa_transactions': mpesa_transactions,
                'card_transactions': card_transactions,
                'bank_transactions': bank_transactions,
                'refund_amount': refund_amount,
                'refund_count': refund_count,
            }
        )
        
        return analytics

# Utility functions
def format_phone_number(phone_number: str) -> str:
    """Format phone number for M-Pesa"""
    # Remove all non-numeric characters
    phone = ''.join(filter(str.isdigit, phone_number))
    
    # Format for Kenya (254)
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('254'):
        pass  # Already formatted
    elif phone.startswith('7') or phone.startswith('1'):
        phone = '254' + phone
    
    return phone

def validate_mpesa_phone(phone_number: str) -> bool:
    """Validate M-Pesa phone number format"""
    formatted = format_phone_number(phone_number)
    
    # Kenya mobile numbers start with 254 followed by 7 or 1
    if len(formatted) != 12:
        return False
    
    if not formatted.startswith('2547') and not formatted.startswith('2541'):
        return False
    
    return True
