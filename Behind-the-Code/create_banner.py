"""
create_banner.py – Generates a cyberpunk-themed banner image using Pillow

Use this for Notion headers or GitHub visuals
"""

from PIL import Image, ImageDraw, ImageFont

width, height = 1500, 400
img = Image.new("RGB", (width, height), color=(10, 10, 10))
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
    font_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
except IOError:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

draw.text((150, 100), "PROGRAMMING PACT", font=font_title, fill=(0, 255, 200))
draw.text((150, 220), "Automation. Brotherhood. Cybersecurity. Creation.", font=font_sub, fill=(100, 255, 255))

img.save("programming_pact_banner.png")
