import os
import sys
import requests
import shutil
import random

# Add the current directory to the path so we can import from patient_eggs
sys.path.append('.')
from patient_eggs.shop.products import products

# Create images directory if it doesn't exist
images_dir = os.path.join('patient_eggs', 'static', 'images')
os.makedirs(images_dir, exist_ok=True)

# Dictionary mapping product IDs to search terms for better image results
search_terms = {
    'fresh-eggs': 'farm fresh eggs',
    'duck-eggs': 'duck eggs',
    'honey': 'raw honey jar',
    'jam': 'homemade berry jam'
}

# Function to download an image from Pixabay
def download_image(search_term, filename):
    # Using Pixabay API which is free and reliable for programmatic access
    # You can get your own API key by signing up at https://pixabay.com/api/docs/
    pixabay_key = ''  # Add your Pixabay API key here if you have one
    
    if not pixabay_key:
        # If no API key, we'll use direct URLs to free stock images
        # These are reliable free images that match our products
        stock_images = {
            'fresh-eggs': [
                'https://cdn.pixabay.com/photo/2016/07/23/15/24/egg-1536990_1280.jpg',
                'https://cdn.pixabay.com/photo/2015/09/17/17/19/egg-944495_1280.jpg',
                'https://cdn.pixabay.com/photo/2016/03/05/19/02/animal-product-1238252_1280.jpg'
            ],
            'duck-eggs': [
                'https://cdn.pixabay.com/photo/2018/03/11/18/34/eggs-3217675_1280.jpg',
                'https://cdn.pixabay.com/photo/2019/06/13/10/06/eggs-4271511_1280.jpg',
                'https://cdn.pixabay.com/photo/2021/01/05/06/40/duck-eggs-5889919_1280.jpg'
            ],
            'honey': [
                'https://images.pexels.com/photos/1638280/pexels-photo-1638280.jpeg',
                'https://images.pexels.com/photos/6412329/pexels-photo-6412329.jpeg',
                'https://images.pexels.com/photos/7474372/pexels-photo-7474372.jpeg'
            ],
            'jam': [
                'https://images.pexels.com/photos/5419336/pexels-photo-5419336.jpeg',
                'https://images.pexels.com/photos/7474372/pexels-photo-7474372.jpeg',
                'https://images.pexels.com/photos/6412329/pexels-photo-6412329.jpeg'
            ]
        }
        
        # Get product ID from filename (remove extension)
        product_id = filename.split('.')[0]
        
        # Use default images if product ID not in our dictionary
        if product_id not in stock_images:
            product_id = 'fresh-eggs'  # Default to fresh eggs
        
        # Select a random image from the options
        image_url = random.choice(stock_images[product_id])
        
        # Download the image
        response = requests.get(image_url, stream=True)
        
        if response.status_code == 200:
            file_path = os.path.join(images_dir, filename)
            with open(file_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            print(f"Downloaded {filename} successfully")
            return True
        else:
            print(f"Failed to download {filename}: {response.status_code}")
            return False
    else:
        # Using Pixabay API with key
        url = f"https://pixabay.com/api/?key={pixabay_key}&q={search_term.replace(' ', '+')}&image_type=photo&per_page=3"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                # Get a random image from the results
                image = random.choice(data['hits'])
                image_url = image['largeImageURL']
                
                img_response = requests.get(image_url, stream=True)
                
                if img_response.status_code == 200:
                    file_path = os.path.join(images_dir, filename)
                    with open(file_path, 'wb') as f:
                        img_response.raw.decode_content = True
                        shutil.copyfileobj(img_response.raw, f)
                    print(f"Downloaded {filename} from Pixabay")
                    return True
            
            print(f"No images found for {search_term}")
            return False
        else:
            print(f"Failed to search for {search_term}: {response.status_code}")
            return False

# Download images for each product
for product_id, product in products.items():
    image_filename = product['image']
    search_term = search_terms.get(product_id, product['name'])
    
    print(f"Downloading image for {product['name']}...")
    download_image(search_term, image_filename)

print("Image download complete!")
