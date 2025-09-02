from flask import render_template, current_app, redirect, url_for, request, jsonify, session, flash
import uuid
from datetime import datetime

from patient_eggs.shop import bp
from patient_eggs.shop.products import products
from patient_eggs.shop.models import inventory_manager
from patient_eggs.shop.cart import Cart

@bp.route('/')
def index():
    return render_template('shop/index.html', products=products)

@bp.route('/product/<product_id>')
def product(product_id):
    if product_id not in products:
        return redirect(url_for('shop.index'))
    product = products[product_id]
    available_weeks = None
    if product.get('requires_weekly_selection', False):
        weeks = inventory_manager.get_available_weeks()
        inventory = inventory_manager.get_inventory()
        
        # Process each week to include availability information
        for week in weeks:
            week_id = week['id']
            if week_id in inventory:
                week['total'] = inventory[week_id]['total']
                week['available'] = inventory[week_id]['available']
                week['reserved'] = inventory[week_id]['reserved']
                
                # Calculate status for each week
                if week['available'] == 0:
                    week['status'] = 'sold_out'
                    week['status_text'] = 'Sold Out'
                    week['status_color'] = '#b71c1c'  # Red
                elif week['available'] <= 10:
                    week['status'] = 'low_stock'
                    week['status_text'] = 'Low Stock'
                    week['status_color'] = '#f57f17'  # Orange
                else:
                    week['status'] = 'available'
                    week['status_text'] = 'Available'
                    week['status_color'] = '#2e7d32'  # Green
                
        available_weeks = weeks
    
    # Get cart count for display
    cart_count = Cart.get_cart_count()
    
    return render_template('shop/product.html', product=product, available_weeks=available_weeks, cart_count=cart_count)

@bp.route('/cart-preview')
def cart_preview():
    """Render a compact cart preview for the navbar dropdown."""
    try:
        cart_data = Cart.get_cart()
        cart_total = Cart.get_cart_total()
        # week labels for display
        available_weeks = inventory_manager.get_available_weeks()
        week_labels = {week['id']: week['label'] for week in available_weeks}
        return render_template('shop/_cart_preview.html',
                               cart=cart_data,
                               cart_total=cart_total,
                               week_labels=week_labels)
    except Exception as e:
        current_app.logger.error(f"Error rendering cart preview: {str(e)}")
        # Render empty preview to avoid breaking navbar
        return render_template('shop/_cart_preview.html',
                               cart={'items': []},
                               cart_total=0,
                               week_labels={})

@bp.route('/check-availability', methods=['POST'])
def check_week_availability():
    """API endpoint to check availability for a specific week and quantity."""
    data = request.json
    week_id = data.get('week_id')
    quantity = int(data.get('quantity', 0))
    
    if not week_id or quantity <= 0:
        return jsonify({'available': False, 'message': 'Invalid request'})
    
    available = inventory_manager.check_availability(week_id, quantity)
    
    if available:
        return jsonify({
            'available': True, 
            'message': f'{quantity} eggs are available for the selected week'
        })
    else:
        return jsonify({
            'available': False, 
            'message': f'Not enough eggs available for the selected week'
        })

@bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Add a product to the shopping cart."""
    try:
        data = request.form
        product_id = data.get('product_id')
        
        current_app.logger.info(f"Adding to cart: {product_id}")
        current_app.logger.info(f"Form data: {data}")
        
        if product_id not in products:
            flash('Product not found', 'error')
            return redirect(url_for('shop.index'))
        
        product = products[product_id]
        unit = product.get('unit', 'egg')
        
        # Support two flows: weekly selection vs simple quantity
        week_selections = {}
        total_eggs = 0
        
        if product.get('requires_weekly_selection', False):
            # Weekly: parse dynamic week inputs (e.g., 2025-12 => qty)
            for key, value in request.form.items():
                if key.startswith('20') and '-' in key and value and int(value) > 0:
                    week_id = key
                    quantity = int(value)
                    current_app.logger.info(f"Processing week: {week_id}, quantity: {quantity}")
                    # Validate inventory for each week
                    if not inventory_manager.check_availability(week_id, quantity):
                        current_app.logger.error(f"Insufficient inventory for week {week_id}")
                        flash('Sorry, one of your selected weeks no longer has enough inventory available.', 'error')
                        return redirect(url_for('shop.product', product_id=product_id))
                    week_selections[week_id] = quantity
                    total_eggs += quantity
            current_app.logger.info(f"Week selections: {week_selections}")
            if not week_selections:
                flash('Please select at least one delivery week.', 'error')
                return redirect(url_for('shop.product', product_id=product_id))
        else:
            # Simple product: use a single quantity from form
            qty_str = request.form.get('quantity', '0')
            try:
                qty = int(qty_str)
            except ValueError:
                qty = 0
            if qty <= 0:
                flash(f'Please enter a valid quantity.', 'error')
                return redirect(url_for('shop.product', product_id=product_id))
            # Use a synthetic key so Cart/DB schema remains the same
            week_selections = { f"{product_id}": qty }
            total_eggs = qty
        
        # Check minimum and maximum order quantities
        min_quantity = product.get('min_quantity', 0)
        max_quantity = product.get('max_quantity', float('inf'))
        
        if total_eggs < min_quantity:
            flash(f'Minimum order is {min_quantity} {unit}{"s" if int(min_quantity) != 1 else ""}.', 'error')
            return redirect(url_for('shop.product', product_id=product_id))
        
        if total_eggs > max_quantity:
            flash(f'Maximum order is {max_quantity} {unit}{"s" if int(max_quantity) != 1 else ""}.', 'error')
            return redirect(url_for('shop.product', product_id=product_id))
        
        # Add to cart
        cart = Cart.add_item(
            product_id=product_id,
            product_name=product['name'],
            price=product['price'],
            week_selections=week_selections,
            product_image=product.get('image')
        )
        
        current_app.logger.info(f"Cart after adding item: {cart}")
        
        flash('Product added to cart successfully!', 'success')
        return redirect(url_for('shop.cart'))
    except Exception as e:
        current_app.logger.error(f"Error adding to cart: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('shop.product', product_id=product_id))

@bp.route('/cart')
def cart():
    """View the shopping cart."""
    try:
        cart_data = Cart.get_cart()
        current_app.logger.info(f"Cart data: {cart_data}")
        
        cart_count = 0
        cart_total = 0
        
        if 'items' in cart_data and cart_data['items']:
            cart_count = len(cart_data['items'])
            cart_total = Cart.get_cart_total()
            current_app.logger.info(f"Cart count: {cart_count}, Cart total: {cart_total}")
        
        # Get week labels for display
        available_weeks = inventory_manager.get_available_weeks()
        week_labels = {}
        for week in available_weeks:
            week_labels[week['id']] = week['label']
        
        return render_template('shop/cart.html', 
                              cart=cart_data, 
                              cart_count=cart_count, 
                              cart_total=cart_total,
                              week_labels=week_labels,
                              products=products)
    except Exception as e:
        current_app.logger.error(f"Error viewing cart: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('shop.index'))

@bp.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    """Update a cart item."""
    data = request.json
    item_id = data.get('item_id')
    week_selections = data.get('week_selections', {})
    
    if not item_id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    # Convert string keys to proper format if needed
    week_selections = {str(k): int(v) for k, v in week_selections.items() if int(v) > 0}
    
    # Update cart
    updated_cart = Cart.update_item(item_id, week_selections)
    
    if updated_cart:
        return jsonify({
            'success': True, 
            'message': 'Cart updated successfully',
            'cart_count': Cart.get_cart_count(),
            'cart_total': Cart.get_cart_total()
        })
    else:
        return jsonify({'success': False, 'message': 'Item not found in cart'})

@bp.route('/remove-from-cart/<item_id>', methods=['POST'])
def remove_from_cart(item_id):
    """Remove an item from the cart."""
    Cart.remove_item(item_id)
    flash('Item removed from cart', 'success')
    return redirect(url_for('shop.cart'))

@bp.route('/clear-cart', methods=['POST'])
def clear_cart():
    """Clear all items from the cart."""
    Cart.clear_cart()
    flash('Cart cleared', 'success')
    return redirect(url_for('shop.cart'))

@bp.route('/checkout', methods=['GET'])
def checkout():
    """Checkout page for the cart."""
    cart_data = Cart.get_cart()
    
    if not cart_data['items']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('shop.index'))
    
    cart_total = Cart.get_cart_total()
    
    # Get week labels for display
    available_weeks = inventory_manager.get_available_weeks()
    week_labels = {}
    for week in available_weeks:
        week_labels[week['id']] = week['label']
    
    return render_template('shop/checkout.html', 
                          cart=cart_data, 
                          cart_total=cart_total,
                          week_labels=week_labels)

@bp.route('/process-checkout', methods=['POST'])
def process_checkout():
    """Process the checkout."""
    try:
        cart_data = Cart.get_cart()
        
        if not cart_data.get('items'):
            flash('Your cart is empty.', 'error')
            return redirect(url_for('shop.index'))
        
        # Collect form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate form data
        if not all([name, email, phone, address]):
            flash('Please fill out all required fields.', 'error')
            return redirect(url_for('shop.checkout'))
        
        # Check inventory availability again
        for item in cart_data.get('items', []):
            week_selections = item.get('week_selections', {})
            
            for week_id, quantity in week_selections.items():
                if not inventory_manager.check_availability(week_id, quantity):
                    flash('Sorry, one of your selected weeks no longer has enough inventory available.', 'error')
                    return redirect(url_for('shop.cart'))
        
        # Reserve inventory
        for item in cart_data.get('items', []):
            week_selections = item.get('week_selections', {})
            
            success, message = inventory_manager.distribute_eggs(week_selections)
            if not success:
                flash(f'Error reserving inventory: {message}', 'error')
                return redirect(url_for('shop.cart'))
        
        # Generate order ID
        order_id = str(uuid.uuid4())
        cart_total = Cart.get_cart_total()
        
        # Create order in database
        from patient_eggs.shop.database import db, Order, OrderItem, OrderItemWeek
        
        # Create main order record
        order = Order(
            order_id=order_id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=address,
            total_amount=cart_total,
            status='completed'
        )
        db.session.add(order)
        db.session.flush()  # Get ID without committing
        
        # Add order items
        for item in cart_data.get('items', []):
            # Create order item
            order_item = OrderItem(
                order_id=order_id,
                product_id=item.get('product_id'),
                product_name=item.get('product_name'),
                price_per_unit=item.get('price_per_unit'),
                total_quantity=item.get('total_quantity'),
                total_price=item.get('total_price')
            )
            db.session.add(order_item)
            db.session.flush()  # Get ID without committing
            
            # Add week selections for this item
            for week_id, quantity in item.get('week_selections', {}).items():
                order_item_week = OrderItemWeek(
                    order_item_id=order_item.id,
                    week_id=week_id,
                    quantity=quantity
                )
                db.session.add(order_item_week)
        
        # Commit all changes
        db.session.commit()
        
        # Store order information in session for display
        order_data = {
            'order_id': order_id,
            'order_date': datetime.now().isoformat(),
            'customer': {
                'name': name,
                'email': email,
                'phone': phone,
                'address': address
            },
            'items': cart_data.get('items', []),
            'total': cart_total
        }
        
        # Store order in session temporarily
        session['order'] = order_data
        
        # Clear the cart after successful checkout
        Cart.clear_cart()
        
        # Log the successful order
        current_app.logger.info(f"Order placed successfully: {order_id}")
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('shop.success'))
    
    except Exception as e:
        current_app.logger.error(f"Error processing checkout: {str(e)}")
        flash(f'An error occurred during checkout: {str(e)}', 'error')
        return redirect(url_for('shop.checkout'))

@bp.route('/success')
def success():
    """Order success page."""
    # Get order data from session
    order = session.get('order')
    
    # Clear order data from the session after displaying it
    if 'order' in session:
        session.pop('order')
    
    return render_template('shop/success.html', order=order)

@bp.route('/admin/inventory')
def view_inventory():
    """Admin route to view current inventory status."""
    inventory = inventory_manager.get_inventory()
    return render_template('shop/inventory.html', inventory=inventory)

@bp.route('/admin/orders')
def view_orders():
    """Admin route to view all orders."""
    from patient_eggs.shop.database import Order
    
    # Get all orders, newest first
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('shop/orders.html', orders=orders)
