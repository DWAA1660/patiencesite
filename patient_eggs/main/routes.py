from flask import Blueprint, render_template, request
from flask_login import current_user
from patient_eggs.models import Product, GalleryImage, BlogPost, db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    # Logic for featured inventory (3x3 grid) can go here
    featured_products = Product.query.order_by(Product.display_order).limit(9).all()
    gallery_images = GalleryImage.query.order_by(GalleryImage.display_order).all()
    return render_template('home.html', products=featured_products, gallery_images=gallery_images)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

@main.route('/blog')
def blog_index():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(is_published=True)\
        .order_by(BlogPost.created_at.desc())\
        .paginate(page=page, per_page=5)
    return render_template('blog/index.html', posts=posts)

@main.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    if post.is_published or (current_user.is_authenticated and current_user.is_admin):
        # Increment views
        post.views += 1
        db.session.commit()
        return render_template('blog/post.html', post=post)
    else:
        # If not published and not admin
        from flask import abort
        abort(404)

