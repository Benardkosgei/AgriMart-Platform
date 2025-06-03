#!/usr/bin/env python
"""
AgriMart Development Server Launcher
"""
import os
import sys
import subprocess
import time

def print_banner():
    """Print the AgriMart banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     🌱 AgriMart - AI-Powered Agricultural Marketplace 🌱      ║
    ║                                                               ║
    ║     YOLO-Based Quality Analysis • Django REST API            ║
    ║     Complete Ecommerce Platform • Multi-User Support        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if basic requirements are met"""
    try:
        import django
        print(f"✅ Django {django.get_version()} is installed")
    except ImportError:
        print("❌ Django is not installed. Please run: pip install -r requirements.txt")
        return False
    
    try:
        import rest_framework
        print("✅ Django REST Framework is installed")
    except ImportError:
        print("❌ Django REST Framework is not installed")
        return False
    
    return True

def run_migrations():
    """Run database migrations"""
    print("\n🔄 Running database migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Migrations completed successfully")
    except subprocess.CalledProcessError:
        print("❌ Migration failed")
        return False
    return True

def collect_static():
    """Collect static files"""
    print("\n📁 Collecting static files...")
    try:
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], 
                      check=True, capture_output=True)
        print("✅ Static files collected")
    except subprocess.CalledProcessError:
        print("⚠️  Static files collection failed (this is ok for development)")

def create_superuser_if_needed():
    """Create superuser if it doesn't exist"""
    print("\n👤 Checking for admin user...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            print("Creating admin user (username: admin, password: admin123)")
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✅ Admin user created successfully")
        else:
            print("✅ Admin user already exists")
    except Exception as e:
        print(f"⚠️  Could not create admin user: {e}")

def start_server():
    """Start the development server"""
    print("\n🚀 Starting development server...")
    print("\n" + "="*60)
    print("🌐 Server will be available at:")
    print("   Web Interface:     http://localhost:8000/")
    print("   Admin Panel:       http://localhost:8000/admin/")
    print("   API Documentation: http://localhost:8000/api/")
    print("\n🔑 Login Credentials:")
    print("   Admin:           admin / admin123")
    print("   Sample Seller:   farmer_john / password123")
    print("   Sample Buyer:    buyer_alice / password123")
    print("="*60 + "\n")
    
    try:
        subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thank you for using AgriMart!")

def main():
    """Main function"""
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print("❌ Error: manage.py not found. Please run this script from the agrimart directory.")
        sys.exit(1)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrimart.settings')
    
    # Setup Django
    import django
    django.setup()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Run setup steps
    if not run_migrations():
        sys.exit(1)
    
    collect_static()
    create_superuser_if_needed()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
