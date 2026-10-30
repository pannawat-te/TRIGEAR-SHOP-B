# ไฟล์นี้: ออกเลขใบเสร็จ เก็บข้อมูล ณ เวลาออก และสร้าง PDF โดยไม่แก้ข้อมูลเดิม
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP
from xml.sax.saxutils import escape
from database.database import get_connection

ROOT = Path(__file__).resolve().parent.parent
STORE = {"name":"TRIGEAR", "address":"เมือง Khon Kaen 40000", "phone":"0956466576"}

# def money: แปลงจำนวนเงินเป็นข้อความสองตำแหน่งโดยใช้ Decimal
def money(value):
    return f"{Decimal(str(value)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP):,.2f}"

# def issue_receipt: ออกเลขครั้งเดียวใน transaction ของผู้เรียก และ snapshot ข้อมูลจริง
# คืน None เมื่อ Order ยังไม่รับเงินหรืออยู่ระหว่างยกเลิก ผู้เรียกต้อง commit เอง
def issue_receipt(conn,order_id):
    existing=conn.execute("SELECT receipt_number FROM receipts WHERE order_id=?",(order_id,)).fetchone()
    if existing:return existing[0]
    cursor=conn.execute("SELECT * FROM orders WHERE id=?",(order_id,));row=cursor.fetchone()
    if not row:return None
    order=dict(zip([x[0] for x in cursor.description],row))
    if order['payment_status']!='ชำระเงินแล้ว' or order['order_status'].startswith('สถานะถูกยกเลิก') or order['order_status'] in ('ยกเลิกแล้ว','คืนเงินสำเร็จ'):return None
    items=conn.execute("""SELECT COALESCE(p.name,'สินค้าเดิม'),oi.size_label,oi.quantity,oi.price
        FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id
        WHERE oi.order_id=? ORDER BY oi.id""",(order_id,)).fetchall()
    if not items:raise ValueError('ไม่พบรายการสินค้า ไม่สามารถออกใบเสร็จได้')
    timestamp=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(timespec='seconds')
    payment=conn.execute("SELECT payment_date FROM payments WHERE order_id=? AND payment_status='ชำระเงินแล้ว' ORDER BY id DESC LIMIT 1",(order_id,)).fetchone()
    snapshot={"store":dict(STORE),"order_id":order_id,"issued_at":timestamp,
        "customer_name":order.get('shipping_name') or '',"phone":order.get('shipping_phone') or '',
        "address":" ".join(str(order.get(k) or '') for k in ('shipping_address','shipping_subdistrict','shipping_district','shipping_province','shipping_postcode')).strip(),
        "total":str(order['total_price']),"subtotal":str(order.get('subtotal')) if order.get('subtotal') is not None else None,"vat_rate":str(order.get('vat_rate',0)),"vat_amount":str(order.get('vat_amount',0)),"method":"โอนเงิน / QR Payment",
        "payment_date":payment[0] if payment else '',
        "items":[{"name":name,"size":size or '',"quantity":qty,"price":str(price)} for name,size,qty,price in items]}
    cur=conn.execute("INSERT INTO receipts(order_id,issued_at,snapshot_json) VALUES(?,?,?)",(order_id,timestamp,json.dumps(snapshot,ensure_ascii=False)))
    number=f"TG-{timestamp[:4]}-{cur.lastrowid:06d}"
    conn.execute("UPDATE receipts SET receipt_number=? WHERE id=?",(number,cur.lastrowid))
    return number

# def receipt_data: ตรวจเจ้าของ Order และอ่าน snapshot; รองรับออกใบเสร็จให้ Order เก่าที่รับเงินแล้ว
# admin=True ใช้เฉพาะ callback ในหน้า Admin ที่ผ่านการเข้าสู่ระบบแล้ว
def receipt_data(order_id,user_id=None,admin=False):
    conn=get_connection()
    try:
        conn.execute('BEGIN IMMEDIATE')
        owner=conn.execute('SELECT user_id,order_status FROM orders WHERE id=?',(order_id,)).fetchone()
        if not owner or (not admin and owner[0]!=user_id):raise ValueError('ไม่พบคำสั่งซื้อของบัญชีนี้')
        number=issue_receipt(conn,order_id)
        if not number:raise ValueError('ใบเสร็จพร้อมใช้หลังยืนยันรับเงิน และไม่ออกใหม่ให้คำสั่งซื้อที่ยกเลิก')
        row=conn.execute('SELECT snapshot_json FROM receipts WHERE order_id=?',(order_id,)).fetchone()
        conn.commit()
        return number,json.loads(row[0]),owner[1]
    finally:conn.close()

