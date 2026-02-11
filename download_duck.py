import requests
import os

url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/54.png"
save_path = os.path.join("patient_eggs", "static", "img", "duck.png")

# Create directory if not exists
os.makedirs(os.path.dirname(save_path), exist_ok=True)

response = requests.get(url)
if response.status_code == 200:
    with open(save_path, 'wb') as f:
        f.write(response.content)
    print("Download successful")
else:
    print(f"Failed to download: {response.status_code}")
