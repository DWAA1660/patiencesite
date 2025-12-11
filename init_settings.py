from patient_eggs import create_app, db
from patient_eggs.models import SiteSetting

app = create_app()

with app.app_context():
    # Check if table exists, if not create it
    inspector = db.inspect(db.engine)
    if 'site_setting' not in inspector.get_table_names():
        print("Creating site_setting table...")
        db.create_all()
        print("Done.")
    else:
        print("site_setting table already exists.")

    # Seed default settings if they don't exist
    defaults = {
        'site_background': 'default_bg.jpg', 
        'home_hero_bg': 'https://via.placeholder.com/1200x400',
        'chicks_hero_bg': 'https://via.placeholder.com/1200x300?text=Chicks',
        'adult_hero_bg': 'https://via.placeholder.com/1200x300?text=Adult+Birds',
        'eggs_hero_bg': 'https://via.placeholder.com/1200x300?text=Hatching+Eggs',
        'about_hero_bg': 'https://via.placeholder.com/1200x300?text=About+Us',
        'contact_hero_bg': 'https://via.placeholder.com/1200x300?text=Contact+Us',
        'site_logo': '' # Empty default, will fall back to text
    }

    for key, val in defaults.items():
        if not SiteSetting.query.filter_by(key=key).first():
            print(f"Seeding {key}...")
            setting = SiteSetting(key=key, value=val)
            db.session.add(setting)
    
    db.session.commit()
    print("Seeding complete.")
