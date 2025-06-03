# AgriMart - AI-Powered Agricultural Ecommerce Platform

## Overview

AgriMart is a comprehensive Django-based agricultural ecommerce platform that integrates YOLO (You Only Look Once) computer vision technology for automated produce quality assessment. The platform provides a complete marketplace solution where sellers can list agricultural products with AI-powered quality analysis, and buyers can purchase high-quality produce with confidence.

## 🌟 Key Features

### 🤖 AI-Powered Quality Analysis
- **YOLO Integration**: Real-time image analysis using YOLOv8 for object detection and quality assessment
- **Quality Grading**: Automatic A-D grading system based on visual features
- **Defect Detection**: Identification of spots, bruises, cracks, and other quality issues
- **Multi-metric Analysis**: Evaluation of size, color, shape, surface quality, and freshness

### 🛒 Complete Ecommerce Platform
- **User Management**: Separate interfaces for buyers, sellers, and administrators
- **Product Catalog**: Comprehensive product listings with categories and filters
- **Shopping Cart**: Full cart functionality with quantity management
- **Order System**: Complete order processing and tracking
- **Payment Integration**: Ready for payment gateway integration

### 📊 Analytics & Reporting
- **Quality Reports**: Detailed analysis of product quality trends
- **Seller Dashboard**: Sales analytics, product performance, and quality metrics
- **Buyer Dashboard**: Order history, wishlist, and purchase analytics

### 🔌 RESTful API
- **Comprehensive Endpoints**: Full API coverage for all platform features
- **Authentication**: Token-based authentication system
- **Documentation**: Well-documented API with usage examples

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 5.2+
- OpenCV
- PyTorch
- Ultralytics YOLOv8

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd agrimart
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure settings**
```bash
# Copy example settings
cp agrimart/settings.py.example agrimart/settings.py
# Edit settings as needed
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Populate sample data**
```bash
python manage.py populate_sample_data
```

8. **Run development server**
```bash
python manage.py runserver
```

### Access the Platform
- **Web Interface**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/

## 📁 Project Structure

```
agrimart/
├── accounts/           # User management and profiles
├── api/               # REST API endpoints and serializers
├── orders/            # Shopping cart and order management
├── products/          # Product catalog and categories
├── quality/           # YOLO analysis and quality assessment
├── templates/         # HTML templates
├── static/            # Static files (CSS, JS, images)
├── media/             # Uploaded files
├── agrimart/          # Main project settings
└── manage.py          # Django management script
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - defaults to SQLite)
DATABASE_URL=postgres://user:pass@localhost/dbname

# YOLO Model Path (optional)
YOLO_MODEL_PATH=/path/to/custom/model.pt

# Quality Analysis Settings
QUALITY_SCORE_THRESHOLD=0.5
MAX_IMAGE_SIZE=10485760  # 10MB

# Email Settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

#### SQLite (Default)
No additional configuration needed. Database file will be created automatically.

#### PostgreSQL (Production)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'agrimart_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔌 API Usage

### Authentication

**Register User**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "user_type": "buyer"
  }'
```

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123"
  }'
```

### Product Management

**List Products**
```bash
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Token your-token-here"
```

**Create Product**
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Organic Tomatoes",
    "category": 1,
    "description": "Fresh organic tomatoes",
    "price": "5.99",
    "unit": "kg",
    "quantity_available": 50,
    "origin_location": "California",
    "organic": true
  }'
```

**Upload Product Image with Quality Analysis**
```bash
curl -X POST http://localhost:8000/api/upload-image/ \
  -H "Authorization: Token your-token-here" \
  -F "image=@/path/to/image.jpg" \
  -F "product_id=1" \
  -F "is_primary=true"
```

### Search and Filtering

**Search Products**
```bash
curl -X GET "http://localhost:8000/api/search/?query=tomato&category=vegetables&quality_grade=A&organic=true&min_price=3.00&max_price=10.00"
```

### Order Management

**Add to Cart**
```bash
curl -X POST http://localhost:8000/api/products/1/add_to_cart/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 2}'
```

**Create Order**
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": "123 Main St",
    "shipping_city": "Anytown",
    "shipping_state": "CA",
    "shipping_postal_code": "12345",
    "shipping_country": "USA",
    "payment_method": "credit_card",
    "items": [
      {"product_id": 1, "quantity": 2}
    ]
  }'
```

