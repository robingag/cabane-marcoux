import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

DEVICE_ID = "a48c"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# QR code content: the ESP32 serves the remote page at /remote
# When connected to same WiFi, scan QR -> get the MQTT remote page
# The page works via MQTT so it keeps working from anywhere after loading
ESP32_IP = "10.0.0.205"
URL = f"http://{ESP32_IP}/remote"

print(f"URL encodee dans le QR: {URL}")
print(f"Device ID: {DEVICE_ID}")

# Generate QR code
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=4)
qr.add_data(URL)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

# Add header and footer text
qr_w, qr_h = img.size
padding_top = 70
padding_bottom = 60
final = Image.new('RGB', (qr_w, qr_h + padding_top + padding_bottom), 'white')
final.paste(img, (0, padding_top))

draw = ImageDraw.Draw(final)
try:
    font_title = ImageFont.truetype("arial.ttf", 30)
    font_sub = ImageFont.truetype("arial.ttf", 20)
    font_sm = ImageFont.truetype("arial.ttf", 16)
except:
    font_title = ImageFont.load_default()
    font_sub = font_title
    font_sm = font_title

# Title
draw.text((qr_w // 2, 15), "CYD Remote Control", fill="black", anchor="mt", font=font_title)
draw.text((qr_w // 2, 50), f"Device ID: {DEVICE_ID}", fill="gray", anchor="mt", font=font_sub)

# Footer
draw.text((qr_w // 2, qr_h + padding_top + 10), "Scannez avec votre telephone", fill="gray", anchor="mt", font=font_sm)
draw.text((qr_w // 2, qr_h + padding_top + 35), f"WiFi requis - {URL}", fill="gray", anchor="mt", font=font_sm)

qr_path = os.path.join(OUTPUT_DIR, f"qr_cyd_{DEVICE_ID}.png")
final.save(qr_path)
print(f"QR code sauvegarde: {qr_path}")
print("Done!")
