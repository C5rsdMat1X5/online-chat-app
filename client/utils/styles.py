import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(BASE_PATH, "assets", "styles.css")

def load_custom_css():
    """
    Loads the contents of the custom CSS file specified by CSS_PATH.
    Returns the CSS as a string, or an empty string if the file is not found.
    """
    try:
        with open(CSS_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❗ CSS file not found at {CSS_PATH}")
        return ""