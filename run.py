from patient_eggs import create_app, db
from patient_eggs.models import User, Product, InventoryAdult, InventoryEggWeekly, GalleryImage, BlogPost, SiteSetting
from sqlalchemy import text

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Check and add is_featured column if missing (Migration aid)
        try:
            with db.engine.connect() as conn:
                # SQLite specific check
                result = conn.execute(text("PRAGMA table_info(product)"))
                columns = [row[1] for row in result]
                if 'is_featured' not in columns:
                    print("Adding is_featured column to product table...")
                    conn.execute(text("ALTER TABLE product ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
                    conn.commit()
                    print("Column added.")
        except Exception as e:
            print(f"Schema check warning: {e}")

        # Create admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin') # Change in production
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        
        # Seed Site Settings
        defaults = {
            'site_background': ('default_bg.jpg', 'Global site background image pattern'), 
            'home_hero_bg': ('https://via.placeholder.com/1200x400', 'Home page main banner background'),
            'chicks_hero_bg': ('https://via.placeholder.com/1200x300?text=Chicks', 'Chicks page header background'),
            'adult_hero_bg': ('https://via.placeholder.com/1200x300?text=Adult+Birds', 'Adult birds page header background'),
            'eggs_hero_bg': ('https://via.placeholder.com/1200x300?text=Hatching+Eggs', 'Hatching eggs page header background'),
            'about_hero_bg': ('https://via.placeholder.com/1200x300?text=About+Us', 'About Us page header background'),
            'contact_hero_bg': ('https://via.placeholder.com/1200x300?text=Contact+Us', 'Contact Us page header background'),
            'site_logo': ('', 'Website logo displayed in the navbar'),
            'logo': ('', 'Central logo on Home page'),
            
            # Hero Heights
            'home_hero_height': ('500px', 'Height of the Home page banner'),
            'chicks_hero_height': ('300px', 'Height of the Chicks page banner'),
            'adult_hero_height': ('300px', 'Height of the Adult Birds page banner'),
            'eggs_hero_height': ('300px', 'Height of the Hatching Eggs page banner'),
            'about_hero_height': ('300px', 'Height of the About Us page banner'),
            'contact_hero_height': ('300px', 'Height of the Contact Us page banner'),
            
            # About Page Images
            'about_our_story_image': ('https://via.placeholder.com/600x400?text=Our+Story', 'Image for Our Story section on About page'),
            'about_our_flocks_image': ('https://via.placeholder.com/600x400?text=Our+Flocks', 'Image for Our Flocks section on About page')
        }

        for key, (val, desc) in defaults.items():
            setting = SiteSetting.query.filter_by(key=key).first()
            if not setting:
                print(f"Seeding {key}...")
                setting = SiteSetting(key=key, value=val, description=desc)
                db.session.add(setting)
            elif not setting.description:
                # Update description if missing for existing keys
                print(f"Updating description for {key}...")
                setting.description = desc
                
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
