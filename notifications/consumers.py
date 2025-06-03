"""
WebSocket consumers for real-time notifications
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            # Reject connection for anonymous users
            await self.close()
            return
        
        # Join user-specific group
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications'
        }))
        
        # Send unread notifications count
        unread_count = await self.get_unread_notifications_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_as_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_as_read(notification_id)
                    
            elif message_type == 'get_notifications':
                notifications = await self.get_recent_notifications()
                await self.send(text_data=json.dumps({
                    'type': 'notifications_list',
                    'notifications': notifications
                }))
                
            elif message_type == 'mark_all_read':
                await self.mark_all_notifications_as_read()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def notification_message(self, event):
        """Handle notification message from group"""
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': message
        }))
    
    @database_sync_to_async
    def get_unread_notifications_count(self):
        """Get count of unread notifications for user"""
        from .models import Notification
        return Notification.objects.filter(
            user=self.user,
            channel='in_app',
            status__in=['sent', 'delivered']
        ).count()
    
    @database_sync_to_async
    def get_recent_notifications(self):
        """Get recent notifications for user"""
        from .models import Notification
        notifications = Notification.objects.filter(
            user=self.user,
            channel='in_app'
        ).order_by('-created_at')[:20]
        
        return [
            {
                'id': str(notification.notification_id),
                'title': notification.title,
                'message': notification.message,
                'status': notification.status,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
                'action_text': notification.action_text,
            }
            for notification in notifications
        ]
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark specific notification as read"""
        from .models import Notification
        from django.utils import timezone
        
        try:
            notification = Notification.objects.get(
                notification_id=notification_id,
                user=self.user,
                channel='in_app'
            )
            notification.status = 'read'
            notification.read_at = timezone.now()
            notification.save()
            
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_as_read(self):
        """Mark all unread notifications as read"""
        from .models import Notification
        from django.utils import timezone
        
        notifications = Notification.objects.filter(
            user=self.user,
            channel='in_app',
            status__in=['sent', 'delivered']
        )
        
        notifications.update(
            status='read',
            read_at=timezone.now()
        )
        
        return notifications.count()
