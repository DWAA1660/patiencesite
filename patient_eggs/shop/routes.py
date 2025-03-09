from flask import render_template, current_app, redirect, url_for
import stripe
from patient_eggs.shop import bp
from patient_eggs.shop.products import products

@bp.route('/')
def index():
    return render_template('shop/index.html', products=products)

@bp.route('/product/<product_id>')
def product(product_id):
    if product_id not in products:
        return redirect(url_for('shop.index'))
    return render_template('shop/product.html', product=products[product_id])

@bp.route('/checkout/<product_id>')
def checkout(product_id):
    if product_id not in products:
        return redirect(url_for('shop.index'))
    
    product = products[product_id]
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product['name'],
                    'description': product['description'],
                },
                'unit_amount': int(product['price'] * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('shop.success', _external=True),
        cancel_url=url_for('shop.index', _external=True),
    )
    
    return redirect(session.url)

@bp.route('/success')
def success():
    return render_template('shop/success.html')
