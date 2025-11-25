from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from patient_eggs.models import Product, InventoryEggWeekly, Order, db

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
