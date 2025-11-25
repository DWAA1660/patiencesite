from datetime import datetime, timedelta
from patient_eggs import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product_type = db.Column(db.String(20), nullable=False) # 'adult', 'egg', 'merch'
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    
    # Relationships
    inventory_adult = db.relationship('InventoryAdult', backref='product', uselist=False, lazy=True)
    inventory_eggs = db.relationship('InventoryEggWeekly', backref='product', lazy=True)

class InventoryAdult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)

class InventoryEggWeekly(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    week_start_date = db.Column(db.Date, nullable=False)
    quantity_available = db.Column(db.Integer, default=0)
    quantity_sold = db.Column(db.Integer, default=0)

    @staticmethod
    def generate_weeks(product_id, start_date=None, weeks=52, default_qty=0):
        if start_date is None:
            start_date = datetime.now().date()
        
        generated = []
        for i in range(weeks):
            week_date = start_date + timedelta(weeks=i)
            # Align to Monday if needed, but assuming start_date is correct for now
            inv = InventoryEggWeekly(
                product_id=product_id,
                week_start_date=week_date,
                quantity_available=default_qty
            )
            generated.append(inv)
        return generated

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for guest checkout if needed
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')
    payment_status = db.Column(db.String(20), default='Pending') # 'Deposit Paid', 'Full Paid'
    total_price = db.Column(db.Float, nullable=False)
    stripe_charge_id = db.Column(db.String(100))
    shipping_info = db.Column(db.Text) # JSON string for simplicity
    
    # Link to items? For now simplistic
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    options = db.Column(db.Text) # JSON for specific options like week, gender, etc.
