# ไฟล์นี้: สร้างรูปโปรไฟล์วงกลมสำหรับปุ่มบัญชี พร้อมภาพคนเมื่อไม่มีรูป
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parent.parent

# def avatar_image: อ่านภาพเดิมโดยไม่แก้ต้นฉบับและครอบวงกลมตามขนาดปุ่ม
def avatar_image(path,size=44):
    base=Image.new('RGB',(size,size),'#EEF2F6')
    try:
        p=Path(path) if path else None
        if p is None:raise ValueError("No profile image")
        if not p.is_absolute():p=ROOT/p
        with Image.open(p) as im:base=ImageOps.fit(ImageOps.exif_transpose(im).convert('RGB'),(size,size),method=Image.Resampling.LANCZOS)
    except (OSError,TypeError,ValueError):
        draw=ImageDraw.Draw(base)
        draw.ellipse((size*.35,size*.17,size*.65,size*.47),fill='#607D8B')
        draw.ellipse((size*.23,size*.52,size*.77,size*.90),fill='#607D8B')
    mask=Image.new('L',(size,size),0);ImageDraw.Draw(mask).ellipse((1,1,size-2,size-2),fill=255)
    result=Image.new('RGBA',(size,size),(255,255,255,0));result.paste(base,(0,0),mask)
    return result
