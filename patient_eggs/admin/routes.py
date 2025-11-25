from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from patient_eggs.models import Product, InventoryEggWeekly, Order, GalleryImage, db
import json

admin = Blueprint('admin', __name__)

@admin.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You must be an admin to access this page.')
        return redirect(url_for('main.home'))

@admin.route('/dashboard')
def dashboard():
    orders = Order.query.all()
    return render_template('admin/dashboard.html', orders=orders)

@admin.route('/order/<int:order_id>')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    shipping_info = {}
    if order.shipping_info:
        try:
            shipping_info = json.loads(order.shipping_info)
        except:
            shipping_info = {'raw': order.shipping_info}
    
    return render_template('admin/view_order.html', order=order, shipping_info=shipping_info)

@admin.route('/calendar')
def calendar():
    orders = Order.query.all()
    products = Product.query.order_by(Product.name).all()
    events = []
    
    for order in orders:
        customer_name = "Guest"
        if order.customer:
            customer_name = order.customer.username
        elif order.shipping_info:
            try:
                info = json.loads(order.shipping_info)
                customer_name = info.get('name', 'Guest')
            except:
                pass

        for item in order.items:
            start_date = None
            title = f"#{order.id} {customer_name} - {item.product.name}"
            color = '#3788d8' # Default blue
            
            # Try to find scheduled week
            if item.options:
                try:
                    opts = json.loads(item.options)
                    if 'week' in opts:
                        start_date = opts['week']
                        color = '#28a745' # Green for scheduled eggs
                        title = f"SHIP: {title}"
                except:
                    pass
            
            # If no specific week, use order date (Ship ASAP)
            if not start_date:
                start_date = order.date_ordered.strftime('%Y-%m-%d')
                color = '#dc3545' # Red for immediate/adult birds
                title = f"NEW: {title}"

            events.append({
                'title': title,
                'start': start_date,
                'url': url_for('admin.view_order', order_id=order.id),
                'color': color,
                'allDay': True,
                'extendedProps': {
                    'productId': item.product_id
                }
            })
            
    return render_template('admin/calendar.html', events=events, products=products)

@admin.route('/inventory/eggs')
def egg_inventory():
    products = Product.query.filter_by(product_type='egg').all()
    inventory = {}
    for p in products:
        inventory[p.id] = InventoryEggWeekly.query.filter_by(product_id=p.id).order_by(InventoryEggWeekly.week_start_date).all()
    return render_template('admin/egg_inventory.html', products=products, inventory=inventory)

@admin.route('/inventory/eggs/update', methods=['POST'])
def update_egg_inventory():
    # Logic to update multiple cells
    # Form data expected: id=qty
    for key, value in request.form.items():
        if key.startswith('inv_'):
            inv_id = int(key.split('_')[1])
            inv = InventoryEggWeekly.query.get(inv_id)
            if inv:
                inv.quantity_available = int(value)
    db.session.commit()
    flash('Inventory updated')
    return redirect(url_for('admin.egg_inventory'))

@admin.route('/products')
def manage_products():
    products = Product.query.order_by(Product.display_order).all()
    return render_template('admin/manage_products.html', products=products)

@admin.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        product_type = request.form['product_type']
        image_file = request.form.get('image_file', 'default.jpg')
        display_order = int(request.form.get('display_order', 0))
        
        product = Product(
            name=name,
            description=description,
            price=price,
            product_type=product_type,
            image_file=image_file,
            display_order=display_order
        )
        db.session.add(product)
        db.session.commit()
        
        # If egg type, initialize inventory weeks? 
        if product_type == 'egg':
            weeks = InventoryEggWeekly.generate_weeks(product.id, default_qty=0)
            db.session.add_all(weeks)
            db.session.commit()
        elif product_type == 'adult':
            inv = InventoryAdult(product_id=product.id, quantity=0)
            db.session.add(inv)
            db.session.commit()
            
        flash('Product added successfully!')
        return redirect(url_for('admin.manage_products'))
        
    return render_template('admin/edit_product.html', legend='Add Product')

@admin.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.product_type = request.form['product_type']
        product.image_file = request.form.get('image_file', product.image_file)
        product.display_order = int(request.form.get('display_order', 0))
        
        db.session.commit()
        flash('Product updated successfully!')
        return redirect(url_for('admin.manage_products'))
    
    return render_template('admin/edit_product.html', legend='Edit Product', product=product)

@admin.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Basic deletion, might need to handle foreign keys or cascade delete in models
    # Manually delete related inventory for now to be safe
    if product.inventory_adult:
        db.session.delete(product.inventory_adult)
    
    InventoryEggWeekly.query.filter_by(product_id=product.id).delete()
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.')
    return redirect(url_for('admin.manage_products'))

# --- Gallery Management ---
@admin.route('/gallery')
def manage_gallery():
    images = GalleryImage.query.order_by(GalleryImage.display_order).all()
    return render_template('admin/gallery.html', images=images)

@admin.route('/gallery/add', methods=['POST'])
def add_gallery_image():
    image_file = request.form.get('image_file')
    caption = request.form.get('caption')
    display_order = int(request.form.get('display_order', 0))
    
    if image_file:
        img = GalleryImage(image_file=image_file, caption=caption, display_order=display_order)
        db.session.add(img)
        db.session.commit()
        flash('Image added to gallery.')
    
    return redirect(url_for('admin.manage_gallery'))

@admin.route('/gallery/delete/<int:image_id>', methods=['POST'])
def delete_gallery_image(image_id):
    img = GalleryImage.query.get_or_404(image_id)
    db.session.delete(img)
    db.session.commit()
    flash('Image removed.')
    return redirect(url_for('admin.manage_gallery'))

@admin.route('/api/images')
def list_images():
    # List files in static/img
    import os
    from flask import current_app
    img_folder = os.path.join(current_app.root_path, 'static', 'img')
    images = []
    if os.path.exists(img_folder):
        for f in os.listdir(img_folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                images.append(f)
    return {'images': images}

