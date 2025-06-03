"""
Notification Services for AgriMart Platform
Handles email, SMS, push notifications, and in-app notifications
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import (Notification, NotificationTemplate, NotificationPreference,
                    EmailCampaign, EmailCampaignRecipient, NotificationLog,
                    DeviceToken, NotificationStats)

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationService:
    """Main notification service for handling all notification types"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
        self.in_app_service = InAppNotificationService()
    
    def send_notification(self, notification_type: str, user: User, 
                         context: Dict = None, related_object: Any = None,
                         channels: List[str] = None) -> Dict:
        """Send notification through specified channels"""
        try:
            # Get user preferences
            preferences = self._get_user_preferences(user)
            
            # Get notification templates for the type
            templates = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            )
            
            if not templates.exists():
                logger.warning(f"No templates found for notification type: {notification_type}")
                return {'success': False, 'error': 'No templates found'}
            
            # Default context
            default_context = {
                'user': user,
                'user_name': user.get_full_name() or user.username,
                'site_name': 'AgriMart',
                'site_url': getattr(settings, 'SITE_URL', 'https://agrimart.com'),
            }
            
            if context:
                default_context.update(context)
            
            results = {}
            
            # Process each template/channel
            for template in templates:
                if channels and template.channel not in channels:
                    continue
                
                # Check user preferences
                if not self._should_send_notification(template.channel, preferences, notification_type):
                    continue
                
                # Create notification record
                notification = self._create_notification(
                    template, user, default_context, related_object
                )
                
                # Send via appropriate service
                if template.channel == 'email':
                    result = self.email_service.send_email_notification(notification, default_context)
                elif template.channel == 'sms':
                    result = self.sms_service.send_sms_notification(notification, default_context)
                elif template.channel == 'push':
                    result = self.push_service.send_push_notification(notification, default_context)
                elif template.channel == 'in_app':
                    result = self.in_app_service.create_in_app_notification(notification, default_context)
                else:
                    result = {'success': False, 'error': 'Unknown channel'}
                
                results[template.channel] = result
                
                # Log the action
                self._log_notification_action(notification, 'sent' if result['success'] else 'failed')
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"Notification sending error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_user_preferences(self, user: User) -> NotificationPreference:
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': True,
                'sms_enabled': True,
                'push_enabled': True,
                'in_app_enabled': True,
            }
        )
        return preferences
    
    def _should_send_notification(self, channel: str, preferences: NotificationPreference,
                                notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences"""
        # Check channel preferences
        if channel == 'email' and not preferences.email_enabled:
            return False
        elif channel == 'sms' and not preferences.sms_enabled:
            return False
        elif channel == 'push' and not preferences.push_enabled:
            return False
        elif channel == 'in_app' and not preferences.in_app_enabled:
            return False
        
        # Check notification type preferences
        if notification_type.startswith('order_') and not preferences.order_notifications:
            return False
        elif notification_type.startswith('payment_') and not preferences.payment_notifications:
            return False
        elif notification_type.startswith('product_') and not preferences.product_notifications:
            return False
        elif notification_type.startswith('promotion_') and not preferences.marketing_notifications:
            return False
        
        # Check quiet hours (for push and SMS)
        if channel in ['push', 'sms'] and preferences.quiet_hours_start and preferences.quiet_hours_end:
            now = timezone.now().time()
            if preferences.quiet_hours_start <= now <= preferences.quiet_hours_end:
                return False
        
        return True
    
    def _create_notification(self, template: NotificationTemplate, user: User,
                           context: Dict, related_object: Any = None) -> Notification:
        """Create notification record"""
        # Get content type and object id for related object
        content_type = None
        object_id = None
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = related_object.id
        
        # Render title and message
        title = self._render_template_string(
            template.in_app_title or template.push_title or template.email_subject,
            context
        )
        message = self._render_template_string(
            template.in_app_message or template.push_body or template.email_template,
            context
        )
        
        notification = Notification.objects.create(
            user=user,
            template=template,
            content_type=content_type,
            object_id=object_id,
            title=title,
            message=message,
            channel=template.channel,
            data=context,
            email_address=user.email if template.channel == 'email' else '',
            phone_number=getattr(user, 'phone_number', '') if template.channel == 'sms' else '',
        )
        
        return notification
    
    def _render_template_string(self, template_string: str, context: Dict) -> str:
        """Render template string with context"""
        if not template_string:
            return ''
        
        try:
            from django.template import Template, Context
            template = Template(template_string)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string
    
    def _log_notification_action(self, notification: Notification, action: str,
                               details: str = '', metadata: Dict = None):
        """Log notification action"""
        NotificationLog.objects.create(
            notification=notification,
            action=action,
            details=details,
            metadata=metadata or {}
        )

class EmailService:
    """Email notification service"""
    
    def send_email_notification(self, notification: Notification, context: Dict) -> Dict:
        """Send email notification"""
        try:
            template = notification.template
            
            # Render email content
            subject = self._render_template_string(template.email_subject, context)
            text_content = self._render_template_string(template.email_template, context)
            html_content = self._render_template_string(template.email_html_template, context)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.email_address]
            )
            
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            notification.status = 'failed'
            notification.failed_reason = str(e)
            notification.save()
            
            return {'success': False, 'error': str(e)}
    
    def _render_template_string(self, template_string: str, context: Dict) -> str:
        """Render template string with context"""
        if not template_string:
            return ''
        
        try:
            from django.template import Template, Context
            template = Template(template_string)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string

class SMSService:
    """SMS notification service using Twilio"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning("Twilio package not installed")
                self.client = None
        else:
            self.client = None
    
    def send_sms_notification(self, notification: Notification, context: Dict) -> Dict:
        """Send SMS notification"""
        try:
            if not self.client:
                return {'success': False, 'error': 'SMS service not configured'}
            
            template = notification.template
            
            # Render SMS content
            message = self._render_template_string(template.sms_template, context)
            
            if not message:
                return {'success': False, 'error': 'No SMS template content'}
            
            # Send SMS
            sms = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=notification.phone_number
            )
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.gateway_transaction_id = sms.sid
            notification.save()
            
            return {'success': True, 'message': 'SMS sent successfully', 'sid': sms.sid}
            
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            notification.status = 'failed'
            notification.failed_reason = str(e)
            notification.save()
            
            return {'success': False, 'error': str(e)}
    
    def _render_template_string(self, template_string: str, context: Dict) -> str:
        """Render template string with context"""
        if not template_string:
            return ''
        
        try:
            from django.template import Template, Context
            template = Template(template_string)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string

