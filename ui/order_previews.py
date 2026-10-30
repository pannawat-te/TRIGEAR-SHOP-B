from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: หน้าต่างดูสลิปและรายการสินค้าที่ใช้ร่วมกันในฝั่งลูกค้า
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from database.database import get_connection
from ui.customer_style import scroll_body
from ui.image_utils import photo

ROOT = Path(__file__).resolve().parent.parent

# def payment_slip_path: อ่านสลิปล่าสุดโดยตรวจว่าคำสั่งซื้อเป็นของผู้ใช้ปัจจุบัน
def payment_slip_path(user_id, order_id):
    conn = get_connection()
    try:
        row = conn.execute("""SELECT p.slip FROM payments p JOIN orders o ON o.id=p.order_id
            WHERE o.id=? AND o.user_id=? ORDER BY p.id DESC LIMIT 1""",
            (order_id, user_id)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()

# def order_items: อ่านรายการสินค้าของ Order พร้อมตรวจสิทธิ์เจ้าของบัญชี
def order_items(user_id, order_id):
    conn = get_connection()
    try:
        return conn.execute("""SELECT COALESCE(p.name,'สินค้าเดิม'),oi.size_label,
            oi.quantity,oi.price,p.image FROM order_items oi
            JOIN orders o ON o.id=oi.order_id LEFT JOIN products p ON p.id=oi.product_id
            WHERE o.id=? AND o.user_id=? ORDER BY oi.id""", (order_id,user_id)).fetchall()
    finally:
        conn.close()

# def show_slip: ตรวจไฟล์และเปิดภาพสลิปเต็มภาพตามขนาดหน้าจอ ไม่แก้ต้นฉบับ
def show_slip(root, path, title="สลิปการชำระเงิน"):
    if not path:
        messagebox.showinfo("สลิป", "ยังไม่มีสลิปแนบ");return
    candidate = Path(path)
    if not candidate.is_absolute():candidate = ROOT / candidate
    try:
        with Image.open(candidate) as im:
            im.load()
            im.thumbnail((max(200,root.winfo_screenwidth()-160),max(200,root.winfo_screenheight()-220)))
            picture = ImageTk.PhotoImage(im.copy())
    except (OSError, ValueError):
        messagebox.showwarning("สลิป", "ไม่พบไฟล์สลิปหรือไฟล์ภาพเปิดไม่ได้");return
    win = tk.Toplevel(root);win.title(title);win.transient(root)
    label = tk.Label(win,image=picture,bg="white");label.image=picture
    label.pack(padx=16,pady=12)
    ActionButton(win,text="ปิด",command=win.destroy).pack(pady=(0,12))

# def show_order_items: เปิด Popup เลื่อนดูรูป ชื่อเต็ม ไซซ์ จำนวน และราคาแต่ละรายการ
def show_order_items(root,user_id,order_id):
    items = order_items(user_id,order_id)
    if not items:
        messagebox.showinfo("รายการสินค้า","ไม่พบรายการสินค้าของคำสั่งซื้อนี้");return
    win=tk.Toplevel(root);win.title(f"สินค้าที่สั่ง · Order #{order_id}");win.transient(root)
    win.geometry(f"{min(800,root.winfo_screenwidth()-80)}x{min(620,root.winfo_screenheight()-100)}")
    tk.Label(win,text=f"Order #{order_id} · {len(items)} รายการ · {sum(x[2] for x in items)} ชิ้น",
             font=("Noto Sans Thai",14,"bold")).pack(pady=12)
    body=scroll_body(win)
    for name,size,qty,price,path in items:
        row=tk.Frame(body,bg="white",padx=12,pady=12);row.pack(fill="x",padx=12,pady=5)
        row.grid_columnconfigure(1,weight=1)
        picture=photo(path,(90,75));label=tk.Label(row,image=picture,bg="white");label.image=picture
        label.grid(row=0,column=0,rowspan=3,padx=(0,12))
        title=tk.Label(row,text=name,font=("Noto Sans Thai",12,"bold"),justify="left",anchor="w",bg="white",wraplength=540)
        title.grid(row=0,column=1,sticky="ew")
        title.bind("<Configure>",lambda e,w=title:w.configure(wraplength=max(100,e.width-8)))
        tk.Label(row,text=f"ไซซ์: {size or '-'} · จำนวน {qty} ชิ้น",bg="white",anchor="w").grid(row=1,column=1,sticky="ew",pady=4)
        tk.Label(row,text=f"฿{price:,.2f} / ชิ้น · รวม ฿{qty*price:,.2f}",bg="white",anchor="w").grid(row=2,column=1,sticky="ew")
    ActionButton(win,text="ปิด",command=win.destroy).pack(pady=12)
