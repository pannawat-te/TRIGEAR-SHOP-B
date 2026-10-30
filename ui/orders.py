from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: ประวัติคำสั่งซื้อลูกค้า: รายการสินค้า ชำระ ยกเลิก คืนเงิน และยืนยันรับ
from ui.customer_style import header, scroll_body, polish
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import shutil
from datetime import datetime
from database.database import get_connection
from ui.image_utils import photo
from ui.receipt_view import show_receipt
from ui.order_previews import order_items, show_order_items, payment_slip_path, show_slip


# คลาส OrdersPage: เก็บข้อมูลและพฤติกรรมของ ประวัติคำสั่งซื้อลูกค้า
class OrdersPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root,user_id,username,back_callback):
        self.root=root; self.user_id=user_id; self.username=username; self.back_callback=back_callback
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True); self.build()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        from ui.shop_style import customer_header,heading,body,button,BG
        customer_header(self.frame,self.user_id,self,active='orders')
        heading(self.frame,'คำสั่งซื้อของฉัน','ติดตามสถานะ ตรวจสอบสลิป และดูสินค้าที่สั่งซื้อ')
        self.filter_value='ทั้งหมด';self.filter_buttons={}
        filters=tk.Frame(self.frame,bg=BG);filters.pack(fill='x',padx=24,pady=(0,12))
        for i,name in enumerate(['ทั้งหมด','รอตรวจสอบ','ยืนยันแล้ว','กำลังจัดส่ง','สำเร็จ','ยกเลิก']):
            filters.columnconfigure(i,weight=1,uniform='filters')
            b=button(filters,name,lambda n=name:self.set_filter(n),'secondary');b.grid(row=0,column=i,sticky='ew',padx=3);self.filter_buttons[name]=b
        self.body=body(self.frame);self.refresh()

    def set_filter(self,name):self.filter_value=name;self.refresh()

    @staticmethod
    def status_group(status):
        if status=='กำลังตรวจสอบ':return 'รอตรวจสอบ'
        if status=='ยืนยันคำสั่งซื้อ':return 'ยืนยันแล้ว'
        if status=='กำลังจัดส่ง':return 'กำลังจัดส่ง'
        if status in ('จัดส่งสำเร็จ','รับสินค้าแล้ว'):return 'สำเร็จ'
        return 'ยกเลิก'

    def refresh(self):
        from ui.shop_style import card,text,button,WHITE,MUTED,BLUE,BORDER
        for w in self.body.winfo_children():w.destroy()
        conn=get_connection()
        try:
            orders=conn.execute('SELECT id,total_price,order_status,payment_status,order_date,shipping_name,shipping_phone,shipping_address,shipping_subdistrict,shipping_district,shipping_province,shipping_postcode FROM orders WHERE user_id=? ORDER BY id DESC',(self.user_id,)).fetchall()
            receipts={x[0] for x in conn.execute('SELECT r.order_id FROM receipts r JOIN orders o ON o.id=r.order_id WHERE o.user_id=?',(self.user_id,))}
        finally:conn.close()
        for name,b in self.filter_buttons.items():
            count=len(orders) if name=='ทั้งหมด' else sum(self.status_group(o[2])==name for o in orders)
            b.configure(text=f'{name} ({count})',bg=BLUE if name==self.filter_value else WHITE,fg=WHITE if name==self.filter_value else BLUE)
        visible=[o for o in orders if self.filter_value=='ทั้งหมด' or self.status_group(o[2])==self.filter_value]
        if not visible:text(self.body,'ไม่มีคำสั่งซื้อในหมวดนี้',14,color=MUTED).pack(pady=45)
        for o in visible:
            c=card(self.body);c.pack(fill='x',pady=(0,14))
            top=tk.Frame(c,bg=WHITE);top.pack(fill='x')
            text(top,f'คำสั่งซื้อ #{o[0]}',16,True).pack(side='left')
            text(top,f'฿{o[1]:,.2f}',20,True,BLUE).pack(side='right')
            text(c,f'สั่งซื้อเมื่อ {o[4]} · ยอดรวม VAT ตามคำสั่งซื้อ',10,color=MUTED).pack(anchor='w',pady=5)
            group=self.status_group(o[2]);color='#15803D' if group=='สำเร็จ' else '#B45309' if group in ('รอตรวจสอบ','ยกเลิก') else BLUE
            text(c,f'{o[2]}  ·  {o[3]}',11,True,color).pack(fill='x',pady=(6,12))
            items=order_items(self.user_id,o[0]);qty=sum(x[2] for x in items)
            actions=tk.Frame(c,bg=WHITE);actions.pack(fill='x')
            choices=[(f'ดูสินค้า ({qty} ชิ้น)',lambda oid=o[0]:show_order_items(self.root,self.user_id,oid),'primary'),
                ('ดูสลิป',lambda oid=o[0]:show_slip(self.root,payment_slip_path(self.user_id,oid),f'สลิป · Order #{oid}'),'secondary'),
                ('ดูรายละเอียด',lambda row=o:self.show_details(row),'secondary')]
            if o[0] in receipts or (o[3]=='ชำระเงินแล้ว' and group!='ยกเลิก'):
                choices.append(('ใบเสร็จ',lambda oid=o[0]:show_receipt(self.root,oid,self.user_id),'secondary'))
            if o[3]!='ชำระเงินแล้ว' and group!='ยกเลิก':choices.append(('QR / ส่งสลิป',lambda oid=o[0],v=o[1]:self.pay(oid,v),'secondary'))
            if o[2] in ('กำลังตรวจสอบ','ยืนยันคำสั่งซื้อ'):choices.append(('ยกเลิกคำสั่งซื้อ',lambda oid=o[0]:self.cancel(oid),'danger'))
            if o[2]=='คืนเงินสำเร็จ':choices.append(('ดูสลิปคืนเงิน',lambda oid=o[0]:self.view_refund(oid),'secondary'))
            if o[2]=='จัดส่งสำเร็จ':choices.append(('ยืนยันรับสินค้า',lambda oid=o[0]:self.receive(oid),'primary'))
            for i,(title,cmd,kind) in enumerate(choices):
                actions.columnconfigure(i%4,weight=1,uniform='actions')
                button(actions,title,cmd,kind,wraplength=170).grid(row=i//4,column=i%4,sticky='ew',padx=(0,8),pady=4)

    def show_details(self,order):
        from ui.shop_style import body,card,text,button,MUTED
        win=tk.Toplevel(self.root);win.title(f'รายละเอียดคำสั่งซื้อ #{order[0]}');win.geometry('720x520');win.transient(self.root)
        content=body(win);c=card(content,f'คำสั่งซื้อ #{order[0]}');c.pack(fill='x',pady=12)
        text(c,f'{order[2]} · {order[3]}',12,True).pack(fill='x')
        text(c,f'ผู้รับ: {order[5] or "-"} · โทร {order[6] or "-"}',11).pack(fill='x',pady=12)
        text(c,' '.join(str(x) for x in order[7:12] if x),11,color=MUTED).pack(fill='x')
        conn=get_connection()
        try:row=conn.execute('SELECT subtotal,vat_amount,refund_bank,refund_account_name,refund_account_number FROM orders WHERE id=? AND user_id=?',(order[0],self.user_id)).fetchone()
        finally:conn.close()
        if row:
            for title,value in [('ราคาก่อน VAT',row[0] if row[0] is not None else order[1]-(row[1] or 0)),('VAT',row[1] or 0),('ยอดรวม',order[1])]:text(c,f'{title}: ฿{value:,.2f}',12,True).pack(fill='x',pady=5)
            text(c,'บัญชีรับเงินคืน: '+ ' · '.join(str(x or '-') for x in row[2:]),11,color=MUTED).pack(fill='x',pady=12)
        button(c,'ปิด',win.destroy,'secondary').pack(anchor='e',pady=10)

    # def view_refund: เปิดหลักฐานการคืนเงินของคำสั่งซื้อที่เลือก
    def view_refund(self,oid):
        conn=get_connection()
        row=conn.execute("SELECT r.slip,r.amount FROM refunds r JOIN orders o ON o.id=r.order_id WHERE r.order_id=? AND o.user_id=? AND r.refund_status='คืนเงินสำเร็จ'",(oid,self.user_id)).fetchone()
        conn.close()
        if not row or not row[0]:
            messagebox.showinfo("คืนเงิน","ยังไม่มีสลิปคืนเงิน");return
        path=Path(row[0]);path=path if path.is_absolute() else Path(__file__).resolve().parent.parent/path
        if not path.is_file():
            messagebox.showerror("คืนเงิน","ไม่พบไฟล์หลักฐานคืนเงิน");return
        win=tk.Toplevel(self.root);win.title(f"สลิปคืนเงิน Order #{oid} — {row[1]:,.2f} บาท")
        picture=photo(str(path),(650,650));win.picture=picture
        tk.Label(win,image=picture).pack(padx=12,pady=12)

    # def receive: บันทึกว่าลูกค้ายืนยันรับสินค้าของออเดอร์ที่เลือกแล้ว
    def receive(self, oid):
        if not messagebox.askyesno("ยืนยันรับสินค้า", "ได้รับสินค้าครบถ้วนแล้วใช่หรือไม่?"): return
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("""UPDATE orders SET order_status='รับสินค้าแล้ว'
                WHERE id=? AND user_id=? AND order_status='จัดส่งสำเร็จ'""", (oid, self.user_id))
            if cur.rowcount != 1:
                conn.rollback(); messagebox.showwarning("สถานะ", "คำสั่งซื้อนี้ยังไม่พร้อมยืนยันรับสินค้า")
            else:
                conn.commit(); messagebox.showinfo("สำเร็จ", "ยืนยันรับสินค้าแล้ว")
        finally: conn.close()
        self.refresh()

    # def pay: ให้ลูกค้าแนบสลิปและบันทึกการชำระของออเดอร์เดิม
    def pay(self,oid,amount):
        from ui.checkout import CheckoutPage
        win=tk.Toplevel(self.root); win.title(f"Payment #{oid}"); win.geometry("530x650")
        tk.Label(win,text=f"ชำระ Order #{oid}\nยอด {amount:,.2f} บาท",font=("Noto Sans Thai",16,"bold")).pack(pady=10)
        tk.Label(win,text="โปรดตรวจสอบชื่อผู้รับและยอดเงินในแอปธนาคารก่อนโอน",fg="#b45309").pack()
        path=Path(__file__).resolve().parent.parent/"assets"/"krungthai_promptpay.jpg"
        qr_photo=photo(str(path),(360,310)); win.qr_photo=qr_photo
        tk.Label(win,image=qr_photo).pack()
        chosen=tk.StringVar()
        # def choose: เปิดหน้าต่างเลือกไฟล์สลิป แล้วเก็บเส้นทางไฟล์ที่เลือก
        def choose():
            p=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg"),("All files","*.*")])
            if p: chosen.set(p); label.config(text=p)
        label=tk.Label(win,text="ยังไม่ได้เลือกสลิป",wraplength=420); label.pack(pady=8)
        ActionButton(win,text="เลือกสลิป",command=choose).pack()
        # def submit: คัดลอกสลิปและบันทึกการชำระของออเดอร์เดิม เพื่อรอ Admin ตรวจสอบ
        def submit():
            if not chosen.get(): messagebox.showwarning("สลิป","กรุณาเลือกสลิป"); return
            upload=Path(__file__).resolve().parent.parent/"uploads"; upload.mkdir(exist_ok=True)
            src=Path(chosen.get()); dst=upload/f"order_{oid}_{src.name}"; shutil.copy2(src,dst)
            conn=get_connection(); cur=conn.cursor()
            cur.execute("SELECT id FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1",(oid,)); p=cur.fetchone()
            if p: cur.execute("UPDATE payments SET slip=?,payment_status='รอตรวจสอบสลิป',payment_date=? WHERE id=?",(str(dst),datetime.now().isoformat(timespec="seconds"),p[0]))
            else: cur.execute("INSERT INTO payments(order_id,amount,slip,payment_status,payment_date) VALUES(?,? ,?,'รอตรวจสอบสลิป',?)",(oid,amount,str(dst),datetime.now().isoformat(timespec="seconds")))
            cur.execute("UPDATE orders SET payment_status='รอตรวจสอบสลิป' WHERE id=?",(oid,))
            conn.commit(); conn.close(); win.destroy(); self.refresh()
        ActionButton(win,text="ส่งสลิป",command=submit).pack(pady=8)

    # def cancel: ตรวจสิทธิ์และสถานะก่อนยกเลิกออเดอร์ และเตรียมการคืนเงินตามเงื่อนไข
    def cancel(self,oid):
        if not messagebox.askyesno("ยืนยัน","ต้องการยกเลิกคำสั่งซื้อนี้หรือไม่?"):return
        conn=get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT total_price,order_status,payment_status FROM orders WHERE id=? AND user_id=?",(oid,self.user_id)).fetchone()
            if not row or row[1] not in ("กำลังตรวจสอบ","ยืนยันคำสั่งซื้อ"):
                conn.rollback();messagebox.showwarning("ยกเลิก","ไม่สามารถยกเลิกในสถานะนี้ได้");return
            total,state,payment=row
            if state=="ยืนยันคำสั่งซื้อ":
                for pid,qty,vid in conn.execute("SELECT product_id,quantity,variant_id FROM order_items WHERE order_id=?",(oid,)).fetchall():
                    conn.execute("UPDATE products SET stock=stock+? WHERE id=?",(qty,pid))
                    if vid is not None:conn.execute("UPDATE product_variants SET stock=stock+? WHERE id=?",(qty,vid))
            # มีสลิปแล้วต้องเข้าคิวคืนเงิน แม้ Admin ยังไม่ตรวจยอดรับจริง
            has_slip=conn.execute("SELECT 1 FROM payments WHERE order_id=? AND COALESCE(slip,'')!='' LIMIT 1",(oid,)).fetchone()
            needs_refund=payment=="ชำระเงินแล้ว" or bool(has_slip)
            if needs_refund:
                conn.execute("UPDATE orders SET order_status='สถานะถูกยกเลิก - รอคืนเงิน' WHERE id=?",(oid,))
                conn.execute("INSERT INTO refunds(order_id,amount,refund_status,stock_restored) VALUES(?,?,'รอคืนเงิน',?)",(oid,total,int(state=="ยืนยันคำสั่งซื้อ")))
            else:
                conn.execute("UPDATE orders SET order_status='ยกเลิกแล้ว' WHERE id=?",(oid,))
            conn.commit();messagebox.showinfo("ยกเลิก","ยกเลิกคำสั่งซื้อแล้ว"+ (" และรอคืนเงิน" if needs_refund else " (ไม่ต้องคืนเงิน)"))
        except Exception as exc:
            conn.rollback();messagebox.showerror("ผิดพลาด",str(exc))
        finally:conn.close()
        self.refresh()

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        self.frame.destroy(); self.back_callback()
