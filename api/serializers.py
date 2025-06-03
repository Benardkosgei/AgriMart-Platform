"""
API Serializers for AgriMart Agricultural Ecommerce Platform
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductReview
from orders.models import Cart, CartItem, Order, OrderItem, Wishlist
from quality.models import QualityAnalysis, QualityReport
from accounts.models import SellerProfile, BuyerProfile

User = get_user_model()

# User and Authentication Serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'user_type', 
                 'first_name', 'last_name', 'phone_number']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone_number', 'profile_image', 'address',
                 'city', 'state', 'postal_code', 'country', 'is_verified',
                 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined', 'is_verified']

class SellerProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = '__all__'

class BuyerProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = BuyerProfile
        fields = '__all__'

# Product Serializers

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active', 
                 'products_count', 'created_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(status='active').count()

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'analyzed', 
                 'analysis_date', 'detected_objects', 'quality_metrics']

class QualityAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityAnalysis
        fields = ['id', 'overall_score', 'quality_grade', 'size_score',
                 'color_score', 'shape_score', 'surface_score', 'freshness_score',
                 'defects_detected', 'defect_count', 'defect_severity',
                 'ripeness_level', 'shelf_life_days', 'created_at']

class ProductReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'rating', 'title', 'comment', 'buyer_name',
                 'verified_purchase', 'helpful_votes', 'created_at']

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'unit', 'category_name',
                 'seller_name', 'primary_image', 'quality_score', 'quality_grade',
                 'quantity_available', 'organic', 'average_rating', 'reviews_count',
                 'created_at']
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    seller = UserProfileSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    quality_analyses = QualityAnalysisSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'unit',
                 'quantity_available', 'minimum_order', 'harvest_date',
                 'expiry_date', 'origin_location', 'organic', 'status',
                 'meta_title', 'meta_description', 'images', 'uploaded_images']
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = Product.objects.create(**validated_data)
        
        # Create ProductImage instances for uploaded images
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)  # First image is primary
            )
        
        return product

# Cart and Order Serializers

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'seller_name', 'quantity', 'unit_price',
                 'total_price', 'quality_grade', 'quality_score', 'status']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'buyer_name', 'status', 'payment_status',
                 'payment_method', 'subtotal', 'tax_amount', 'shipping_amount',
                 'discount_amount', 'total_amount', 'shipping_address',
                 'shipping_city', 'shipping_state', 'shipping_postal_code',
                 'shipping_country', 'tracking_number', 'estimated_delivery_date',
                 'items', 'total_items', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'shipping_city', 'shipping_state',
                 'shipping_postal_code', 'shipping_country', 'payment_method',
                 'delivery_instructions', 'preferred_delivery_date', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                seller=product.seller,
                quantity=item_data['quantity'],
                unit_price=product.price,
                quality_grade=product.quality_grade,
                quality_score=product.quality_score
            )
        
        return order

# Wishlist Serializer

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'added_at']

# Quality Report Serializer

class QualityReportSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = QualityReport
        fields = ['id', 'product_name', 'total_analyses', 'average_score',
                 'most_common_grade', 'grade_a_count', 'grade_b_count',
                 'grade_c_count', 'grade_d_count', 'quality_trend',
                 'last_analysis_date', 'updated_at']

# Image Upload Serializer

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    product_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=False)
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
            # Check if user owns the product (if seller)
            request = self.context.get('request')
            if request and request.user.user_type == 'seller':
                if product.seller != request.user:
                    raise serializers.ValidationError("You can only upload images for your own products")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        return value

# Search and Filter Serializers

class ProductSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    quality_grade = serializers.ChoiceField(choices=['A', 'B', 'C', 'D'], required=False)
    organic = serializers.BooleanField(required=False)
    location = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        choices=['price', '-price', 'quality_score', '-quality_score', 'created_at', '-created_at'],
        required=False
    )