## 🧠 YOLO Quality Analysis

### How It Works

1. **Image Upload**: Sellers upload high-quality images of their produce
2. **YOLO Processing**: The YOLOv8 model analyzes the image for:
   - Object detection and classification
   - Size estimation
   - Color analysis
   - Shape regularity
   - Surface quality assessment
   - Defect detection

3. **Quality Scoring**: Multiple metrics are combined to generate an overall quality score:
   - **Size Score** (20%): Based on object size and uniformity
   - **Color Score** (25%): Color consistency and freshness indicators
   - **Shape Score** (20%): Shape regularity and expected form
   - **Surface Score** (25%): Surface smoothness and defect presence
   - **Freshness Score** (10%): Overall freshness indicators

4. **Grading System**:
   - **Grade A** (80-100%): Premium quality
   - **Grade B** (60-79%): Good quality
   - **Grade C** (40-59%): Average quality
   - **Grade D** (0-39%): Below average quality

### Custom Model Training

To use your own trained YOLO model:

1. Train your model using Ultralytics YOLOv8
2. Save the model weights (.pt file)
3. Update `YOLO_MODEL_PATH` in settings
4. Restart the application

```python
# settings.py
YOLO_MODEL_PATH = '/path/to/your/custom_model.pt'
```

## 👥 User Roles

### Sellers
- Upload and manage products
- Add product images for quality analysis
- View sales analytics and quality reports
- Manage inventory and pricing
- Track orders and customer feedback

### Buyers
- Browse products with quality indicators
- Search and filter by quality grades
- Add products to cart and wishlist
- Place orders and track delivery
- Leave reviews and ratings

### Administrators
- Manage all users and products
- Configure quality standards
- Monitor platform analytics
- Manage categories and defect types
- System configuration and maintenance

## 📊 Quality Metrics

### Analysis Components

**Visual Features**:
- Color uniformity and vibrancy
- Size consistency and appropriate dimensions
- Shape regularity and expected form
- Surface smoothness and texture

**Defect Detection**:
- Spots and discoloration
- Bruises and physical damage
- Cracks and structural issues
- Mold and decay indicators
- Insect damage

**Quality Indicators**:
- Ripeness level assessment
- Estimated shelf life
- Freshness scoring
- Overall condition rating

## 🔐 Security Features

- Token-based authentication
- Role-based access control
- Input validation and sanitization
- CSRF protection
- Secure file upload handling
- SQL injection prevention

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test products
python manage.py test quality
python manage.py test orders
```

## 📈 Performance Optimization

### Image Processing
- Optimized image resizing and compression
- Efficient YOLO model loading
- Background processing for analysis
- Caching of analysis results

### Database
- Indexed fields for fast queries
- Optimized database queries
- Connection pooling (in production)
- Query optimization for large datasets

### API
- Pagination for large result sets
- Response caching
- Rate limiting (recommended for production)
- Gzip compression

## 🚀 Deployment

### Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "agrimart.wsgi:application", "--bind", "0.0.0.0:8000"]
```

2. **Build and run**
```bash
docker build -t agrimart .
docker run -p 8000:8000 agrimart
```

### Production Considerations

- Use PostgreSQL or MySQL for database
- Configure Redis for caching
- Set up Nginx for static file serving
- Use Celery for background tasks
- Configure proper logging
- Set up monitoring and alerts
- Enable SSL/HTTPS
- Configure backup strategy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and request features via GitHub issues
- **API Documentation**: Available at `/api/` endpoint when running the server

## 🔄 Changelog

### Version 1.0.0
- Initial release with core ecommerce functionality
- YOLO-based quality analysis system
- RESTful API with comprehensive endpoints
- User management with buyer/seller roles
- Product catalog with categories and search
- Order processing and cart management
- Admin interface for platform management
- Sample data and documentation

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Payment gateway integration
- [ ] Advanced search with ML recommendations
- [ ] Batch processing for large image uploads
- [ ] Integration with IoT sensors for farm data
