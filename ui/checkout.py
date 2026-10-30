from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: ชำระเงิน: ที่อยู่ สลิป บัญชีคืนเงิน หน้าสรุป และสร้างคำสั่งซื้อ
from ui.customer_style import entry as customer_entry, header, scroll_body, polish
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import shutil
from datetime import datetime
import re
from ui.image_utils import photo
from ui.order_previews import show_slip

from database.address import get_address
from database.customer_defaults import get_refund,save_checkout_defaults
from database.database import get_connection
from ui.cart import CartPage
from services.pricing import totals,VAT_RATE,amount


# คลาส CheckoutPage: เก็บข้อมูลและพฤติกรรมของ ชำระเงิน
class CheckoutPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root, user_id, username, back_callback):
        self.root=root; self.user_id=user_id; self.username=username; self.back_callback=back_callback
        self.checkout_items=CartPage.selected_items(user_id)
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True)
        from ui.shop_style import customer_header,heading
        customer_header(self.frame,self.user_id,self,active='cart')
        heading(self.frame,'ชำระเงิน','ตะกร้า  ›  ชำระเงิน  ›  ตรวจสอบ')
        self.content=tk.Frame(self.frame,bg="#F3F5F9");self.content.pack(fill="both",expand=True)
        self.build()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        from ui.shop_style import body,card,text,button,form_field,money_summary,two_columns,BG,WHITE,MUTED
        try:items=self.review_items()
        except ValueError as exc:messagebox.showwarning('สินค้า',str(exc));self.back();return
        base,vat,total=totals([(item[5],item[4]) for item in items])
        content=body(self.content);shell=tk.Frame(content,bg=BG);shell.pack(fill='x')
        left=tk.Frame(shell,bg=BG);right=tk.Frame(shell,bg=BG);two_columns(shell,left,right,ratio=(3,2),threshold=1100)
        shipping=card(left,'ที่อยู่จัดส่ง');shipping.pack(fill='x',pady=(0,16))
        text(shipping,'แก้ไขข้อมูลเฉพาะคำสั่งซื้อนี้ได้',10,color=MUTED).pack(anchor='w',pady=(0,8))
        self.shipping_fields={};saved=get_address(self.user_id)
        from database.address import ADDRESS_FIELDS
        for key,label in ADDRESS_FIELDS:
            var=tk.StringVar(value=saved.get(key,''));self.shipping_fields[key]=var;form_field(shipping,label,var)
        account=card(left,'บัญชีรับเงินคืน');account.pack(fill='x',pady=(0,16))
        saved=get_refund(self.user_id)
        self.refund_bank=tk.StringVar(value=saved.get('refund_bank','กรุงไทย'))
        self.refund_name=tk.StringVar(value=saved.get('refund_account_name',''))
        self.refund_number=tk.StringVar(value=saved.get('refund_account_number',''))
        for title,var in [('ธนาคาร',self.refund_bank),('ชื่อเจ้าของบัญชี',self.refund_name),('เลขบัญชี',self.refund_number)]:form_field(account,title,var)
        self.save_defaults=tk.BooleanVar(value=False)
        CheckBox(account,text='บันทึกที่อยู่และบัญชีรับเงินคืนเป็นข้อมูลเริ่มต้น',variable=self.save_defaults,bg=WHITE,wraplength=460,justify='left',selectcolor='#EEEDFF').pack(anchor='w',pady=8)
        text(account,'หากยังไม่มีข้อมูลเริ่มต้น จะบันทึกหลังสั่งซื้อสำเร็จ',10,color=MUTED).pack(anchor='w')
        payment=card(left,'ชำระเงินผ่าน QR');payment.pack(fill='x',pady=(0,16))
        self.qr_label=tk.Label(payment,bg=WHITE);self.qr_label.pack(pady=8);self.make_qr(total)
        button(payment,'ขยาย QR',self.expand_qr,'secondary').pack(pady=6)
        text(payment,f'ยอดที่ต้องโอน ฿{total:,.2f}',19,True,'#4145F1').pack(anchor='w',pady=12)
        text(payment,'ตรวจสอบผู้รับและยอดเงินในแอปธนาคารก่อนโอน',10,color=MUTED).pack(anchor='w')
        self.slip_var=tk.StringVar()
        self.slip_preview=tk.Label(payment,bg=WHITE);self.slip_preview.pack(pady=8)
        self.slip_name=text(payment,'ยังไม่ได้แนบสลิป',10,color=MUTED);self.slip_name.pack(anchor='w')
        button(payment,'แนบสลิปการชำระเงิน',self.choose_slip).pack(fill='x',pady=(10,6))
        button(payment,'ดูสลิปของฉัน',lambda:show_slip(self.root,self.slip_var.get()),'secondary').pack(fill='x')
        summary,labels=money_summary(right,base,vat,total,sum(i[4] for i in items));summary.pack(fill='x')
        button(summary,'ตรวจสอบคำสั่งซื้อ',lambda:self.place_order(total)).pack(fill='x',pady=(8,6))
        button(summary,'กลับตะกร้า',self.back,'secondary').pack(fill='x',pady=6)
        preview=card(right,'สินค้าที่เลือก');preview.pack(fill='x',pady=16)
        self.product_rows(preview,items)

    def product_rows(self,parent,items):
        from ui.shop_style import text,WHITE,MUTED,divider
        conn=get_connection()
        try:
            for pid,vid,title,size,qty,price in items:
                row=tk.Frame(parent,bg=WHITE);row.pack(fill='x',pady=8)
                found=conn.execute('SELECT image FROM products WHERE id=?',(pid,)).fetchone()
                image=photo(found[0] if found else None,(72,72));label=tk.Label(row,image=image,bg=WHITE);label.image=image;label.pack(side='left',padx=(0,12))
                info=tk.Frame(row,bg=WHITE);info.pack(side='left',fill='x',expand=True)
                text(info,title,11,True).pack(fill='x')
                text(info,(f'ไซส์ {size} · ' if size else '')+f'{qty} ชิ้น × ฿{price:,.2f}',10,color=MUTED).pack(fill='x',pady=4)
                text(info,f'฿{amount(price)*qty:,.2f}',12,True).pack(anchor='w')
                divider(parent)
        finally:conn.close()

    # def make_qr: โหลดภาพ QR ที่ร้านกำหนดมาแสดง; ฟังก์ชันนี้ไม่ได้สร้าง QR ตามยอด total
    def make_qr(self,total):
        target=Path(__file__).resolve().parent.parent/"assets"/"krungthai_promptpay.jpg"
        self.qr_photo=photo(str(target),(260,235))
        self.qr_label.config(image=self.qr_photo)

    # def expand_qr: เปิด QR ต้นฉบับขนาดใหญ่ในหน้าต่างแยก โดยไม่เปลี่ยนข้อมูลชำระเงิน
    def expand_qr(self):
        target=Path(__file__).resolve().parent.parent/"assets"/"krungthai_promptpay.jpg"
        show_slip(self.root,str(target),"QR Payment — ตรวจสอบผู้รับและยอดเงินก่อนโอน")

    # def choose_slip: เปิดหน้าต่างเลือกไฟล์สลิป และเก็บเส้นทางไฟล์ที่เลือก
    def choose_slip(self):
        path=filedialog.askopenfilename(title="เลือกสลิป",filetypes=[("Images","*.png *.jpg *.jpeg"),("All files","*.*")])
        if path:
            self.slip_var.set(path)
            image=photo(path,(150,140));self.slip_preview.configure(image=image);self.slip_preview.image=image
            self.slip_name.configure(text=Path(path).name)

    # def review_items: อ่านรายการตะกร้าพร้อมราคา/ไซซ์ล่าสุด ตรวจ Stock และคืนข้อมูลสำหรับหน้าสรุป
    def review_items(self):
        conn=get_connection()
        try:
            rows=[]
            cart=CartPage.carts.get(self.user_id,{})
            if any(cart.get(k)!=q for k,q in self.checkout_items.items()):raise ValueError("จำนวนสินค้าในตะกร้าเปลี่ยน กรุณากลับไปเลือกใหม่")
            CartPage.validate_limits(self.user_id,conn,self.checkout_items)
            for key,qty in self.checkout_items.items():
                pid,vid=key if isinstance(key,tuple) else (key,None)
                p=conn.execute("SELECT name,price,stock,size_type FROM products WHERE id=?",(pid,)).fetchone()
                if not p or qty<1 or qty>p[2]:raise ValueError("สินค้าในตะกร้ามี Stock ไม่เพียงพอ")
                size=""
                if p[3]!='none' or vid is not None:
                    v=conn.execute("SELECT size,stock FROM product_variants WHERE id=? AND product_id=?",(vid,pid)).fetchone()
                    if not v or qty>v[1]:raise ValueError("ไซซ์ที่เลือกไม่มีสินค้าหรือ Stock ไม่เพียงพอ")
                    size=v[0]
                rows.append((pid,vid,p[0],size,qty,p[1]))
            if not rows:raise ValueError("ตะกร้าว่าง")
            return rows
        finally:conn.close()

    # def show_review: ซ่อนฟอร์มชำระเงินแล้วแสดงสินค้ากับข้อมูลจัดส่งให้ตรวจ ก่อนสร้างออเดอร์
    def show_review(self,items,shipping,bank,name,number):
        from ui.shop_style import customer_header,heading,body,card,text,button,money_summary,two_columns,BG,WHITE,MUTED
        self.checkout_layout=[(w,w.pack_info()) for w in self.frame.winfo_children()]
        for w,options in self.checkout_layout:w.pack_forget()
        review=tk.Frame(self.frame,bg=BG);review.pack(fill='both',expand=True);self.review_frame=review
        customer_header(review,self.user_id,self,back=self.edit_checkout)
        heading(review,'ตรวจสอบคำสั่งซื้อ','ตะกร้า  ›  ชำระเงิน  ›  ตรวจสอบก่อนยืนยัน')
        content=body(review);shell=tk.Frame(content,bg=BG);shell.pack(fill='x')
        left=tk.Frame(shell,bg=BG);right=tk.Frame(shell,bg=BG);two_columns(shell,left,right,ratio=(3,2),threshold=1100)
        address=card(left,'ที่อยู่จัดส่ง');address.pack(fill='x',pady=(0,16))
        text(address,f"{shipping['shipping_name']} · {shipping['shipping_phone']}",12,True).pack(fill='x')
        text(address,' '.join(shipping[k] for k in ('shipping_address','shipping_subdistrict','shipping_district','shipping_province','shipping_postcode')),11,color=MUTED).pack(fill='x',pady=10)
        button(address,'แก้ไข',self.edit_checkout,'secondary').pack(anchor='e')
        products=card(left,'รายการสินค้า');products.pack(fill='x',pady=(0,16));self.product_rows(products,items)
        payment=card(left,'หลักฐานการชำระเงิน');payment.pack(fill='x',pady=(0,16))
        image=photo(self.slip_var.get(),(170,180));label=tk.Label(payment,image=image,bg=WHITE);label.image=image;label.pack(anchor='w')
        button(payment,'ดูสลิปที่แนบ',lambda:show_slip(self.root,self.slip_var.get()),'secondary').pack(anchor='w',pady=8)
        text(payment,'บัญชีรับเงินคืน',12,True).pack(anchor='w',pady=(10,5))
        text(payment,f'{bank} · {name} · {number}',11,color=MUTED).pack(fill='x')
        base,vat,total=totals([(row[5],row[4]) for row in items])
        summary,labels=money_summary(right,base,vat,total,sum(row[4] for row in items));summary.pack(fill='x')
        self.review_items_snapshot=items
        self.confirm_button=button(summary,'ยืนยันคำสั่งซื้อ',lambda:self.confirm_review(total));self.confirm_button.pack(fill='x',pady=(8,6))
        button(summary,'กลับไปแก้ไข',self.edit_checkout,'secondary').pack(fill='x',pady=6)
        text(summary,'คำสั่งซื้อจะถูกสร้างเมื่อกดยืนยันเท่านั้น',10,color=MUTED).pack(fill='x',pady=10)

    # def edit_checkout: ปิดหน้าสรุปแล้วแสดงฟอร์มเดิม โดยยังเก็บค่าที่กรอกไว้
    def edit_checkout(self):
        self.review_frame.destroy()
        for w,options in self.checkout_layout:w.pack(**options)

    # def confirm_review: ตรวจว่าข้อมูลสินค้ายังตรงกับหน้าสรุป แล้วเรียกสร้างออเดอร์
    def confirm_review(self,total):
        try:
            if self.review_items()!=self.review_items_snapshot:
                raise ValueError("สินค้า ราคา หรือจำนวนเปลี่ยนไป กรุณาตรวจสอบคำสั่งซื้ออีกครั้ง")
        except ValueError as exc:
            messagebox.showwarning("ตรวจสอบคำสั่งซื้อ",str(exc));self.edit_checkout();return
        self.confirm_button.configure(state="disabled")
        try:self.place_order(total,confirmed=True)
        finally:
            if self.frame.winfo_exists() and self.confirm_button.winfo_exists():self.confirm_button.configure(state="normal")

    # def place_order: ตรวจที่อยู่ บัญชีคืนเงิน และสลิป; แสดงหน้าสรุป หรือสร้างออเดอร์/รายการสินค้า/การชำระในธุรกรรม
    def place_order(self,total,confirmed=False):
        if not self.slip_var.get():
            messagebox.showwarning("ชำระเงิน","กรุณาเลือกสลิปก่อนยืนยันคำสั่งซื้อ")
            return
        shipping={key:var.get().strip() for key,var in self.shipping_fields.items()}
        if any(not v for v in shipping.values()):
            messagebox.showwarning("ข้อมูลจัดส่ง","กรุณากรอกข้อมูลผู้รับและที่อยู่จัดส่งให้ครบทุกช่อง");return
        if not re.fullmatch(r"0[0-9]{8,9}",re.sub(r"[\s-]","",shipping["shipping_phone"])):
            messagebox.showwarning("เบอร์โทร","กรุณากรอกเบอร์โทรศัพท์ไทย 9–10 หลัก เริ่มด้วย 0");return
        if not re.fullmatch(r"[0-9]{5}",shipping["shipping_postcode"]):
            messagebox.showwarning("รหัสไปรษณีย์","กรุณากรอกรหัสไปรษณีย์ 5 หลัก");return
        bank=self.refund_bank.get().strip(); name=self.refund_name.get().strip()
        number=re.sub(r"[\s-]", "", self.refund_number.get())
        if not bank or not name or not re.fullmatch(r"[0-9]{9,15}",number):
            messagebox.showwarning("บัญชีรับเงินคืน","กรุณากรอกธนาคาร ชื่อบัญชี และเลขบัญชี 9–15 หลัก")
            return
        if not confirmed:
            try:items=self.review_items()
            except ValueError as exc:
                messagebox.showwarning("คำสั่งซื้อ",str(exc));return
            self.show_review(items,shipping,bank,name,number)
            return
        conn=get_connection(); cur=conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            from database.members import require_active_customer
            require_active_customer(conn,self.user_id)
            CartPage.validate_limits(self.user_id,conn,self.checkout_items)
            if self.review_items()!=self.review_items_snapshot:
                raise ValueError("ข้อมูลสินค้าเปลี่ยนไป กรุณากลับไปตรวจสอบอีกครั้ง")
            base,vat,total=totals([(row[5],row[4]) for row in self.review_items_snapshot])
            cur.execute("""INSERT INTO orders(user_id,total_price,refund_bank,refund_account_name,refund_account_number,
                shipping_name,shipping_phone,shipping_address,shipping_subdistrict,shipping_district,shipping_province,shipping_postcode)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(self.user_id,float(total),bank,name,number,
                *(shipping[k] for k in ("shipping_name","shipping_phone","shipping_address","shipping_subdistrict","shipping_district","shipping_province","shipping_postcode"))))
            oid=cur.lastrowid
            cur.execute("UPDATE orders SET subtotal=?,vat_rate=?,vat_amount=? WHERE id=?",(str(base),str(VAT_RATE),str(vat),oid))
            for key,qty in self.checkout_items.items():
                pid,vid=key if isinstance(key,tuple) else (key,None)
                cur.execute("SELECT price,stock FROM products WHERE id=?",(pid,))
                p=cur.fetchone()
                if not p or qty>p[1]: raise ValueError("Stock ไม่เพียงพอ")
                size=None
                if vid is not None:
                    v=cur.execute("SELECT size,stock FROM product_variants WHERE id=? AND product_id=?",(vid,pid)).fetchone()
                    if not v or v[1]<qty:raise ValueError("Stock ของไซซ์ที่เลือกไม่เพียงพอ")
                    size=v[0]
                cur.execute("INSERT INTO order_items(order_id,product_id,quantity,price,variant_id,size_label) VALUES(?,?,?,?,?,?)",(oid,pid,qty,float(amount(p[0])),vid,size))
            upload_dir=Path(__file__).resolve().parent.parent/"uploads"
            upload_dir.mkdir(exist_ok=True)
            src=Path(self.slip_var.get()); dst=upload_dir/f"order_{oid}_{src.name}"
            shutil.copy2(src,dst)
            cur.execute("INSERT INTO payments(order_id,amount,slip,payment_status,payment_date) VALUES(?,?,?,'รอตรวจสอบสลิป',?)",
                        (oid,float(total),str(dst),datetime.now().isoformat(timespec="seconds")))
            cur.execute("UPDATE orders SET payment_status='รอตรวจสอบสลิป' WHERE id=?",(oid,))
            save_checkout_defaults(conn,self.user_id,shipping,{
                'refund_bank':bank,'refund_account_name':name,'refund_account_number':number},self.save_defaults.get())
            from database.cart_store import remove_purchased
            remove_purchased(conn,self.user_id,self.checkout_items)
            conn.commit()
            CartPage.complete_purchase(self.user_id,self.checkout_items)
            messagebox.showinfo("สำเร็จ",f"สร้างคำสั่งซื้อ #{oid} แล้ว\nรอ Admin ตรวจสอบสลิป")
            self.frame.destroy(); self.back_callback()
        except Exception as e:
            conn.rollback(); messagebox.showerror("ผิดพลาด",str(e))
        finally: conn.close()

    # def back: เปิดตะกร้าเดิมของผู้ใช้ ส่วน callback เดิมเก็บไว้ให้ตะกร้ากลับหน้าร้าน
    def back(self):
        self.frame.destroy()
        CartPage(self.root,self.user_id,self.username,self.back_callback)
