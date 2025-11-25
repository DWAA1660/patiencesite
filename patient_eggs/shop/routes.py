from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from patient_eggs.models import Product, InventoryEggWeekly
from patient_eggs import db
import json

shop = Blueprint('shop', __name__)

@shop.route('/adult-birds')
def adult_birds():
    products = Product.query.filter_by(product_type='adult').all()
    return render_template('adult_birds.html', products=products)

@shop.route('/hatching-eggs')
def hatching_eggs():
    products = Product.query.filter_by(product_type='egg').all()
    # Assuming we might want to show available weeks here or on detail page
    return render_template('hatching_eggs.html', products=products)

@shop.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    weeks = []
    if product.product_type == 'egg':
        weeks = InventoryEggWeekly.query.filter_by(product_id=product.id).filter(InventoryEggWeekly.quantity_available > 0).all()
    return render_template('product_detail.html', product=product, weeks=weeks)

@shop.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    options = {}
    
    if 'week' in request.form:
        options['week'] = request.form['week']
    if 'gender' in request.form:
        options['gender'] = request.form['gender']
    if 'substitute_date' in request.form:
        options['substitute_date'] = True
    if 'substitute_breed' in request.form:
        options['substitute_breed'] = True

    cart = session.get('cart', {})
    # Simple cart logic: Key by product_id (this prevents multiple configs of same product, ideally key by composite or list)
    # Using list for simplicity
    if 'items' not in cart:
        cart['items'] = []
    
    cart['items'].append({
        'product_id': product_id,
        'quantity': quantity,
        'options': options
    })
    session['cart'] = cart
    flash('Added to cart!')
    return redirect(url_for('shop.cart'))

@shop.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    deposit_total = 0
    
    if 'items' in cart:
        for item in cart['items']:
            product = Product.query.get(item['product_id'])
            item_total = product.price * item['quantity']
            total += item_total
            
            if product.product_type == 'adult':
                deposit_total += item_total * 0.25
            else:
                deposit_total += item_total # Full price for eggs
            
            items.append({
                'product': product,
                'quantity': item['quantity'],
                'options': item['options'],
                'total': item_total
            })
            
    return render_template('cart.html', items=items, total=total, deposit_total=deposit_total)

@shop.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Stripe logic would go here
    return render_template('checkout.html')
