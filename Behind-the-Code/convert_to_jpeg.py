"""
convert_to_jpeg.py – Converts any PNG image into JPEG format using Pillow
"""

from PIL import Image

input_file = "programming_pact_banner.png"
output_file = "programming_pact_banner.jpg"

img = Image.open(input_file)
rgb_img = img.convert("RGB")
rgb_img.save(output_file, format="JPEG")
