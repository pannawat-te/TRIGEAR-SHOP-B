# ไฟล์นี้: โหลดโลโก้ TRI GEAR และกำหนดสีแบรนด์
from pathlib import Path
from PIL import Image, ImageTk, ImageChops

BLUE = "#4145F1"

# def logo: โหลดและปรับขนาดโลโก้ คืนภาพสำหรับใช้กับวิดเจ็ต Tkinter
def logo(size):
    with Image.open(Path(__file__).resolve().parent.parent / "assets/tri_gear_logo.png") as source:
        im = source.convert("RGB")
        mask = ImageChops.difference(im, Image.new("RGB", im.size, "white")).convert("L").point(lambda x: 255 if x > 65 else 0)
        box = mask.getbbox()
        im = im.crop(box).convert("RGBA")
        alpha = im.convert("RGB").convert("L").point(lambda x: 0 if x > 225 else 255)
        im.putalpha(alpha)
        im.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(im)
