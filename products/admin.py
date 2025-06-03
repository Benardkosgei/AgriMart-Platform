from django.contrib import admin
from .models import Category, Product, ProductImage, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['analyzed', 'analysis_date']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'quality_grade', 'status', 'created_at']
    list_filter = ['category', 'quality_grade', 'status', 'organic', 'created_at']
    search_fields = ['name', 'description', 'seller__username']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['quality_score', 'quality_grade', 'quality_analyzed', 'views_count', 'sales_count']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'seller', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'unit', 'quantity_available', 'minimum_order')
        }),
        ('Product Details', {
            'fields': ('harvest_date', 'expiry_date', 'origin_location', 'organic', 'status')
        }),
        ('Quality Assessment', {
            'fields': ('quality_score', 'quality_grade', 'quality_analyzed'),
            'classes': ('collapse',)
        }),
        ('SEO & Metadata', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'sales_count'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'analyzed', 'analysis_date']
    list_filter = ['is_primary', 'analyzed', 'analysis_date']
    search_fields = ['product__name', 'alt_text']
    readonly_fields = ['analyzed', 'analysis_date', 'detected_objects', 'quality_metrics']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'buyer', 'rating', 'verified_purchase', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'buyer__username', 'title']
    readonly_fields = ['helpful_votes', 'created_at']
