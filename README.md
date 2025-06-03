# 🌾 AgriMart - AI-Powered Agricultural E-commerce Platform

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-blue.svg)](https://ultralytics.com/)
[![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

## 🚀 Overview

AgriMart is a comprehensive agricultural marketplace platform that revolutionizes agricultural commerce by combining advanced e-commerce functionality with AI-powered quality assessment using YOLO computer vision technology. The platform enables farmers and agricultural businesses to sell their products while providing buyers with AI-verified quality indicators, ensuring transparency and trust in agricultural transactions.

## ✨ Key Features

### 🤖 Advanced AI Quality Assessment
- **YOLO v8 Integration**: State-of-the-art computer vision for automatic quality grading
- **Real-time Analysis**: Instant quality scoring (A-D grades) for uploaded product images
- **Multi-factor Assessment**: Color, size, shape, defect detection, and freshness analysis
- **Product-specific Standards**: Optimized algorithms for different agricultural products
- **Comprehensive Reporting**: Detailed quality reports with improvement recommendations

### 🛒 Complete E-commerce Solution
- **Product Management**: Comprehensive catalog with categories, specifications, and quality indicators
- **Smart Shopping Cart**: Quality-aware cart with intelligent recommendations
- **Order Processing**: Complete order lifecycle with real-time tracking
- **User Management**: Separate seller and buyer profiles with role-based permissions
- **Advanced Search**: Quality-based filtering and intelligent product discovery

### 💳 Secure Payment Processing
- **M-Pesa Integration**: STK Push for mobile money payments (optimized for African markets)
- **Multi-gateway Support**: Stripe, PayPal, and local payment processors
- **Payment Analytics**: Real-time transaction tracking and financial reporting
- **Automated Refunds**: Intelligent refund processing with dispute management

### 📊 Business Intelligence & Analytics
- **Sales Dashboard**: Revenue tracking, performance metrics, and trend analysis
- **Quality Insights**: AI-generated insights on product quality patterns and trends
- **Inventory Management**: Smart stock tracking with predictive reorder alerts
- **Customer Analytics**: User behavior analysis and purchase pattern insights

### 🔔 Multi-channel Notification System
- **Real-time Delivery**: Email, SMS, push notifications, and in-app alerts
- **WebSocket Integration**: Live updates and real-time communication
- **Smart Alerts**: Quality-based notifications and automated status updates
- **Campaign Management**: Targeted marketing and promotional notifications

### 🎯 Advanced Promotions & Loyalty
- **Dynamic Pricing**: AI-assisted pricing based on quality grades and market conditions
- **Loyalty Programs**: Points-based reward system with tier benefits
- **Flash Sales**: Time-limited offers with intelligent inventory management
- **Flexible Coupons**: Advanced discount and promotion management system

## 🛠️ Technology Stack

### Backend Infrastructure
- **Django 5.2**: High-performance web framework with advanced ORM
- **Django REST Framework**: Comprehensive API development with serialization
- **PostgreSQL**: Robust relational database with advanced indexing
- **Redis**: High-performance caching and session management
- **Celery**: Distributed task queue for background processing

### AI/ML & Computer Vision
- **YOLOv8**: Latest object detection for quality assessment
- **OpenCV**: Advanced computer vision and image processing
- **Ultralytics**: Professional YOLO model management and training
- **NumPy & Pillow**: Numerical processing and image manipulation
- **scikit-learn**: Machine learning for quality prediction models

### Payment & Financial
- **M-Pesa API**: Mobile money integration for African markets
- **Stripe**: International credit card and payment processing
- **PayPal**: Global online payment solutions
- **Webhook Processing**: Real-time payment event handling

### Real-time & Communication
- **Django Channels**: WebSocket support for real-time features
- **Redis Channels**: Scalable channel layer for live communication
- **Twilio**: SMS and voice communication services
- **Push Notifications**: Mobile and web push notification services

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+ with pip and virtual environment support
- Node.js 16+ for frontend dependencies and build tools
- Redis 6+ for caching and real-time features
- PostgreSQL 13+ (optional, SQLite included for development)
- Git for version control

### Quick Start Guide

1. **Clone and Setup Repository**
   ```bash
   git clone https://github.com/your-org/agrimart.git
   cd agrimart
   
   # Create virtual environment
   python -m venv agrimart_env
   source agrimart_env/bin/activate  # On Windows: agrimart_env\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   # Core dependencies
   pip install -r requirements.txt
   
   # Development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

3. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration (use your preferred editor)
   nano .env
   ```

4. **Database Setup**
   ```bash
   # Run database migrations
   python manage.py migrate --settings=agrimart.settings_simple
   
   # Create administrative superuser
   python manage.py createsuperuser --settings=agrimart.settings_simple
   ```

5. **Load Sample Data**
   ```bash
   # Populate with sample agricultural products and categories
   python manage.py populate_sample_data --settings=agrimart.settings_simple
   ```

6. **Start Development Server**
   ```bash
   # Start the Django development server
   python manage.py runserver --settings=agrimart.settings_simple
   
   # Access the platform at http://localhost:8000
   # Admin panel at http://localhost:8000/admin/
   # API documentation at http://localhost:8000/api/
   ```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root with the following configurations:

```bash
# Core Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/agrimart
# For development with SQLite (default):
# DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AI/ML Configuration
YOLO_MODEL_PATH=models/agri_quality_v8.pt
YOLO_CONFIDENCE_THRESHOLD=0.7

# Payment Gateway Configuration
# M-Pesa (Safaricom)
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_mpesa_passkey

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# File Storage (AWS S3)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=agrimart-media
AWS_S3_REGION_NAME=us-east-1
```

## 📚 API Documentation

### Authentication
All API endpoints require authentication via token or session. Obtain tokens through:

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### Core API Endpoints

#### 🏷️ Products Management
```bash
# List all products with quality indicators
GET /api/products/

# Create new product (sellers only)
POST /api/products/
{
    "name": "Premium Red Apples",
    "category": 1,
    "price": "250.00",
    "description": "Fresh organic apples",
    "images": ["image1.jpg", "image2.jpg"]
}

# Get product details with quality analysis
GET /api/products/{id}/

# Update product information
PUT /api/products/{id}/

# Delete product
DELETE /api/products/{id}/
```

#### 🔬 Quality Analysis
```bash
# Analyze product image quality
POST /api/quality/analyze/
Content-Type: multipart/form-data
{
    "image": <image_file>,
    "product_type": "apple"
}

# Get quality analysis reports
GET /api/quality/reports/

# Get quality standards for products
GET /api/quality/standards/
```

#### 🛍️ Order Management
```bash
# Get user's orders
GET /api/orders/

# Create new order
POST /api/orders/
{
    "items": [
        {"product": 1, "quantity": 5},
        {"product": 2, "quantity": 3}
    ],
    "delivery_address": "123 Main St, Nairobi"
}

# Get order details
GET /api/orders/{id}/

# Update order status (sellers)
PUT /api/orders/{id}/
{
    "status": "shipped",
    "tracking_number": "TRK123456"
}
```

#### 💳 Payment Processing
```bash
# Initiate M-Pesa payment
POST /api/payments/mpesa/initiate/
{
    "order_id": 123,
    "phone_number": "254712345678"
}

# Get payment history
GET /api/payments/history/

# Request refund
POST /api/payments/refund/
{
    "payment_id": "pay_123456",
    "amount": "100.00",
    "reason": "product_defect"
}
```

## 🧠 YOLO Model Integration

### Model Configuration
The platform supports custom YOLO models trained specifically for agricultural quality assessment:

```python
# Quality assessment configuration
YOLO_CONFIG = {
    'model_path': 'models/agri_quality_v8.pt',
    'confidence_threshold': 0.7,
    'quality_standards': {
        'apple': {
            'color_range': [(0, 100, 100), (10, 255, 255)],
            'size_range': (5000, 50000),
            'shape_circularity': 0.7
        },
        'tomato': {
            'color_range': [(0, 100, 100), (15, 255, 255)],
            'size_range': (3000, 30000),
            'shape_circularity': 0.8
        }
    }
}
```

### Quality Assessment Process
1. **Image Upload & Validation**: User uploads product image with format validation
2. **Preprocessing**: Image normalization, enhancement, and standardization
3. **YOLO Object Detection**: Identify and locate agricultural products in images
4. **Feature Extraction**: Extract color, size, shape, and texture features
5. **Defect Detection**: Identify bruises, spots, deformations, and quality issues
6. **Quality Scoring**: Multi-factor scoring algorithm with weighted criteria
7. **Grade Assignment**: Automated A-D grade assignment based on quality score
8. **Report Generation**: Comprehensive quality report with recommendations

### Supported Product Categories
- **Fruits**: Apples, bananas, oranges, tomatoes, mangoes, avocados
- **Vegetables**: Cabbage, carrots, lettuce, potatoes, onions, peppers
- **Grains**: Rice, wheat, corn, beans, lentils, quinoa
- **Root Vegetables**: Sweet potatoes, cassava, yams, turnips

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Production Setup Checklist
- [ ] Configure PostgreSQL database with proper indexing
- [ ] Set up Redis cluster for high availability
- [ ] Configure Nginx with SSL certificates (Let's Encrypt)
- [ ] Set up Celery workers and beat scheduler
- [ ] Configure monitoring (Sentry, Prometheus)
- [ ] Set up automated backups
- [ ] Configure CDN for static files
- [ ] Implement load balancing
- [ ] Set up log aggregation

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Run all tests with coverage
python manage.py test --keepdb --parallel --settings=agrimart.settings_simple
coverage run --source='.' manage.py test --settings=agrimart.settings_simple
coverage report --show-missing

# Run specific test categories
python manage.py test products.tests.test_quality_analysis --settings=agrimart.settings_simple
python manage.py test payments.tests.test_mpesa_integration --settings=agrimart.settings_simple
python manage.py test orders.tests.test_order_workflow --settings=agrimart.settings_simple
```

### API Testing with Examples
```bash
# Test quality analysis endpoint
curl -X POST http://localhost:8000/api/quality/analyze/ \
  -H "Authorization: Token your_token_here" \
  -F "image=@sample_apple.jpg" \
  -F "product_type=apple"

# Test M-Pesa payment initiation
curl -X POST http://localhost:8000/api/payments/mpesa/initiate/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 123,
    "phone_number": "254712345678"
  }'
```

## 🤝 Contributing

### Development Workflow
1. **Fork the repository** and create a feature branch
2. **Install development dependencies**: `pip install -r requirements-dev.txt`
3. **Follow coding standards**: Black formatting, PEP 8 compliance
4. **Write comprehensive tests** with >80% coverage
5. **Update documentation** for new features
6. **Submit pull request** with detailed description

### Code Quality Standards
- **Type Hints**: Use Python type hints for all function signatures
- **Docstrings**: Google-style docstrings for all classes and functions
- **Testing**: Unit tests, integration tests, and API tests
- **Performance**: Optimize database queries and API response times
- **Security**: Follow OWASP guidelines and Django security best practices

## 📊 Performance & Monitoring

### Key Metrics
- **API Response Time**: <200ms for standard endpoints
- **Quality Analysis**: <5 seconds for image processing
- **Database Queries**: Optimized with proper indexing
- **Caching**: 90%+ cache hit rate for static content
- **Uptime**: 99.9% availability target

### Monitoring Stack
- **Application Performance**: Sentry for error tracking
- **Infrastructure**: Prometheus + Grafana for metrics
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Uptime Monitoring**: Pingdom or UptimeRobot

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for complete details.

## 🆘 Support & Community

### Getting Help
- **Documentation**: [Complete API Docs](https://docs.agrimart.com)
- **GitHub Issues**: Report bugs and request features
- **Community Forum**: [Discord Server](https://discord.gg/agrimart)
- **Email Support**: support@agrimart.com

### Professional Services
- **Custom Development**: Tailored features and integrations
- **Deployment Support**: Production setup and optimization
- **Training**: Team training and best practices
- **Consulting**: Architecture and scaling guidance

## 🌍 Roadmap

### Upcoming Features
- [ ] **Mobile Applications**: Native iOS and Android apps
- [ ] **Blockchain Integration**: Supply chain traceability
- [ ] **IoT Integration**: Smart farming device connectivity
- [ ] **Advanced Analytics**: Predictive market analysis
- [ ] **Multi-language Support**: Localization for global markets
- [ ] **Augmented Reality**: AR-based quality assessment

### Version History
- **v1.0.0**: Initial release with core e-commerce and YOLO integration
- **v1.1.0**: Enhanced quality analysis and M-Pesa payments
- **v1.2.0**: Advanced analytics and notification system
- **v2.0.0**: Multi-vendor marketplace and loyalty programs

## 🙏 Acknowledgments

Special thanks to the open-source community and these amazing projects:
- **Ultralytics YOLO**: Cutting-edge computer vision models
- **Django REST Framework**: Powerful API development framework
- **Safaricom M-Pesa**: Mobile payment innovation for Africa
- **OpenCV Community**: Computer vision library and algorithms
- **All Contributors**: Developers, testers, and community members

---

<div align="center">

**🌾 AgriMart Platform**

*Revolutionizing agricultural commerce with AI-powered quality assessment*

[![GitHub Stars](https://img.shields.io/github/stars/your-org/agrimart?style=social)](https://github.com/your-org/agrimart)
[![Follow](https://img.shields.io/twitter/follow/agrimart?style=social)](https://twitter.com/agrimart)

</div>
