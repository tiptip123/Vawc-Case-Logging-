import json
import os
import base64
import io
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw

# Global image cache to prevent re-decoding base64 strings
IMAGE_CACHE = {}

def make_circle_image(base64_str_or_path, size=64):
    """Convert base64 image string or file path to a circular ImageTk.PhotoImage"""
    cache_key = f"{base64_str_or_path}_{size}"
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]

    try:
        if not base64_str_or_path:
            return None
            
        if os.path.exists(str(base64_str_or_path)):
            img = Image.open(base64_str_or_path).convert("RGBA")
        else:
            # Assume base64
            img_data = base64.b64decode(base64_str_or_path)
            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        img = img.resize((size, size), resample)
        
        # Create circular mask
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.paste(img, mask=mask)
        
        photo_img = ImageTk.PhotoImage(output)
        IMAGE_CACHE[cache_key] = photo_img
        return photo_img
    except Exception as e:
        print(f"Error creating circle image: {e}")
        return None

def calculate_age(birthdate):
    today = datetime.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    default_config = {
        "lgu_name": "Barangay Tankulan",
        "municipality": "Manolo Fortich",
        "province": "Bukidnon",
        "region": "Region X",
        "office_name": "VAWC Desk",
        "contact_number": "0912-345-6789",
        "email": "vawc.tankulan@gmail.com",
        "appearance_mode": "light",
        "font_scale": 1.0
    }
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return {**default_config, **json.load(f)}
        return default_config
    except (IOError, json.JSONDecodeError):
        return default_config

def get_scaled_font(size, weight="normal", scale=1.0):
    scaled_size = max(int(size * scale), 10)
    return ("Arial", scaled_size, weight)

def save_config(config_data):
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=4)
        return True
    except IOError:
        return False

def show_success(message):
    # Placeholder for success popup
    pass

def show_error(message):
    # Placeholder for error popup
    pass