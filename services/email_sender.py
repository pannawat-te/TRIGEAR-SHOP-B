"""Gmail SMTP configuration stays on the shop computer."""
import json
import os
import smtplib
import ssl
import tempfile
from pathlib import Path
from email.message import EmailMessage

CONFIG = Path(__file__).resolve().parents[1] / 'config' / 'smtp.local.json'

def load_settings():
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def save_settings(email, password):
    email = email.strip()
    password = ''.join(password.split())
    if '@' not in email or not password:
        raise ValueError('กรุณากรอก Gmail และ App Password')
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=CONFIG.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'email': email, 'password': password}, stream)
        os.replace(name, CONFIG)
    finally:
        if os.path.exists(name): os.unlink(name)

def build_otp_message(sender, recipient, code, purpose):
    """สร้างอีเมล HTML + ข้อความสำรอง; ไม่ส่งอีเมลจนกว่า send_otp จะถูกเรียก"""
    from html import escape
    from email.utils import make_msgid
    if purpose not in ('register', 'reset'):
        raise ValueError('ประเภท OTP ไม่ถูกต้อง')
    code = str(code)
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        raise ValueError('OTP ต้องเป็นตัวเลข 6 หลัก')
    title = 'ยืนยันอีเมลเพื่อสมัครสมาชิก' if purpose == 'register' else 'รหัส OTP สำหรับตั้งรหัสผ่านใหม่'
    instruction = ('ใช้รหัสด้านล่างเพื่อยืนยันอีเมลของคุณกับ TRIGEAR' if purpose == 'register'
                   else 'ใช้รหัสด้านล่างในหน้าตั้งรหัสผ่านใหม่ของ TRIGEAR เพื่อดำเนินการต่อ')
    expiry = 'รหัสนี้ใช้ได้ภายใน 10 นาที และใช้ได้ครั้งเดียว'
    warning = 'กรุณาอย่าเปิดเผยรหัสนี้ให้ผู้อื่น รวมถึงผู้ดูแลระบบ'
    ignore = 'หากคุณไม่ได้เป็นผู้ขอรหัส สามารถละเว้นอีเมลฉบับนี้ได้'
    message = EmailMessage()
    message['From'] = f'TRIGEAR <{sender}>'
    message['To'] = recipient
    message['Subject'] = f'TRIGEAR | {title}'
    message.set_content(f'TRIGEAR\n\n{title}\n{instruction}\n\nรหัส OTP: {code}\n\n'
                        f'{expiry}\n{warning}\n\n{ignore}\n\n'
                        'ติดต่อ TRIGEAR โทร 0956466576\nอีเมลนี้ส่งจากระบบอัตโนมัติ')
    # แนบโลโก้ภายในอีเมล ไม่โหลดภาพจากเว็บภายนอก และยังอ่านชื่อร้านได้เมื่อไคลเอนต์ซ่อนภาพ
    logo_data = None
    try:
        from io import BytesIO
        from PIL import Image, ImageChops
        logo_path = Path(__file__).resolve().parents[1] / 'assets' / 'tri_gear_logo.png'
        with Image.open(logo_path) as source:
            image = source.convert('RGB')
            mask = ImageChops.difference(image, Image.new('RGB', image.size, 'white')).convert('L').point(lambda x: 255 if x > 65 else 0)
            image = image.crop(mask.getbbox() or (0, 0, *image.size))
            image.thumbnail((240, 140), Image.Resampling.LANCZOS)
            stream = BytesIO();image.save(stream, format='PNG');logo_data = stream.getvalue()
    except (OSError, ImportError, ValueError):
        pass
    cid = make_msgid(domain='trigear.local') if logo_data else None
    logo_html = (f'<img src="cid:{cid[1:-1]}" alt="TRIGEAR" width="120" '
                 'style="display:block;max-width:120px;height:auto;margin:0 auto 14px;border:0;">' if cid else '')
    html = f'''<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#F3F5FA;color:#14253D;font-family:Tahoma,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F3F5FA;">
<tr><td align="center" style="padding:28px 14px;">
<table role="presentation" width="480" cellpadding="0" cellspacing="0" style="width:100%;max-width:480px;background-color:#FFFFFF;border:1px solid #E1E5ED;border-radius:16px;">
<tr><td align="center" style="padding:30px 24px 12px;">{logo_html}
<div style="font-size:21px;font-weight:bold;letter-spacing:1px;color:#4145F1;">TRIGEAR</div></td></tr>
<tr><td align="center" style="padding:8px 24px;">
<h1 style="margin:0;font-size:22px;line-height:1.5;color:#14253D;">{escape(title)}</h1>
<p style="margin:14px 0 18px;font-size:15px;line-height:1.8;color:#57657A;">{escape(instruction)}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td align="center" style="background-color:#F0F0FF;border-radius:10px;padding:18px 8px;">
<div style="font-size:12px;color:#57657A;margin-bottom:6px;">รหัส OTP ของคุณ</div>
<div dir="ltr" style="font-family:Arial,sans-serif;font-size:34px;line-height:1.4;font-weight:bold;letter-spacing:8px;color:#4145F1;">{escape(code)}</div>
</td></tr></table>
<p style="margin:18px 0 8px;font-size:14px;line-height:1.8;">รหัสนี้ใช้ได้ภายใน <strong>10 นาที</strong> และใช้ได้ครั้งเดียว</p>
<p style="margin:0 0 18px;font-size:13px;line-height:1.8;color:#57657A;">{escape(warning)}</p>
</td></tr>
<tr><td align="center" style="padding:0 24px 24px;">
<p style="border-top:1px solid #E7EBF2;padding-top:18px;margin:0;font-size:13px;line-height:1.8;color:#6B778C;">{escape(ignore)}</p>
<p style="font-size:12px;line-height:1.8;color:#6B778C;margin:14px 0 0;">ติดต่อ TRIGEAR โทร 0956466576<br>อีเมลนี้ส่งจากระบบอัตโนมัติ</p>
</td></tr></table></td></tr></table></body></html>'''
    message.add_alternative(html, subtype='html')
    if logo_data:
        message.get_payload()[-1].add_related(logo_data, maintype='image', subtype='png', cid=cid, disposition='inline')
    return message


def send_otp(recipient, code, purpose):
    settings = load_settings()
    if not settings.get('email') or not settings.get('password'):
        raise ValueError('ร้านยังไม่ได้ตั้งค่า Gmail กรุณาให้ Admin เปิดเมนูตั้งค่าอีเมล OTP')
    message = build_otp_message(settings['email'], recipient, code, purpose)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(settings['email'], settings['password'])
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError:
        raise ValueError('Gmail ปฏิเสธการเข้าสู่ระบบ กรุณาตรวจอีเมลและ App Password') from None
    except (OSError, smtplib.SMTPException):
        raise ValueError('ส่งอีเมลไม่สำเร็จ กรุณาตรวจอินเทอร์เน็ตและการตั้งค่า Gmail แล้วลองใหม่') from None
