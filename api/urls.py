"""
URL patterns for AgriMart API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Main router
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'cart-items', views.CartItemViewSet, basename='cartitem')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')
router.register(r'seller-profiles', views.SellerProfileViewSet, basename='sellerprofile')
router.register(r'buyer-profiles', views.BuyerProfileViewSet, basename='buyerprofile')
router.register(r'quality-reports', views.QualityReportViewSet, basename='qualityreport')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    
    # Image upload and quality analysis
    path('upload-image/', views.upload_product_image, name='upload-image'),
    path('analyze-image/<int:image_id>/', views.analyze_existing_image, name='analyze-image'),
    
    # Search
    path('search/', views.search_products, name='search-products'),
    
    # Dashboard
    path('dashboard/seller/', views.seller_dashboard, name='seller-dashboard'),
    path('dashboard/buyer/', views.buyer_dashboard, name='buyer-dashboard'),
    
    # Product reviews (without nested router)
    path('products/<int:product_pk>/reviews/', views.ProductReviewViewSet.as_view({'get': 'list', 'post': 'create'}), name='product-reviews'),
    
    # Include router URLs
    path('', include(router.urls)),
]