# def thai_fonts: ลงทะเบียนฟอนต์ไทยที่แนบในโปรเจกต์ ไม่ใช้ฟอนต์ที่แสดงภาษาไทยไม่ได้
def thai_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for name,filename in [('ReceiptTH','NotoSansThai-Regular.ttf'),('ReceiptBold','NotoSansThai-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name,str(ROOT/'assets'/'fonts'/filename)))
    return 'ReceiptTH','ReceiptBold'

# def render_pdf: สร้าง A4 หลายหน้า หัวตารางซ้ำ ชื่อไทยยาวตัดบรรทัด และแสดงยอดตาม snapshot
def render_pdf(number,data,target):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_RIGHT
    normal,bold=thai_fonts()
    styles={
        'body':ParagraphStyle('body',fontName=normal,fontSize=10,leading=16,wordWrap='CJK'),
        'title':ParagraphStyle('title',fontName=bold,fontSize=21,leading=30),
        'bold':ParagraphStyle('bold',fontName=bold,fontSize=11,leading=18,wordWrap='CJK'),
        'right':ParagraphStyle('right',fontName=normal,fontSize=10,leading=16,alignment=TA_RIGHT)}
    # def para: escape ข้อความฐานข้อมูลเพื่อไม่ให้ตีความเป็น HTML
    def para(text,style='body'):return Paragraph(escape(str(text)),styles[style])
    story=[]
    logo=Image(str(ROOT/'assets'/'receipt_logo.png'),width=150,height=100)
    head=Table([[logo,[para('ใบเสร็จรับเงิน','title'),para(number,'bold'),para(f"วันที่ออก: {data['issued_at'][:10]} {data['issued_at'][11:19]}")]]],colWidths=[235,280])
    head.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.extend([head,Spacer(1,14),para(data['store']['name'],'bold'),para(data['store']['address']),para('โทร. '+data['store']['phone']),Spacer(1,14),
        para(f"คำสั่งซื้อ #{data['order_id']}",'bold'),para('ผู้ซื้อ / ผู้รับ: '+(data['customer_name'] or '-')),para('เบอร์โทร: '+(data['phone'] or '-')),para('ที่อยู่: '+(data['address'] or '-')),Spacer(1,16)])
    rows=[[para(x,'bold') for x in ('สินค้า / ไซซ์','จำนวน','ราคา / ชิ้น','รวม (บาท)')]]
    for item in data['items']:
        label=item['name']+(f" (ไซซ์ {item['size']})" if item['size'] else '')
        subtotal=Decimal(item['price'])*item['quantity']
        rows.append([para(label),para(item['quantity'],'right'),para(money(item['price']),'right'),para(money(subtotal),'right')])
    table=Table(rows,colWidths=[270,45,95,105],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF2F8')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#233650')),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#D8DFE8'))]))
    story.extend([table,Spacer(1,18)])
    if data.get('subtotal') is not None:
        story.extend([para('ราคาสินค้าก่อน VAT '+money(data['subtotal'])+' บาท'),para('VAT '+str(data['vat_rate'])+'% '+money(data['vat_amount'])+' บาท'),Spacer(1,10)])
    story.extend([KeepTogether([para('ยอดรับชำระทั้งหมด '+money(data['total'])+' บาท','bold'),para('วิธีชำระเงิน: '+data['method']),para('ขอบคุณที่เลือกซื้อสินค้ากับ TRIGEAR')])])
    # def footer: ใส่เลขใบเสร็จและเลขหน้าในทุกหน้า
    def footer(canvas,doc):
        canvas.setFont(normal,8);canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(40,25,number);canvas.drawRightString(A4[0]-40,25,f'หน้า {doc.page}')
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=30,bottomMargin=45,title='TRIGEAR '+number).build(story,onFirstPage=footer,onLaterPages=footer)

# def receipt_pdf: สร้างไฟล์แบบ atomic; ดาวน์โหลดซ้ำใช้ snapshot และเลขเดิม
# คืนสถานะปัจจุบันแยกจาก PDF เดิม เพื่อแจ้งการยกเลิก/คืนเงินใน UI
def receipt_pdf(order_id,user_id=None,admin=False):
    number,data,status=receipt_data(order_id,user_id,admin)
    directory=ROOT/'uploads'/'receipts';directory.mkdir(parents=True,exist_ok=True)
    target=directory/(number+'.pdf')
    if not target.is_file():
        fd,tmp=tempfile.mkstemp(suffix='.pdf',dir=directory);os.close(fd)
        try:render_pdf(number,data,tmp);os.replace(tmp,target)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return target,status