class PushNotificationService:
    """Push notification service"""
    
    def send_push_notification(self, notification: Notification, context: Dict) -> Dict:
        """Send push notification to user's devices"""
        try:
            # Get user's active device tokens
            device_tokens = DeviceToken.objects.filter(
                user=notification.user,
                is_active=True
            )
            
            if not device_tokens.exists():
                return {'success': False, 'error': 'No active devices found'}
            
            template = notification.template
            
            # Render push notification content
            title = self._render_template_string(template.push_title, context)
            body = self._render_template_string(template.push_body, context)
            
            results = []
            
            for device_token in device_tokens:
                result = self._send_to_device(device_token, title, body, notification.data)
                results.append(result)
            
            # Update notification status
            if any(r['success'] for r in results):
                notification.status = 'sent'
                notification.sent_at = timezone.now()
            else:
                notification.status = 'failed'
                notification.failed_reason = 'All devices failed'
            
            notification.save()
            
            return {
                'success': any(r['success'] for r in results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            notification.status = 'failed'
            notification.failed_reason = str(e)
            notification.save()
            
            return {'success': False, 'error': str(e)}
    
    def _send_to_device(self, device_token: DeviceToken, title: str, 
                       body: str, data: Dict) -> Dict:
        """Send push notification to specific device"""
        try:
            # This would integrate with FCM, APNS, or other push services
            # For now, we'll simulate the process
            
            if device_token.device_type == 'android':
                return self._send_fcm_notification(device_token.token, title, body, data)
            elif device_token.device_type == 'ios':
                return self._send_apns_notification(device_token.token, title, body, data)
            else:
                return {'success': False, 'error': 'Unsupported device type'}
                
        except Exception as e:
            logger.error(f"Device push notification error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_fcm_notification(self, token: str, title: str, body: str, data: Dict) -> Dict:
        """Send FCM notification (Android)"""
        # Implement FCM integration here
        logger.info(f"FCM notification sent: {title}")
        return {'success': True, 'service': 'fcm'}
    
    def _send_apns_notification(self, token: str, title: str, body: str, data: Dict) -> Dict:
        """Send APNS notification (iOS)"""
        # Implement APNS integration here
        logger.info(f"APNS notification sent: {title}")
        return {'success': True, 'service': 'apns'}
    
    def _render_template_string(self, template_string: str, context: Dict) -> str:
        """Render template string with context"""
        if not template_string:
            return ''
        
        try:
            from django.template import Template, Context
            template = Template(template_string)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string

class InAppNotificationService:
    """In-app notification service"""
    
    def create_in_app_notification(self, notification: Notification, context: Dict) -> Dict:
        """Create in-app notification"""
        try:
            # In-app notifications are just stored in database
            # and delivered via WebSocket or API polling
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            # Send real-time notification via WebSocket
            self._send_websocket_notification(notification)
            
            return {'success': True, 'message': 'In-app notification created'}
            
        except Exception as e:
            logger.error(f"In-app notification error: {e}")
            notification.status = 'failed'
            notification.failed_reason = str(e)
            notification.save()
            
            return {'success': False, 'error': str(e)}
    
    def _send_websocket_notification(self, notification: Notification):
        """Send notification via WebSocket"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            # Send to user's personal channel
            async_to_sync(channel_layer.group_send)(
                f"user_{notification.user.id}",
                {
                    "type": "notification_message",
                    "message": {
                        "id": str(notification.notification_id),
                        "title": notification.title,
                        "message": notification.message,
                        "channel": notification.channel,
                        "created_at": notification.created_at.isoformat(),
                        "action_url": notification.action_url,
                        "action_text": notification.action_text,
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"WebSocket notification error: {e}")

class EmailCampaignService:
    """Email marketing campaign service"""
    
    def create_campaign(self, name: str, subject: str, html_content: str,
                       target_criteria: Dict, scheduled_at: datetime = None) -> EmailCampaign:
        """Create email campaign"""
        campaign = EmailCampaign.objects.create(
            name=name,
            subject=subject,
            html_content=html_content,
            scheduled_at=scheduled_at,
            status='scheduled' if scheduled_at else 'draft'
        )
        
        # Add recipients based on criteria
        recipients = self._get_target_recipients(target_criteria)
        campaign.total_recipients = len(recipients)
        campaign.save()
        
        # Create recipient records
        for user in recipients:
            EmailCampaignRecipient.objects.create(
                campaign=campaign,
                user=user,
                email_address=user.email
            )
        
        return campaign
    
    def send_campaign(self, campaign: EmailCampaign) -> Dict:
        """Send email campaign"""
        try:
            recipients = campaign.recipients.filter(status='pending')
            
            if not recipients.exists():
                return {'success': False, 'error': 'No pending recipients'}
            
            campaign.status = 'sending'
            campaign.save()
            
            sent_count = 0
            failed_count = 0
            
            for recipient in recipients:
                try:
                    # Send email
                    msg = EmailMultiAlternatives(
                        subject=campaign.subject,
                        body=campaign.text_content or '',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[recipient.email_address]
                    )
                    
                    if campaign.html_content:
                        msg.attach_alternative(campaign.html_content, "text/html")
                    
                    msg.send()
                    
                    # Update recipient status
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Campaign email sending error: {e}")
                    recipient.status = 'failed'
                    recipient.save()
                    failed_count += 1
            
            # Update campaign status
            campaign.sent_count = sent_count
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.save()
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Campaign sending error: {e}")
            campaign.status = 'cancelled'
            campaign.save()
            
            return {'success': False, 'error': str(e)}
    
    def _get_target_recipients(self, criteria: Dict) -> List[User]:
        """Get target recipients based on criteria"""
        queryset = User.objects.filter(is_active=True)
        
        # Filter by user type
        if 'user_types' in criteria:
            queryset = queryset.filter(user_type__in=criteria['user_types'])
        
        # Filter by registration date
        if 'min_registration_date' in criteria:
            queryset = queryset.filter(date_joined__gte=criteria['min_registration_date'])
        
        # Filter by activity
        if 'has_orders' in criteria and criteria['has_orders']:
            queryset = queryset.filter(orders__isnull=False).distinct()
        
        # Filter by preferences (only users who allow marketing)
        queryset = queryset.filter(
            notification_preferences__marketing_notifications=True
        )
        
        return list(queryset)

# Utility functions
def send_order_notification(order, notification_type: str):
    """Send order-related notifications"""
    service = NotificationService()
    
    context = {
        'order': order,
        'order_number': order.order_number,
        'total_amount': order.total_amount,
        'items_count': order.total_items,
    }
    
    # Send to buyer
    service.send_notification(
        notification_type=notification_type,
        user=order.buyer,
        context=context,
        related_object=order
    )
    
    # Send to sellers (for order placed notification)
    if notification_type == 'order_placed':
        for item in order.items.all():
            seller_context = context.copy()
            seller_context.update({
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item.total_price,
            })
            
            service.send_notification(
                notification_type='order_received',  # Different notification for sellers
                user=item.seller,
                context=seller_context,
                related_object=order
            )

def send_payment_notification(payment, notification_type: str):
    """Send payment-related notifications"""
    service = NotificationService()
    
    context = {
        'payment': payment,
        'order': payment.order,
        'amount': payment.amount,
        'payment_method': payment.payment_method.name,
    }
    
    service.send_notification(
        notification_type=notification_type,
        user=payment.user,
        context=context,
        related_object=payment
    )

def update_notification_stats(date=None):
    """Update daily notification statistics"""
    if date is None:
        date = timezone.now().date()
    
    # Get notifications for the date
    notifications = Notification.objects.filter(created_at__date=date)
    
    # Calculate stats
    stats = {
        'emails_sent': notifications.filter(channel='email', status='sent').count(),
        'emails_delivered': notifications.filter(channel='email', status='delivered').count(),
        'sms_sent': notifications.filter(channel='sms', status='sent').count(),
        'sms_delivered': notifications.filter(channel='sms', status='delivered').count(),
        'sms_failed': notifications.filter(channel='sms', status='failed').count(),
        'push_sent': notifications.filter(channel='push', status='sent').count(),
        'push_delivered': notifications.filter(channel='push', status='delivered').count(),
        'in_app_created': notifications.filter(channel='in_app').count(),
        'in_app_read': notifications.filter(channel='in_app', status='read').count(),
    }
    
    # Update or create stats record
    notification_stats, created = NotificationStats.objects.update_or_create(
        date=date,
        defaults=stats
    )
    
    return notification_stats
