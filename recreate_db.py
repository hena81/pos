from app import app, db
from app.models import Product, Sale, SaleItem, Category

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    print("Database has been recreated successfully!")