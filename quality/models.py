from django.db import models
from products.models import Product, ProductImage
from django.core.validators import MinValueValidator, MaxValueValidator

class QualityAnalysis(models.Model):
    """Detailed quality analysis results from YOLO model"""
    
    ANALYSIS_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quality_analyses')
    image = models.ForeignKey(ProductImage, on_delete=models.CASCADE, related_name='quality_analyses')
    
    # Analysis metadata
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS, default='pending')
    model_version = models.CharField(max_length=50, default='yolov8')
    confidence_threshold = models.FloatField(default=0.5)
    
    # Overall quality metrics
    overall_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    quality_grade = models.CharField(max_length=1)  # A, B, C, D
    
    # Specific quality metrics
    size_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    color_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    shape_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    surface_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    freshness_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Defect detection
    defects_detected = models.JSONField(default=list, blank=True)  # List of detected defects
    defect_count = models.PositiveIntegerField(default=0)
    defect_severity = models.CharField(max_length=20, default='none')  # none, low, medium, high
    
    # YOLO detection results
    bounding_boxes = models.JSONField(default=list, blank=True)  # YOLO bounding boxes
    class_predictions = models.JSONField(default=list, blank=True)  # Predicted classes
    confidence_scores = models.JSONField(default=list, blank=True)  # Confidence scores
    
    # Additional metrics
    estimated_weight = models.FloatField(blank=True, null=True)  # Estimated weight from image
    ripeness_level = models.CharField(max_length=20, blank=True)  # underripe, ripe, overripe
    shelf_life_days = models.PositiveIntegerField(blank=True, null=True)  # Estimated shelf life
    
    # Processing info
    processing_time = models.FloatField(blank=True, null=True)  # Time taken in seconds
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quality Analysis for {self.product.name} - Grade {self.quality_grade}"

class QualityStandard(models.Model):
    """Quality standards and thresholds for different product categories"""
    
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE, related_name='quality_standards')
    
    # Grade thresholds
    grade_a_min_score = models.FloatField(default=0.8)
    grade_b_min_score = models.FloatField(default=0.6)
    grade_c_min_score = models.FloatField(default=0.4)
    
    # Specific metric weights
    size_weight = models.FloatField(default=0.2)
    color_weight = models.FloatField(default=0.2)
    shape_weight = models.FloatField(default=0.2)
    surface_weight = models.FloatField(default=0.2)
    freshness_weight = models.FloatField(default=0.2)
    
    # Defect tolerance
    max_defects_grade_a = models.PositiveIntegerField(default=0)
    max_defects_grade_b = models.PositiveIntegerField(default=2)
    max_defects_grade_c = models.PositiveIntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Quality Standards for {self.category.name}"

class DefectType(models.Model):
    """Types of defects that can be detected"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    severity_multiplier = models.FloatField(default=1.0)  # How much this defect affects quality
    categories = models.ManyToManyField('products.Category', related_name='defect_types')
    
    def __str__(self):
        return self.name

class QualityReport(models.Model):
    """Summary quality reports for products"""
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='quality_report')
    
    # Overall statistics
    total_analyses = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    most_common_grade = models.CharField(max_length=1, blank=True)
    
    # Grade distribution
    grade_a_count = models.PositiveIntegerField(default=0)
    grade_b_count = models.PositiveIntegerField(default=0)
    grade_c_count = models.PositiveIntegerField(default=0)
    grade_d_count = models.PositiveIntegerField(default=0)
    
    # Trend analysis
    quality_trend = models.CharField(max_length=20, blank=True)  # improving, stable, declining
    last_analysis_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Quality Report for {self.product.name}"
