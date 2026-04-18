import os
import urllib.request

base_dir = r"c:\Users\themr\OneDrive\Desktop\AgriRent\static\images"
os.makedirs(base_dir, exist_ok=True)

images = [
    "mahindra_575.jpg", "mahindra_475.jpg", "mahindra_arjun_555.jpg",
    "swaraj_735.jpg", "swaraj_744.jpg", "john_5050.jpg",
    "john_5310.jpg", "newholland_3630.jpg", "newholland_3600.jpg",
    "massey_1035.jpg", "massey_241.jpg", "sonalika_745.jpg",
    "sonalika_750.jpg", "eicher_380.jpg", "kubota_mu5501.jpg",
    "default.jpg"
]

for i, img in enumerate(images):
    url = f"https://loremflickr.com/800/600/tractor?lock={i+1}"
    if img == "default.jpg":
        url = "https://loremflickr.com/800/600/farm,equipment?lock=100"
    out_path = os.path.join(base_dir, img)
    print(f"Downloading {img} from {url}...")
    try:
        urllib.request.urlretrieve(url, out_path)
    except Exception as e:
        print(f"Failed to download {img}: {e}")

print("Done!")
