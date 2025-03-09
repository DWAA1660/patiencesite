from flask import render_template
from patient_eggs.main import bp
from patient_eggs.shop.products import products

@bp.route('/')
def index():
    featured_products = list(products.values())[:3]
    return render_template('index.html', featured_products=featured_products)
