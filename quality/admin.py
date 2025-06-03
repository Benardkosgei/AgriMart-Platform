from django.contrib import admin
from .models import QualityAnalysis, QualityStandard, DefectType, QualityReport

@admin.register(QualityAnalysis)
class QualityAnalysisAdmin(admin.ModelAdmin):
    list_display = ['product', 'quality_grade', 'overall_score', 'status', 'created_at']
    list_filter = ['quality_grade', 'status', 'defect_severity', 'created_at']
    search_fields = ['product__name', 'product__seller__username']
    readonly_fields = ['created_at', 'processing_time']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('product', 'image', 'status', 'model_version', 'confidence_threshold')
        }),
        ('Quality Scores', {
            'fields': ('overall_score', 'quality_grade', 'size_score', 'color_score',
                      'shape_score', 'surface_score', 'freshness_score')
        }),
        ('Defect Analysis', {
            'fields': ('defects_detected', 'defect_count', 'defect_severity')
        }),
        ('YOLO Results', {
            'fields': ('bounding_boxes', 'class_predictions', 'confidence_scores'),
            'classes': ('collapse',)
        }),
        ('Additional Metrics', {
            'fields': ('estimated_weight', 'ripeness_level', 'shelf_life_days'),
            'classes': ('collapse',)
        }),
        ('Processing Info', {
            'fields': ('processing_time', 'error_message', 'created_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(QualityStandard)
class QualityStandardAdmin(admin.ModelAdmin):
    list_display = ['category', 'grade_a_min_score', 'grade_b_min_score', 'grade_c_min_score']
    list_filter = ['created_at']
    search_fields = ['category__name']

@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity_multiplier']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories']

@admin.register(QualityReport)
class QualityReportAdmin(admin.ModelAdmin):
    list_display = ['product', 'total_analyses', 'average_score', 'most_common_grade', 'updated_at']
    list_filter = ['most_common_grade', 'quality_trend', 'updated_at']
    search_fields = ['product__name', 'product__seller__username']
    readonly_fields = ['created_at', 'updated_at']
