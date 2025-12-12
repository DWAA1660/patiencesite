from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from patient_eggs.models import Product, InventoryEggWeekly, Order, GalleryImage, BlogPost, InventoryAdult, SiteSetting, ProductImage, db
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime

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

# --- Product Gallery Management ---
@admin.route('/product/<int:product_id>/gallery/add', methods=['POST'])
def add_product_image(product_id):
    product = Product.query.get_or_404(product_id)
    image_file = request.form.get('image_file')
    
    if image_file:
        # Get max display order
        max_order = db.session.query(db.func.max(ProductImage.display_order))\
            .filter_by(product_id=product_id).scalar() or 0
            
        img = ProductImage(
            product_id=product.id,
            image_file=image_file,
            display_order=max_order + 1
        )
        db.session.add(img)
        db.session.commit()
        flash('Image added to product gallery.')
    
    return redirect(url_for('admin.edit_product', product_id=product_id))

@admin.route('/product/gallery/delete/<int:image_id>', methods=['POST'])
def delete_product_image(image_id):
    img = ProductImage.query.get_or_404(image_id)
    product_id = img.product_id
    db.session.delete(img)
    db.session.commit()
    flash('Image removed from gallery.')
    return redirect(url_for('admin.edit_product', product_id=product_id))

@admin.route('/product/<int:product_id>/gallery/reorder', methods=['POST'])
def reorder_product_images(product_id):
    order_data = request.json.get('order', [])
    if not order_data:
        return {'error': 'No order data'}, 400
        
    for index, image_id in enumerate(order_data):
        img = ProductImage.query.get(image_id)
        if img and img.product_id == product_id:
            img.display_order = index
            
    db.session.commit()
    return {'success': True}

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

# --- Blog Management ---
@admin.route('/blogs')
def manage_blogs():
    blogs = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/manage_blogs.html', blogs=blogs)

