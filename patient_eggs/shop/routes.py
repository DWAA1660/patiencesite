from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import current_user
from patient_eggs.models import Product, InventoryEggWeekly, Order, OrderItem
from patient_eggs import db
import json
import stripe

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

@shop.route('/chicks')
def chicks():
    products = Product.query.filter_by(product_type='chick').all()
    return render_template('chicks.html', products=products)

@shop.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    weeks = []
    if product.product_type == 'egg':
        # Filter weeks where available > sold
        weeks = InventoryEggWeekly.query.filter_by(product_id=product.id)\
            .filter(InventoryEggWeekly.quantity_available > InventoryEggWeekly.quantity_sold)\
            .order_by(InventoryEggWeekly.week_start_date).all()
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

@shop.route('/update_cart_item/<int:item_index>', methods=['POST'])
def update_cart_item(item_index):
    cart = session.get('cart', {})
    if 'items' in cart and 0 <= item_index < len(cart['items']):
        try:
            new_quantity = int(request.form.get('quantity'))
            if new_quantity > 0:
                cart['items'][item_index]['quantity'] = new_quantity
                session.modified = True
                flash('Cart updated.')
            else:
                # If 0 or negative, remove it? Or just flash error? Let's remove if 0.
                cart['items'].pop(item_index)
                session.modified = True
                flash('Item removed from cart.')
        except ValueError:
            flash('Invalid quantity.')
    
    session['cart'] = cart
    return redirect(url_for('shop.cart'))

@shop.route('/remove_from_cart/<int:item_index>')
def remove_from_cart(item_index):
    cart = session.get('cart', {})
    if 'items' in cart and 0 <= item_index < len(cart['items']):
        cart['items'].pop(item_index)
        session.modified = True
        flash('Item removed from cart.')
    
    session['cart'] = cart
    return redirect(url_for('shop.cart'))

@shop.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared.')
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
    cart = session.get('cart', {})
    if not cart.get('items'):
        flash('Your cart is empty.')
        return redirect(url_for('shop.cart'))

    # Calculate totals
    items = []
    total = 0
    deposit_total = 0
    
    for item in cart['items']:
        product = Product.query.get(item['product_id'])
        if product:
            item_total = product.price * item['quantity']
            total += item_total
            
            if product.product_type == 'adult':
                deposit_total += item_total * 0.25
            else:
                deposit_total += item_total
            
            items.append({
                'product': product,
                'quantity': item['quantity'],
                'options': item['options'],
                'total': item_total,
                'price': product.price
            })
    
    if request.method == 'POST':
        token = request.form.get('stripeToken')
        if not token:
            flash('An error occurred with the payment provider.')
            return redirect(url_for('shop.checkout'))
            
        # Capture Shipping Info
        shipping_info = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'zip': request.form.get('zip')
        }
        
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        
        try:
            # Charge the user's card
            # Amount in cents
            amount_to_charge = int(deposit_total * 100)
            
            charge = stripe.Charge.create(
                amount=amount_to_charge,
                currency='usd',
                description=f'Order for {shipping_info["email"]}',
                source=token,
                metadata=shipping_info,
                receipt_email=shipping_info['email']
            )
            
            # Payment successful, create order
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else None,
                total_price=total,
                payment_status='Deposit Paid' if deposit_total < total else 'Full Paid',
                stripe_charge_id=charge.id,
                shipping_info=json.dumps(shipping_info)
            )
            db.session.add(order)
            db.session.commit()
            
            # Add items to order
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    quantity=item['quantity'],
                    price_at_purchase=item['price'],
                    options=json.dumps(item['options'])
                )
                db.session.add(order_item)
                
                # Update Inventory (Simplified)
                # Note: A more robust system would check stock availability again here
                if item['product'].product_type == 'adult':
                    inv = item['product'].inventory_adult
                    if inv:
                        inv.quantity -= item['quantity']
                elif item['product'].product_type == 'egg' and 'week' in item['options']:
                    # Find the specific week inventory
                    # Week option is stored as string "YYYY-MM-DD" or similar from form
                    pass # TODO: Implement specific week inventory decrement

            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash(f'Payment successful! Order #{order.id} created.')
            return redirect(url_for('main.home'))
            
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err  = body.get('error', {})
            flash(f"Payment failed: {err.get('message')}")
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe log the exception
            flash('Something went wrong. You were not charged. Please try again.')
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            flash(f'An error occurred: {str(e)}')
            
    return render_template('checkout.html', key=current_app.config['STRIPE_PUBLIC_KEY'], total=total, deposit_total=deposit_total)
