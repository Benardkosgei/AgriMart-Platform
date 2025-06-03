"""
Management command to populate sample data for AgriMart platform
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage
from accounts.models import SellerProfile, BuyerProfile
from quality.models import QualityStandard, DefectType
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {'name': 'Fruits', 'slug': 'fruits', 'description': 'Fresh fruits from local farms'},
            {'name': 'Vegetables', 'slug': 'vegetables', 'description': 'Organic and conventional vegetables'},
            {'name': 'Grains', 'slug': 'grains', 'description': 'Rice, wheat, and other cereals'},
            {'name': 'Herbs', 'slug': 'herbs', 'description': 'Fresh herbs and spices'},
            {'name': 'Dairy', 'slug': 'dairy', 'description': 'Farm-fresh dairy products'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample users
        users_data = [
            {'username': 'farmer_john', 'email': 'john@farm.com', 'user_type': 'seller', 'first_name': 'John', 'last_name': 'Smith'},
            {'username': 'organic_mary', 'email': 'mary@organic.com', 'user_type': 'seller', 'first_name': 'Mary', 'last_name': 'Johnson'},
            {'username': 'buyer_alice', 'email': 'alice@example.com', 'user_type': 'buyer', 'first_name': 'Alice', 'last_name': 'Brown'},
            {'username': 'buyer_bob', 'email': 'bob@example.com', 'user_type': 'buyer', 'first_name': 'Bob', 'last_name': 'Wilson'},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={**user_data, 'password': 'password123'}
            )
            if created:
                user.set_password('password123')
                user.save()
                
                # Create profiles
                if user.user_type == 'seller':
                    SellerProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'business_name': f"{user.first_name}'s Farm",
                            'farm_location': f"{user.first_name}'s Valley, CA",
                            'organic_certified': random.choice([True, False]),
                            'description': f"Quality produce from {user.first_name}'s farm since 2010."
                        }
                    )
                elif user.user_type == 'buyer':
                    BuyerProfile.objects.get_or_create(user=user)
                
                self.stdout.write(f'Created user: {user.username} ({user.user_type})')
        
        # Create quality standards
        for category in Category.objects.all():
            QualityStandard.objects.get_or_create(
                category=category,
                defaults={
                    'grade_a_min_score': 0.8,
                    'grade_b_min_score': 0.6,
                    'grade_c_min_score': 0.4,
                    'size_weight': 0.2,
                    'color_weight': 0.25,
                    'shape_weight': 0.2,
                    'surface_weight': 0.25,
                    'freshness_weight': 0.1,
                    'max_defects_grade_a': 0,
                    'max_defects_grade_b': 2,
                    'max_defects_grade_c': 5,
                }
            )
        
        # Create defect types
        defect_types = [
            {'name': 'Bruising', 'description': 'Physical damage causing discoloration', 'severity_multiplier': 0.8},
            {'name': 'Spots', 'description': 'Dark or discolored spots on surface', 'severity_multiplier': 0.7},
            {'name': 'Cracks', 'description': 'Physical cracks or splits', 'severity_multiplier': 0.6},
            {'name': 'Mold', 'description': 'Fungal growth', 'severity_multiplier': 0.3},
            {'name': 'Insect Damage', 'description': 'Damage caused by insects', 'severity_multiplier': 0.5},
        ]
        
        for defect_data in defect_types:
            defect, created = DefectType.objects.get_or_create(
                name=defect_data['name'],
                defaults=defect_data
            )
            if created:
                # Associate with all categories
                defect.categories.set(Category.objects.all())
        
        # Create sample products
        sellers = User.objects.filter(user_type='seller')
        categories = Category.objects.all()
        
        products_data = [
            # Fruits
            {'name': 'Organic Apples', 'category': 'fruits', 'price': '4.99', 'unit': 'kg', 'organic': True},
            {'name': 'Fresh Strawberries', 'category': 'fruits', 'price': '6.99', 'unit': 'kg', 'organic': False},
            {'name': 'Premium Mangoes', 'category': 'fruits', 'price': '8.99', 'unit': 'kg', 'organic': True},
            {'name': 'Sweet Oranges', 'category': 'fruits', 'price': '3.99', 'unit': 'kg', 'organic': False},
            
            # Vegetables
            {'name': 'Organic Tomatoes', 'category': 'vegetables', 'price': '5.99', 'unit': 'kg', 'organic': True},
            {'name': 'Fresh Carrots', 'category': 'vegetables', 'price': '2.99', 'unit': 'kg', 'organic': False},
            {'name': 'Green Lettuce', 'category': 'vegetables', 'price': '1.99', 'unit': 'pieces', 'organic': True},
            {'name': 'Bell Peppers', 'category': 'vegetables', 'price': '4.49', 'unit': 'kg', 'organic': False},
            
            # Grains
            {'name': 'Organic Rice', 'category': 'grains', 'price': '12.99', 'unit': 'kg', 'organic': True},
            {'name': 'Whole Wheat', 'category': 'grains', 'price': '8.99', 'unit': 'kg', 'organic': False},
            
            # Herbs
            {'name': 'Fresh Basil', 'category': 'herbs', 'price': '2.49', 'unit': 'bunch', 'organic': True},
            {'name': 'Organic Cilantro', 'category': 'herbs', 'price': '1.99', 'unit': 'bunch', 'organic': True},
        ]
        
        for product_data in products_data:
            category = Category.objects.get(slug=product_data['category'])
            seller = random.choice(sellers)
            
            # Generate quality data
            quality_score = random.uniform(0.3, 0.95)
            if quality_score >= 0.8:
                quality_grade = 'A'
            elif quality_score >= 0.6:
                quality_grade = 'B'
            elif quality_score >= 0.4:
                quality_grade = 'C'
            else:
                quality_grade = 'D'
            
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                seller=seller,
                defaults={
                    'category': category,
                    'slug': product_data['name'].lower().replace(' ', '-'),
                    'description': f"High quality {product_data['name'].lower()} from {seller.first_name}'s farm. "
                                 f"{'Certified organic' if product_data['organic'] else 'Conventionally grown'}.",
                    'price': Decimal(product_data['price']),
                    'unit': product_data['unit'],
                    'quantity_available': random.randint(10, 100),
                    'minimum_order': 1,
                    'origin_location': f"{seller.first_name}'s Farm, California",
                    'organic': product_data['organic'],
                    'status': 'active',
                    'quality_score': quality_score,
                    'quality_grade': quality_grade,
                    'quality_analyzed': True,
                    'meta_title': f"Buy {product_data['name']} Online",
                    'meta_description': f"Fresh {product_data['name'].lower()} delivered to your door."
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name} (Grade {quality_grade})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- Categories: {Category.objects.count()}\n'
                f'- Users: {User.objects.count()}\n'
                f'- Products: {Product.objects.count()}\n'
                f'- Quality Standards: {QualityStandard.objects.count()}\n'
                f'- Defect Types: {DefectType.objects.count()}'
            )
        )
        
        self.stdout.write('\nSample login credentials:')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Seller: farmer_john / password123')
        self.stdout.write('Seller: organic_mary / password123')
        self.stdout.write('Buyer: buyer_alice / password123')
        self.stdout.write('Buyer: buyer_bob / password123')
