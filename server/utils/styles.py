import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(BASE_PATH, "assets", "styles.css")

def load_custom_css():
    try:
        with open(CSS_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❗ CSS file not found at {CSS_PATH}")
        return ""