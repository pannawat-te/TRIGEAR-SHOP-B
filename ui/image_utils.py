# ไฟล์นี้: คัดลอกรูปเข้า uploads และปรับภาพเพื่อแสดงใน Tkinter
"""Safe image loading, resizing and portable storage."""
from pathlib import Path
from uuid import uuid4
import shutil
from PIL import Image, ImageTk, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DIR = ROOT / "uploads" / "products"

# def store_image: คัดลอกรูปต้นทางไปเก็บในพื้นที่ uploads ของโปรเจกต์ และคืนเส้นทางที่บันทึก
def store_image(source):
    if not source:
        return ""
    source = Path(source)
    if not source.is_file() or source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("กรุณาเลือกไฟล์ภาพ JPG, PNG หรือ WEBP ที่เปิดได้")
    try:
        with Image.open(source) as im:
            im.verify()
    except Exception as exc:
        raise ValueError("ไม่สามารถเปิดไฟล์ภาพนี้ได้") from exc
    PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
    target = PRODUCT_DIR / (uuid4().hex + source.suffix.lower())
    shutil.copy2(source, target)
    return target.relative_to(ROOT).as_posix()

# def photo: อ่านและย่อภาพให้พอดีขนาด; สร้างภาพสำรองเมื่อเปิดรูปต้นทางไม่ได้
def photo(path, size=(180, 135)):
    w,h=size
    canvas=Image.new('RGB', size, '#F6F8FC')
    source=ROOT / path if path and not Path(path).is_absolute() else Path(path) if path else None
    try:
        if not source or not source.is_file():
            raise FileNotFoundError()
        with Image.open(source) as im:
            im=im.convert('RGBA')
            im.thumbnail((w-12,h-12), Image.Resampling.LANCZOS)
            base=Image.new('RGBA', im.size, 'white')
            base.alpha_composite(im)
            canvas.paste(base.convert('RGB'), ((w-im.width)//2,(h-im.height)//2))
    except (OSError,ValueError,FileNotFoundError):
        d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((w//2-26,h//2-25,w//2+26,h//2+17),radius=7,outline='#8ca0b5',width=3)
        d.text((w//2-24,h//2+25),'NO IMAGE',fill='#60758c')
    return ImageTk.PhotoImage(canvas)
