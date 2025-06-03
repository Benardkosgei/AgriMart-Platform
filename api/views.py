"""
API Views for AgriMart Agricultural Ecommerce Platform
"""
from rest_framework import generics, viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from typing import Dict

from products.models import Category, Product, ProductImage, ProductReview
from orders.models import Cart, CartItem, Order, OrderItem, Wishlist
from quality.models import QualityAnalysis, QualityReport
from accounts.models import SellerProfile, BuyerProfile
from quality.services import analyze_product_image

from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, SellerProfileSerializer,
    BuyerProfileSerializer, CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, ProductReviewSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderCreateSerializer,
    WishlistSerializer, QualityReportSerializer, ImageUploadSerializer,
    ProductSearchSerializer, QualityAnalysisSerializer
)

User = get_user_model()

# Authentication Views

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Create profile based on user type
        if user.user_type == 'seller':
            SellerProfile.objects.create(
                user=user,
                business_name=request.data.get('business_name', f"{user.username}'s Farm")
            )
        elif user.user_type == 'buyer':
            BuyerProfile.objects.create(user=user)
        
        return Response({
            'message': 'User registered successfully',
            'user_id': user.id,
            'user_type': user.user_type
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username and password:
        user = authenticate(username=username, password=password)
        if user:
            return Response({
                'message': 'Login successful',
                'user_id': user.id,
                'user_type': user.user_type,
                'username': user.username
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'error': 'Username and password required'
    }, status=status.HTTP_400_BAD_REQUEST)

# User Profile Views

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class SellerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'seller':
            return SellerProfile.objects.filter(user=self.request.user)
        return SellerProfile.objects.none()

class BuyerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BuyerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'buyer':
            return BuyerProfile.objects.filter(user=self.request.user)
        return BuyerProfile.objects.none()

# Category Views

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

# Product Views

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'organic', 'quality_grade']
    search_fields = ['name', 'description', 'origin_location']
    ordering_fields = ['price', 'quality_score', 'created_at', 'sales_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.action == 'list':
            return Product.objects.filter(status='active')
        return Product.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_cart(self, request, pk=None):
        """Add product to cart"""
        product = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if product.quantity_available < quantity:
            return Response({
                'error': 'Insufficient stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'message': 'Product added to cart',
            'cart_total_items': cart.total_items
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request, pk=None):
        """Add product to wishlist"""
        product = self.get_object()
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({'message': 'Product added to wishlist'})
        else:
            return Response({'message': 'Product already in wishlist'})
    
    @action(detail=True, methods=['get'])
    def quality_analysis(self, request, pk=None):
        """Get quality analysis for product"""
        product = self.get_object()
        analyses = product.quality_analyses.all()
        serializer = QualityAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

# Product Review Views

class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_pk')
        return ProductReview.objects.filter(product_id=product_id)
    
    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_pk')
        product = get_object_or_404(Product, id=product_id)
        serializer.save(buyer=self.request.user, product=product)

# Cart Views

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart.items.all()
    
    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)
    
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        """Update cart item quantity"""
        cart_item = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        
        if cart_item.product.quantity_available < quantity:
            return Response({
                'error': 'Insufficient stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'message': 'Quantity updated',
            'new_quantity': quantity
        })

# Order Views

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        order = serializer.save(buyer=self.request.user)
        
        # Clear cart after order creation
        cart = Cart.objects.filter(user=self.request.user).first()
        if cart:
            cart.items.all().delete()
        
        return order
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        if order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            order.save()
            return Response({'message': 'Order cancelled successfully'})
        else:
            return Response({
                'error': 'Order cannot be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)

# Wishlist Views

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Image Upload and Quality Analysis Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_product_image(request):
    """Upload product image and trigger quality analysis"""
    parser_classes = [MultiPartParser, FormParser]
    
    serializer = ImageUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        image = serializer.validated_data['image']
        product_id = serializer.validated_data['product_id']
        is_primary = serializer.validated_data['is_primary']
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Create ProductImage instance
            product_image = ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=is_primary
            )
            
            # Trigger quality analysis
            try:
                analysis_results = analyze_product_image(product_image.image.path)
                
                # Create QualityAnalysis record
                quality_analysis = QualityAnalysis.objects.create(
                    product=product,
                    image=product_image,
                    status='completed',
                    overall_score=analysis_results.get('overall_score', 0.0),
                    quality_grade=analysis_results.get('quality_grade', 'D'),
                    size_score=analysis_results.get('size_score', 0.0),
                    color_score=analysis_results.get('color_score', 0.0),
                    shape_score=analysis_results.get('shape_score', 0.0),
                    surface_score=analysis_results.get('surface_score', 0.0),
                    freshness_score=analysis_results.get('freshness_score', 0.0),
                    defects_detected=analysis_results.get('defects_detected', []),
                    defect_count=len(analysis_results.get('defects_detected', [])),
                    bounding_boxes=analysis_results.get('bounding_boxes', []),
                    class_predictions=analysis_results.get('class_predictions', []),
                    confidence_scores=analysis_results.get('confidence_scores', []),
                    estimated_weight=analysis_results.get('estimated_weight'),
                    ripeness_level=analysis_results.get('ripeness_level', ''),
                    processing_time=analysis_results.get('processing_time', 0.0)
                )
                
                # Update product quality metrics
                product.quality_score = analysis_results.get('overall_score', 0.0)
                product.quality_grade = analysis_results.get('quality_grade', 'D')
                product.quality_analyzed = True
                product.save()
                
                # Update ProductImage analysis status
                product_image.analyzed = True
                product_image.detected_objects = analysis_results.get('class_predictions', [])
                product_image.quality_metrics = {
                    'size_score': analysis_results.get('size_score', 0.0),
                    'color_score': analysis_results.get('color_score', 0.0),
                    'shape_score': analysis_results.get('shape_score', 0.0),
                    'surface_score': analysis_results.get('surface_score', 0.0),
                    'freshness_score': analysis_results.get('freshness_score', 0.0)
                }
                product_image.save()
                
                return Response({
                    'message': 'Image uploaded and analyzed successfully',
                    'image_id': product_image.id,
                    'quality_analysis': {
                        'overall_score': quality_analysis.overall_score,
                        'quality_grade': quality_analysis.quality_grade,
                        'defect_count': quality_analysis.defect_count
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # If analysis fails, still save the image
                return Response({
                    'message': 'Image uploaded successfully, but quality analysis failed',
                    'image_id': product_image.id,
                    'analysis_error': str(e)
                }, status=status.HTTP_201_CREATED)
                
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_existing_image(request, image_id):
    """Re-analyze existing product image"""
    try:
        product_image = ProductImage.objects.get(id=image_id)
        
        # Check permissions
        if (request.user.user_type == 'seller' and 
            product_image.product.seller != request.user):
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Run analysis
        analysis_results = analyze_product_image(product_image.image.path)
        
        # Update or create QualityAnalysis record
        quality_analysis, created = QualityAnalysis.objects.update_or_create(
            product=product_image.product,
            image=product_image,
            defaults={
                'status': 'completed',
                'overall_score': analysis_results.get('overall_score', 0.0),
                'quality_grade': analysis_results.get('quality_grade', 'D'),
                'size_score': analysis_results.get('size_score', 0.0),
                'color_score': analysis_results.get('color_score', 0.0),
                'shape_score': analysis_results.get('shape_score', 0.0),
                'surface_score': analysis_results.get('surface_score', 0.0),
                'freshness_score': analysis_results.get('freshness_score', 0.0),
                'defects_detected': analysis_results.get('defects_detected', []),
                'defect_count': len(analysis_results.get('defects_detected', [])),
                'processing_time': analysis_results.get('processing_time', 0.0)
            }
        )
        
        return Response({
            'message': 'Image analyzed successfully',
            'quality_analysis': QualityAnalysisSerializer(quality_analysis).data
        })
        
    except ProductImage.DoesNotExist:
        return Response({
            'error': 'Image not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Analysis failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Search and Filter Views

@api_view(['GET'])
@permission_classes([AllowAny])
def search_products(request):
    """Advanced product search with quality filters"""
    serializer = ProductSearchSerializer(data=request.query_params)
    if serializer.is_valid():
        queryset = Product.objects.filter(status='active')
        
        # Apply filters
        if serializer.validated_data.get('query'):
            query = serializer.validated_data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(origin_location__icontains=query)
            )
        
        if serializer.validated_data.get('category'):
            queryset = queryset.filter(category__slug=serializer.validated_data['category'])
        
        if serializer.validated_data.get('min_price'):
            queryset = queryset.filter(price__gte=serializer.validated_data['min_price'])
        
        if serializer.validated_data.get('max_price'):
            queryset = queryset.filter(price__lte=serializer.validated_data['max_price'])
        
        if serializer.validated_data.get('quality_grade'):
            queryset = queryset.filter(quality_grade=serializer.validated_data['quality_grade'])
        
        if serializer.validated_data.get('organic') is not None:
            queryset = queryset.filter(organic=serializer.validated_data['organic'])
        
        if serializer.validated_data.get('location'):
            location = serializer.validated_data['location']
            queryset = queryset.filter(origin_location__icontains=location)
        
        # Apply ordering
        ordering = serializer.validated_data.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        from django.core.paginator import Paginator
        paginator = Paginator(queryset, 20)
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        products_serializer = ProductListSerializer(
            page_obj, many=True, context={'request': request}
        )
        
        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': products_serializer.data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Dashboard Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_dashboard(request):
    """Seller dashboard with analytics"""
    if request.user.user_type != 'seller':
        return Response({
            'error': 'Access denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    products = Product.objects.filter(seller=request.user)
    orders = OrderItem.objects.filter(seller=request.user)
    
    dashboard_data = {
        'total_products': products.count(),
        'active_products': products.filter(status='active').count(),
        'total_sales': orders.count(),
        'total_revenue': sum(order.total_price for order in orders),
        'average_quality_score': products.aggregate(
            avg_score=Avg('quality_score')
        )['avg_score'] or 0,
        'quality_distribution': {
            'A': products.filter(quality_grade='A').count(),
            'B': products.filter(quality_grade='B').count(),
            'C': products.filter(quality_grade='C').count(),
            'D': products.filter(quality_grade='D').count(),
        },
        'recent_orders': OrderSerializer(
            Order.objects.filter(items__seller=request.user).distinct()[:5],
            many=True
        ).data
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buyer_dashboard(request):
    """Buyer dashboard with order history"""
    if request.user.user_type != 'buyer':
        return Response({
            'error': 'Access denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    orders = Order.objects.filter(buyer=request.user)
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    dashboard_data = {
        'total_orders': orders.count(),
        'total_spent': sum(order.total_amount for order in orders),
        'pending_orders': orders.filter(status='pending').count(),
        'completed_orders': orders.filter(status='delivered').count(),
        'wishlist_items': wishlist_items.count(),
        'recent_orders': OrderSerializer(orders[:5], many=True).data,
        'wishlist': WishlistSerializer(wishlist_items[:10], many=True).data
    }
    
    return Response(dashboard_data)

# Quality Report Views

class QualityReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QualityReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'seller':
            return QualityReport.objects.filter(product__seller=self.request.user)
        return QualityReport.objects.none()
