from patient_eggs import create_app, db
from patient_eggs.models import User, Product, InventoryAdult, InventoryEggWeekly, GalleryImage, BlogPost, SiteSetting

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin') # Change in production
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        
        # Seed Site Settings
        defaults = {
            'site_background': 'default_bg.jpg', 
            'home_hero_bg': 'https://via.placeholder.com/1200x400',
            'chicks_hero_bg': 'https://via.placeholder.com/1200x300?text=Chicks',
            'adult_hero_bg': 'https://via.placeholder.com/1200x300?text=Adult+Birds',
            'eggs_hero_bg': 'https://via.placeholder.com/1200x300?text=Hatching+Eggs',
            'about_hero_bg': 'https://via.placeholder.com/1200x300?text=About+Us',
            'contact_hero_bg': 'https://via.placeholder.com/1200x300?text=Contact+Us',
            'site_logo': '', # Empty default, will fall back to text
            
            # Hero Heights
            'home_hero_height': '500px',
            'chicks_hero_height': '300px',
            'adult_hero_height': '300px',
            'eggs_hero_height': '300px',
            'about_hero_height': '300px',
            'contact_hero_height': '300px'
        }

        for key, val in defaults.items():
            if not SiteSetting.query.filter_by(key=key).first():
                print(f"Seeding {key}...")
                setting = SiteSetting(key=key, value=val)
                db.session.add(setting)
        db.session.commit()

        # Seed Products
        if not Product.query.first():
            p1 = Product(name='Black Copper Marans', description='Beautiful dark brown eggs.', price=50.00, product_type='adult', image_file='default.jpg')
            p2 = Product(name='Ameraucana', description='Blue eggs.', price=45.00, product_type='adult', image_file='default.jpg')
            p3 = Product(name='Olive Egger Hatching Eggs', description='Olive green eggs.', price=60.00, product_type='egg', image_file='default.jpg')
            
            db.session.add_all([p1, p2, p3])
            db.session.commit()
            
            # Seed Inventory
            inv1 = InventoryAdult(product_id=p1.id, quantity=10)
            inv2 = InventoryAdult(product_id=p2.id, quantity=5)
            db.session.add_all([inv1, inv2])
            
            # Seed Weekly Inventory for Eggs
            weeks = InventoryEggWeekly.generate_weeks(p3.id, default_qty=12)
            db.session.add_all(weeks)
            
            db.session.commit()
            print("Sample data seeded")
    
    app.run(debug=True, host='0.0.0.0', port=3000)
