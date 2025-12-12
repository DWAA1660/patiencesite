from patient_eggs import create_app
import sys

app = create_app()
with app.app_context():
    print("Searching for admin.reorder_gallery_images...")
    found = False
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'admin.reorder_gallery_images':
            print(f"FOUND: {rule}")
            found = True
            break
    
    if not found:
        print("NOT FOUND. Listing all admin endpoints:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin.'):
                print(f" - {rule.endpoint}: {rule}")
