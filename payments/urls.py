"""
Payment URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payment-methods', views.PaymentMethodViewSet)
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'user-payment-methods', views.UserPaymentMethodViewSet, basename='userpaymentmethod')
router.register(r'refunds', views.RefundViewSet, basename='refund')

app_name = 'payments'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Payment processing
    path('api/process-card/', views.process_card_payment, name='process-card'),
    path('api/history/', views.payment_history, name='payment-history'),
    path('api/analytics/', views.payment_analytics, name='payment-analytics'),
    path('api/validate/', views.validate_payment_data, name='validate-payment'),
    
    # M-Pesa webhooks
    path('mpesa/callback/', views.MpesaCallbackView.as_view(), name='mpesa-callback'),
    
    # Include in main API URLs
    path('', include(router.urls)),
]
