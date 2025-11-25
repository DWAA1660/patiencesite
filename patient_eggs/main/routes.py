from flask import Blueprint, render_template
from patient_eggs.models import Product

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    # Logic for featured inventory (3x3 grid) can go here
    featured_products = Product.query.order_by(Product.display_order).limit(9).all()
    return render_template('home.html', products=featured_products)

@main.route('/about')
def about():
    return render_template('about.html')
