# Generated by Django 5.2.1 on 2025-06-03 07:39

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_orders', models.IntegerField(default=0)),
                ('unique_customers', models.IntegerField(default=0)),
                ('avg_order_value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('top_categories', models.JSONField(blank=True, default=list)),
                ('quality_distribution', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='QualityAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_analyses', models.IntegerField(default=0)),
                ('avg_processing_time', models.FloatField(default=0)),
                ('grade_distribution', models.JSONField(blank=True, default=dict)),
                ('accuracy_feedback', models.FloatField(default=0)),
                ('error_rate', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('date',)},
            },
        ),
        migrations.CreateModel(
            name='AnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('page_view', 'Page View'), ('product_view', 'Product View'), ('quality_analysis', 'Quality Analysis'), ('purchase', 'Purchase'), ('cart_add', 'Add to Cart'), ('search', 'Search'), ('login', 'Login'), ('registration', 'Registration')], max_length=50)),
                ('event_data', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['event_type', 'timestamp'], name='analytics_a_event_t_64745b_idx'), models.Index(fields=['user', 'timestamp'], name='analytics_a_user_id_5c8c13_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserBehaviorAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('page_views', models.IntegerField(default=0)),
                ('session_duration', models.IntegerField(default=0)),
                ('products_viewed', models.IntegerField(default=0)),
                ('searches_performed', models.IntegerField(default=0)),
                ('cart_additions', models.IntegerField(default=0)),
                ('purchases_made', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('user', 'date')},
            },
        ),
    ]