@admin.route('/blogs/add', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        is_published = 'is_published' in request.form
        
        if not slug:
            slug = title.lower().replace(' ', '-')
            
        # Handle duplicate slug
        if BlogPost.query.filter_by(slug=slug).first():
            flash('Slug already exists. Please choose a different one.')
            return render_template('admin/edit_blog.html', legend='Add Blog Post', title=title, content=content, slug=slug, tinymce_api_key=current_app.config.get('TINYMCE_API_KEY'))

        blog = BlogPost(title=title, slug=slug, content=content, is_published=is_published)
        
        # Handle Cover Image (Text selection or File upload)
        # Priority: File Upload > Text Selection > Default (if new)
        if 'cover_image_file' in request.files and request.files['cover_image_file'].filename:
            file = request.files['cover_image_file']
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            # Save to main img folder
            save_path = os.path.join(current_app.root_path, 'static', 'img')
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            file.save(os.path.join(save_path, filename))
            blog.cover_image = filename
        elif request.form.get('cover_image'):
            blog.cover_image = request.form.get('cover_image')

        db.session.add(blog)
        db.session.commit()
        flash('Blog post created!')
        return redirect(url_for('admin.manage_blogs'))
        
    return render_template('admin/edit_blog.html', legend='Add Blog Post', tinymce_api_key=current_app.config.get('TINYMCE_API_KEY'))

@admin.route('/blogs/edit/<int:blog_id>', methods=['GET', 'POST'])
def edit_blog(blog_id):
    blog = BlogPost.query.get_or_404(blog_id)
    if request.method == 'POST':
        blog.title = request.form.get('title')
        new_slug = request.form.get('slug')
        if new_slug != blog.slug:
             if BlogPost.query.filter_by(slug=new_slug).first():
                 flash('Slug already exists.')
                 return render_template('admin/edit_blog.html', legend='Edit Blog Post', blog=blog, tinymce_api_key=current_app.config.get('TINYMCE_API_KEY'))
        blog.slug = new_slug
        blog.content = request.form.get('content')
        blog.is_published = 'is_published' in request.form
        
        # Handle Cover Image
        if 'cover_image_file' in request.files and request.files['cover_image_file'].filename:
            file = request.files['cover_image_file']
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            # Save to main img folder
            save_path = os.path.join(current_app.root_path, 'static', 'img')
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            file.save(os.path.join(save_path, filename))
            blog.cover_image = filename
        elif request.form.get('cover_image'):
             blog.cover_image = request.form.get('cover_image')
        
        db.session.commit()
        flash('Blog post updated!')
        return redirect(url_for('admin.manage_blogs'))
        
    return render_template('admin/edit_blog.html', legend='Edit Blog Post', blog=blog, tinymce_api_key=current_app.config.get('TINYMCE_API_KEY'))

@admin.route('/blogs/delete/<int:blog_id>', methods=['POST'])
def delete_blog(blog_id):
    blog = BlogPost.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    flash('Blog post deleted.')
    return redirect(url_for('admin.manage_blogs'))

@admin.route('/blogs/upload_image', methods=['POST'])
def upload_blog_image():
    if 'file' not in request.files:
        return {'error': 'No file uploaded'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No filename'}, 400
        
    if file:
        filename = secure_filename(file.filename)
        # Add timestamp to make filename unique
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        from flask import current_app
        # Use main img folder as requested
        save_path = os.path.join(current_app.root_path, 'static', 'img')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        file.save(os.path.join(save_path, filename))
        
        # Return URL
        url = url_for('static', filename=f'img/{filename}')
        return {'location': url} # TinyMCE expects 'location'

# --- Media Manager ---
@admin.route('/media')
def media_manager():
    return render_template('admin/media_manager.html')

@admin.route('/media/upload', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('admin.media_manager'))
    
    files = request.files.getlist('file')
    upload_dir = os.path.join(current_app.root_path, 'static', 'img')
    
    saved_count = 0
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Avoid overwriting
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(upload_dir, filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            
            file.save(os.path.join(upload_dir, filename))
            saved_count += 1
            
    flash(f'{saved_count} images uploaded successfully.')
    return redirect(url_for('admin.media_manager'))

@admin.route('/media/rename', methods=['POST'])
def rename_media():
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    
    if not old_name or not new_name:
        flash('Invalid filenames.')
        return redirect(url_for('admin.media_manager'))
        
    # Security check - ensure we stay in static/img
    if '..' in old_name or '..' in new_name or '/' in old_name or '/' in new_name:
        flash('Invalid filename security.')
        return redirect(url_for('admin.media_manager'))
        
    img_dir = os.path.join(current_app.root_path, 'static', 'img')
    old_path = os.path.join(img_dir, old_name)
    
    # Ensure extension is preserved or added
    _, old_ext = os.path.splitext(old_name)
    _, new_ext = os.path.splitext(new_name)
    if not new_ext:
        new_name += old_ext
        
    new_path = os.path.join(img_dir, secure_filename(new_name))
    
    if not os.path.exists(old_path):
        flash('Original file not found.')
    elif os.path.exists(new_path):
        flash('A file with that name already exists.')
    else:
        try:
            os.rename(old_path, new_path)
            # TODO: Update DB references? That's risky/complex. 
            # For now, just warn user or let them update manually.
            # Ideally we'd update Product, GalleryImage, etc.
            _update_db_references(old_name, os.path.basename(new_path))
            flash(f'Renamed {old_name} to {os.path.basename(new_path)} and updated references.')
        except Exception as e:
            flash(f'Error renaming file: {str(e)}')
            
    return redirect(url_for('admin.media_manager'))

@admin.route('/media/delete', methods=['POST'])
def delete_media():
    filename = request.form.get('filename')
    if not filename:
        flash('No filename provided.')
        return redirect(url_for('admin.media_manager'))
        
    if '..' in filename or '/' in filename:
        flash('Invalid filename.')
        return redirect(url_for('admin.media_manager'))
        
    img_dir = os.path.join(current_app.root_path, 'static', 'img')
    file_path = os.path.join(img_dir, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            flash(f'Deleted {filename}.')
        except Exception as e:
            flash(f'Error deleting file: {str(e)}')
    else:
        flash('File not found.')
        
    return redirect(url_for('admin.media_manager'))

@admin.route('/site-media', methods=['GET', 'POST'])
def manage_site_media():
    if request.method == 'POST':
        # Handle New Setting Creation
        new_key = request.form.get('new_setting_key')
        if new_key:
            # Clean key: lowercase, underscores only
            clean_key = new_key.strip().lower().replace(' ', '_')
            if clean_key and not SiteSetting.query.filter_by(key=clean_key).first():
                new_value = request.form.get('new_setting_value', '')
                new_desc = request.form.get('new_setting_description', '')
                
                # Create manually to include description
                setting = SiteSetting(key=clean_key, value=new_value, description=new_desc)
                db.session.add(setting)
                db.session.commit()
                
                flash(f'New setting "{clean_key}" added.')
            elif SiteSetting.query.filter_by(key=clean_key).first():
                flash(f'Setting "{clean_key}" already exists.', 'warning')

        # Handle Updates
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                SiteSetting.set_value(setting_key, value)
            elif key.startswith('description_'):
                setting_key = key.replace('description_', '')
                setting = SiteSetting.query.filter_by(key=setting_key).first()
                if setting:
                    setting.description = value
                    # set_value commits, but here we just modify object attached to session
                    # We need to make sure we commit eventually. 
                    # set_value commits immediately, so if we update value then description, 
                    # we might need an explicit commit for description if set_value wasn't called for this key (unlikely if form submits both).
                    # But SiteSetting.set_value commits inside itself.
                    # Let's just do a final commit at the end to be sure for descriptions.
        
        db.session.commit()
        
        if not new_key: # Only show "updated" if we weren't just creating one (though we do both)
             flash('Site settings updated successfully.')
             
        return redirect(url_for('admin.manage_site_media'))
    
    all_settings = SiteSetting.query.all()
    
    # Organize settings into groups for easier editing
    groups = []
    processed_ids = set()

    def find_setting(key):
        for s in all_settings:
            if s.key == key:
                return s
        return None

    # Define known hero sections
    hero_sections = [
        {'title': 'Home Page Hero', 'prefix': 'home_hero'},
        {'title': 'Chicks Page Hero', 'prefix': 'chicks_hero'},
        {'title': 'Adult Birds Page Hero', 'prefix': 'adult_hero'},
        {'title': 'Hatching Eggs Page Hero', 'prefix': 'eggs_hero'},
        {'title': 'About Page Hero', 'prefix': 'about_hero'},
        {'title': 'Contact Page Hero', 'prefix': 'contact_hero'},
    ]

    for section in hero_sections:
        bg_key = f"{section['prefix']}_bg"
        height_key = f"{section['prefix']}_height"
        
        bg_setting = find_setting(bg_key)
        height_setting = find_setting(height_key)
        
        if bg_setting or height_setting:
            groups.append({
                'title': section['title'],
                'bg': bg_setting,
                'height': height_setting
            })
            if bg_setting: processed_ids.add(bg_setting.id)
            if height_setting: processed_ids.add(height_setting.id)

    # Collect any settings not in the groups
    misc_settings = [s for s in all_settings if s.id not in processed_ids]

    return render_template('admin/site_media.html', groups=groups, misc_settings=misc_settings)

@admin.route('/api/media-list')
def api_media_list():
    img_dir = os.path.join(current_app.root_path, 'static', 'img')
    images = []
    
    # 1. Get usage data
    usage = _get_image_usage()
    
    # 2. List files
    if os.path.exists(img_dir):
        for f in os.listdir(img_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                images.append({
                    'name': f,
                    'url': url_for('static', filename=f'img/{f}'),
                    'usage': usage.get(f, [])
                })
                
    return {'images': images}

def _get_image_usage():
    """Scans DB to find where images are used."""
    usage = {}
    
    # Products
    products = Product.query.all()
    for p in products:
        if p.image_file:
            if p.image_file not in usage: usage[p.image_file] = []
            usage[p.image_file].append(f'Product: {p.name}')
            
    # Gallery
    gallery = GalleryImage.query.all()
    for g in gallery:
        if g.image_file:
            if g.image_file not in usage: usage[g.image_file] = []
            usage[g.image_file].append(f'Gallery: {g.caption or "Image"}')
            
    # Blog Cover
    blogs = BlogPost.query.all()
    for b in blogs:
        if b.cover_image:
            # Blog images might be in subfolder 'blog/', check how we stored them. 
            # If they are just filenames, we might need to handle paths.
            # Assuming main img folder for now based on user request "one directory".
            # But currently blog images are saved to static/img/blog.
            # We should probably check if the filename matches.
            name = b.cover_image
            if name not in usage: usage[name] = []
            usage[name].append(f'Blog Cover: {b.title}')
            
        # Blog Content (basic string search)
        # This is expensive for many blogs but fine for small scale
        if b.content:
            for img_name in usage.keys():
                # Check if image name appears in content
                if img_name in b.content:
                     if f'Blog Post: {b.title}' not in usage[img_name]:
                         usage[img_name].append(f'Blog Content: {b.title}')
                         
    return usage

def _update_db_references(old_name, new_name):
    """Updates DB references when a file is renamed."""
    # Products
    products = Product.query.filter_by(image_file=old_name).all()
    for p in products:
        p.image_file = new_name
        
    # Gallery
    gallery = GalleryImage.query.filter_by(image_file=old_name).all()
    for g in gallery:
        g.image_file = new_name
        
    # Blog Cover
    blogs = BlogPost.query.filter_by(cover_image=old_name).all()
    for b in blogs:
        b.cover_image = new_name
        
    db.session.commit()


