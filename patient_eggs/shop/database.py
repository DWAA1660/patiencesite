from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class WeeklyInventory(db.Model):
    """Model for weekly inventory data."""
    __tablename__ = 'weekly_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: YYYY-WW (e.g., 2025-12)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Integer, default=50)
    available = db.Column(db.Integer, default=50)
    reserved = db.Column(db.Integer, default=0)
    label = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @staticmethod
    def generate_weeks(start_date=None, num_weeks=52, eggs_per_week=50):
        """Generate weekly inventory for a year starting from the given date."""
        if start_date is None:
            # Start from the next Monday
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7  # If today is Monday, start from next Monday
            start_date = today + timedelta(days=days_until_monday)
        
        weeks = []
        for i in range(num_weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            
            # Format: YYYY-WW (year and week number)
            year = week_start.year
            week_num = week_start.isocalendar()[1]
            week_id = f"{year}-{week_num:02d}"
            
            # Format the label
            label = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
            
            weeks.append({
                "week_id": week_id,
                "start_date": week_start,
                "end_date": week_end,
                "total": eggs_per_week,
                "available": eggs_per_week,
                "reserved": 0,
                "label": label
            })
        
        return weeks

class CartItem(db.Model):
    """Model for cart items."""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.String(36), nullable=False)  # UUID for the cart
    product_id = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class CartItemWeek(db.Model):
    """Model for cart item week selections."""
    __tablename__ = 'cart_item_weeks'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_item_id = db.Column(db.Integer, db.ForeignKey('cart_items.id'), nullable=False)
    week_id = db.Column(db.String(20), db.ForeignKey('weekly_inventory.week_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    cart_item = db.relationship('CartItem', backref=db.backref('week_selections', lazy=True))
    week = db.relationship('WeeklyInventory', backref=db.backref('cart_items', lazy=True))

class Order(db.Model):
    """Model for customer orders."""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID for the order
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='completed')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class OrderItem(db.Model):
    """Model for order items."""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    order = db.relationship('Order', backref=db.backref('items', lazy=True))

class OrderItemWeek(db.Model):
    """Model for order item week selections."""
    __tablename__ = 'order_item_weeks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    week_id = db.Column(db.String(20), db.ForeignKey('weekly_inventory.week_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    order_item = db.relationship('OrderItem', backref=db.backref('week_selections', lazy=True))
    week = db.relationship('WeeklyInventory', backref=db.backref('order_items', lazy=True))
