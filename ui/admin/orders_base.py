from ui.modern_widgets import ActionButton,RoundedCard
# ไฟล์นี้: จัดการคำสั่งซื้อ: ตรวจสลิป เปลี่ยนสถานะ จัดส่ง และคืนเงิน
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ui.image_utils import photo, ROOT
from database.database import get_connection
from services.receipt import issue_receipt, receipt_pdf
from ui.receipt_view import show_receipt


# คลาส AdminOrdersPage: เก็บข้อมูลและพฤติกรรมของ จัดการคำสั่งซื้อ
class AdminOrdersPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,back_callback):
        self.root=root; self.back_callback=back_callback
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True); self.build(); self.load()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        self.frame.configure(bg="#f1f5f9")
        tk.Label(self.frame,text="จัดการคำสั่งซื้อ / ตรวจสลิป",font=("Noto Sans Thai",20,"bold"),bg="#f1f5f9").pack(pady=10)
        self.tree=ttk.Treeview(self.frame,columns=("id","user","total","order","payment","slip","date"),show="headings",height=8)
        for c,t,w in (("id","Order",65),("user","ลูกค้า",130),("total","ยอด",95),("order","Order Status",170),("payment","Payment Status",150),("slip","หลักฐานโอน",120),("date","วันที่",150)):
            self.tree.heading(c,text=t); self.tree.column(c,width=w,anchor="center")
        self.tree.pack(fill="x",padx=16,pady=6)
        self.tree.bind("<<TreeviewSelect>>",self.select)
        area=tk.Frame(self.frame,bg="white"); area.pack(fill="both",expand=True,padx=16,pady=8)
        left=tk.Frame(area,bg="white"); left.pack(side="left",fill="both",expand=True,padx=12,pady=10)
        self.detail=tk.Text(left,height=12,wrap="word",font=("Noto Sans Thai",11)); self.detail.pack(fill="both",expand=True)
        ActionButton(left,text="ดู / แนบสลิปคืนเงิน",command=self.refund_slip_dialog).pack(anchor="w",pady=5)
        ActionButton(left,text="ดู / บันทึก / พิมพ์ใบเสร็จ",command=self.view_receipt).pack(anchor="w",pady=5)
        right=tk.Frame(area,bg="white",width=300); right.pack(side="right",fill="y",padx=12,pady=10)
        tk.Label(right,text="สลิปของคำสั่งซื้อที่เลือก",bg="white",font=("Noto Sans Thai",12,"bold")).pack(pady=(0,8))
        self.slip_label=tk.Label(right,text="เลือกคำสั่งซื้อเพื่อดูสลิป",bg="#e9eef5",width=35,height=13,compound="center")
        self.slip_label.pack()
        self.slip_photo=None; self.slip_path=None
        ActionButton(right,text="ขยายภาพสลิป",command=self.open_slip).pack(fill="x",pady=(10,4))
        ActionButton(right,text="อนุมัติการชำระเงิน",command=self.confirm_payment,bg="#15803D",fg="white",activebackground="#166534",activeforeground="white").pack(fill="x",pady=3)
        ActionButton(right,text="ปฏิเสธสลิป",command=self.reject_payment,bg="#DC2626",fg="white",activebackground="#B91C1C",activeforeground="white").pack(fill="x",pady=3)
        btn=tk.Frame(self.frame,bg="#f1f5f9"); btn.pack(pady=8)
        for label,callback in (("ยืนยันคำสั่งซื้อ",self.confirm_order),("กำลังจัดส่ง",self.shipping),("จัดส่งสำเร็จ",self.delivered),("คืนเงินสำเร็จ",self.refund_done),("กลับ Dashboard",self.back)):
            ActionButton(btn,text=label,command=callback).pack(side="left",padx=4)

    # def show_slip: เปิดภาพหลักฐานตามเส้นทางที่รับมา
    def show_slip(self, path):
        self.slip_photo=None; self.slip_path=None
        if not path:
            self.slip_label.configure(image="",text="ยังไม่มีสลิปการชำระเงิน")
            return
        candidate=Path(path)
        if not candidate.is_absolute(): candidate=ROOT / candidate
        if not candidate.is_file():
            self.slip_label.configure(image="",text="ไม่พบไฟล์สลิป\nโปรดตรวจสอบไฟล์ต้นฉบับ")
            return
        try:
            from PIL import Image
            with Image.open(candidate) as im: im.verify()
            self.slip_photo=photo(str(candidate),(280,310))
            self.slip_path=candidate
            self.slip_label.configure(image=self.slip_photo,text="",width=280,height=310)
        except Exception as exc:
            self.slip_label.configure(image="",text="ไม่สามารถเปิดไฟล์สลิปได้")
            messagebox.showerror("เปิดสลิปไม่สำเร็จ", str(exc))

    # def open_slip: อ่านคำสั่งซื้อที่เลือกแล้วเปิดหลักฐานการชำระ
    def open_slip(self):
        if not self.slip_path:
            messagebox.showinfo("สลิป", "ไม่มีไฟล์สลิปที่เปิดได้"); return
        win=tk.Toplevel(self.root); win.title("หลักฐานการชำระเงิน"); win.geometry("700x750")
        from PIL import Image, ImageTk
        try:
            with Image.open(self.slip_path) as im:
                im=im.copy(); im.thumbnail((660,680),Image.Resampling.LANCZOS)
            picture=ImageTk.PhotoImage(im)
            label=tk.Label(win,image=picture); label.image=picture; label.pack(expand=True)
        except Exception as exc:
            win.destroy(); messagebox.showerror("สลิป",f"เปิดภาพไม่ได้: {exc}")

    # def reject_payment: เปลี่ยนสถานะสลิปที่ไม่ผ่านการตรวจ เพื่อให้ลูกค้าดำเนินการใหม่
    def reject_payment(self):
        oid=self.selected_id()
        if oid is None:return
        conn=get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            state=conn.execute("SELECT order_status,payment_status FROM orders WHERE id=?",(oid,)).fetchone()
            latest=conn.execute("SELECT id,slip FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1",(oid,)).fetchone()
            if not state or state[0]!="กำลังตรวจสอบ" or state[1]!="รอตรวจสอบสลิป" or not latest or not latest[1]:
                conn.rollback(); messagebox.showwarning("สลิป","ปฏิเสธได้เฉพาะสลิปที่รอตรวจสอบ");return
            if not messagebox.askyesno("ยืนยัน","ปฏิเสธสลิปนี้และให้ลูกค้าอัปโหลดใหม่?"):
                conn.rollback();return
            conn.execute("UPDATE payments SET payment_status='ปฏิเสธสลิป' WHERE id=?",(latest[0],))
            conn.execute("UPDATE orders SET payment_status='ยังไม่ชำระ' WHERE id=?",(oid,))
            conn.commit()
        finally:conn.close()
        self.load(); self.select_order(oid)

    # def select_order: เลือกออเดอร์จากรหัสที่ระบุและอัปเดตรายละเอียดบนหน้าจอ
    def select_order(self,oid):
        for item in self.tree.get_children():
            if int(self.tree.item(item)["values"][0])==int(oid):
                self.tree.selection_set(item);self.tree.see(item);self.select();return

    # def load: อ่านข้อมูลล่าสุดจากฐานข้อมูล แล้วเติมรายการในหน้าจอ
    def load(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        conn=get_connection(); cur=conn.cursor()
        cur.execute("""SELECT o.id,u.username,o.total_price,o.order_status,o.payment_status,
                    CASE WHEN (SELECT slip FROM payments WHERE order_id=o.id ORDER BY id DESC LIMIT 1) IS NOT NULL
                         THEN 'มีสลิป' ELSE 'ไม่มีสลิป' END,o.order_date
                    FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.id DESC""")
        rows=cur.fetchall();conn.close()
        for r in rows:self.tree.insert("",tk.END,values=r)

    # def selected_id: คืนรหัสออเดอร์ที่เลือก หรือแจ้งให้เลือกก่อนดำเนินการ
    def selected_id(self):
        s=self.tree.selection()
        return self.tree.item(s[0])["values"][0] if s else None

    # def select: อ่านข้อมูลรายการที่เลือกมาแสดงในฟอร์มหรือรายละเอียด
    def select(self,event=None):
        oid=self.selected_id()
        if not oid:
            self.show_slip(None);return
        conn=get_connection(); cur=conn.cursor()
        cur.execute("""SELECT o.id,u.username,o.total_price,o.order_status,o.payment_status,o.order_date,
                       p.slip,p.amount,o.refund_bank,o.refund_account_name,o.refund_account_number,
                       o.shipping_name,o.shipping_phone,o.shipping_address,o.shipping_subdistrict,
                       o.shipping_district,o.shipping_province,o.shipping_postcode
                       FROM orders o JOIN users u ON o.user_id=u.id
                       LEFT JOIN payments p ON p.order_id=o.id
                       WHERE o.id=? ORDER BY p.id DESC LIMIT 1""",(oid,))
        r=cur.fetchone()
        cur.execute("""SELECT p.name || COALESCE(' (ไซซ์ ' || oi.size_label || ')',''),oi.quantity,oi.price FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""",(oid,))
        items=cur.fetchall(); conn.close()
        self.detail.delete("1.0",tk.END)
        if r:
            text=f"Order #{r[0]} | ลูกค้า {r[1]} | ยอด {r[2]:,.2f}\nOrder: {r[3]}\nPayment: {r[4]}\nSlip: {r[6] or '-'}\n"
            text+=f"บัญชีคืนเงิน: {r[8] or '-'} / {r[9] or '-'} / {r[10] or '-'}\n"
            text+=f"จัดส่งถึง: {r[11] or 'ไม่ระบุ'} | โทร: {r[12] or '-'}\n"
            text+=f"ที่อยู่: {r[13] or '-'} {r[14] or ''} {r[15] or ''} {r[16] or ''} {r[17] or ''}\n\n"
            text+="\n".join([f"- {x[0]} x{x[1]} @ {x[2]:,.2f}" for x in items])
            self.detail.insert("1.0",text)
            self.show_slip(r[6])

    # def set_status: ตรวจออเดอร์และบันทึกสถานะใหม่ตามเงื่อนไขของระบบ
    def set_status(self,status):
        oid=self.selected_id()
        if not oid:return
        conn=get_connection(); cur=conn.cursor()
        cur.execute("SELECT order_status FROM orders WHERE id=?",(oid,)); old=cur.fetchone()[0]
        if old.startswith("สถานะถูกยกเลิก") or old in ("คืนเงินสำเร็จ", "ยกเลิกแล้ว"):
            conn.close(); messagebox.showwarning("ไม่อนุญาต","คำสั่งซื้อที่ลูกค้ายกเลิกแล้วไม่สามารถเปลี่ยนเป็นสถานะปกติได้"); return
        if (status == "กำลังจัดส่ง" and old != "ยืนยันคำสั่งซื้อ") or (status == "จัดส่งสำเร็จ" and old != "กำลังจัดส่ง"):
            conn.close(); messagebox.showwarning("สถานะ","ต้องยืนยันคำสั่งซื้อก่อนจัดส่ง"); return
        if old in ("จัดส่งสำเร็จ", "รับสินค้าแล้ว"):
            conn.close(); messagebox.showwarning("สถานะ", "คำสั่งซื้อนี้เสร็จสิ้นการจัดส่งแล้ว"); return
        cur.execute("UPDATE orders SET order_status=? WHERE id=?",(status,oid))
        conn.commit(); conn.close(); self.load()

    # def confirm_order: ยืนยันคำสั่งซื้อที่เลือกตามเงื่อนไขการชำระเงิน
    def confirm_order(self):
        oid=self.selected_id()
        if not oid:return
        conn=get_connection(); cur=conn.cursor()
        conn.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT order_status,payment_status FROM orders WHERE id=?",(oid,)); state=cur.fetchone()
        if not state or state[0] != "กำลังตรวจสอบ" or state[1] != "ชำระเงินแล้ว":
            conn.rollback(); conn.close(); messagebox.showwarning("ไม่อนุญาต","ยืนยันได้เฉพาะคำสั่งซื้อที่กำลังตรวจสอบและชำระเงินแล้ว"); return
        cur.execute("SELECT product_id,quantity,variant_id FROM order_items WHERE order_id=?",(oid,))
        items=cur.fetchall()
        for pid,qty,vid in items:
            cur.execute("SELECT stock FROM product_variants WHERE id=?" if vid is not None else "SELECT stock FROM products WHERE id=?",(vid if vid is not None else pid,)); stock=cur.fetchone()[0]
            if stock<qty:
                conn.close(); messagebox.showerror("Stock","Stock ไม่พอสำหรับการยืนยันคำสั่งซื้อ"); return
        for pid,qty,vid in items:
            if vid is not None:
                cur.execute("UPDATE product_variants SET stock=stock-? WHERE id=? AND stock>=?",(qty,vid,qty))
                if cur.rowcount==1:cur.execute("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?",(qty,pid,qty))
            else:cur.execute("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?",(qty,pid,qty))
            if cur.rowcount != 1:
                conn.rollback(); conn.close(); messagebox.showerror("Stock","Stock ไม่เพียงพอ"); return
        cur.execute("UPDATE orders SET order_status='ยืนยันคำสั่งซื้อ' WHERE id=?",(oid,))
        conn.commit(); conn.close(); messagebox.showinfo("สำเร็จ","ยืนยันคำสั่งซื้อและตัด Stock แล้ว"); self.load()

    # def shipping: เปลี่ยนสถานะคำสั่งซื้อเป็นกำลังจัดส่ง
    def shipping(self): self.set_status("กำลังจัดส่ง")

    # def delivered: เปลี่ยนสถานะคำสั่งซื้อเป็นจัดส่งสำเร็จ
    def delivered(self): self.set_status("จัดส่งสำเร็จ")

    # def confirm_payment: ตรวจรายการและยืนยันชำระ พร้อมจัดการตัด Stock ตามขั้นตอนในระบบ
    def confirm_payment(self):
        oid=self.selected_id()
        if not oid:return
        conn=get_connection(); cur=conn.cursor()
        # ล็อกข้อมูลระหว่างตรวจ เพื่อไม่ให้ยืนยันซ้อนกับการยกเลิกหรือคืนเงิน
        conn.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT order_status,payment_status FROM orders WHERE id=?",(oid,))
        state=cur.fetchone()
        if not state or state[0] in ("คืนเงินสำเร็จ", "ยกเลิกแล้ว") or state[1]!="รอตรวจสอบสลิป":
            conn.close(); messagebox.showwarning("การชำระเงิน","ไม่สามารถยืนยันการชำระเงินในสถานะนี้"); return
        latest=cur.execute("SELECT slip FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1",(oid,)).fetchone()
        if not latest or not latest[0]:
            conn.close();messagebox.showwarning("สลิป","ไม่มีสลิปแนบสำหรับตรวจสอบ");return
        candidate=Path(latest[0]);candidate=candidate if candidate.is_absolute() else ROOT/candidate
        if not candidate.is_file():
            conn.close();messagebox.showwarning("สลิป","ไม่พบไฟล์สลิป ไม่สามารถอนุมัติได้");return
        if not messagebox.askyesno("ยืนยันการชำระเงิน","ตรวจสอบชื่อบัญชีผู้รับ ยอดเงิน และสลิปแล้วใช่หรือไม่?"):
            conn.close();return
        cur.execute("UPDATE orders SET payment_status='ชำระเงินแล้ว' WHERE id=?",(oid,))
        cur.execute("UPDATE payments SET payment_status='ชำระเงินแล้ว' WHERE order_id=?",(oid,))
        # ออกเลขพร้อม snapshot ใน transaction เดียวกับการรับเงิน
        try:
            number=issue_receipt(conn,oid)
            conn.commit()
        except Exception as exc:
            conn.rollback();messagebox.showerror("ใบเสร็จ",str(exc));conn.close();return
        conn.close();self.load()
        if number:
            try:receipt_pdf(oid,admin=True)
            except Exception as exc:
                messagebox.showwarning("PDF",f"บันทึกการรับเงินและเลขใบเสร็จแล้ว แต่สร้าง PDF ไม่สำเร็จ เปิดใบเสร็จเพื่อลองใหม่: {exc}")

    # def view_receipt: เปิดใบเสร็จของ Order ที่ Admin เลือก
    def view_receipt(self):
        oid=self.selected_id()
        if oid is not None:show_receipt(self.root,oid,admin=True)

    # def refund_slip_dialog: เปิดฟอร์มเลือกสลิปหลักฐานสำหรับการคืนเงิน
    def refund_slip_dialog(self):
        oid=self.selected_id()
        if oid is None:return
        conn=get_connection()
        row=conn.execute("""SELECT o.order_status,o.refund_bank,o.refund_account_name,o.refund_account_number,
            r.amount,r.slip,r.refund_status FROM orders o LEFT JOIN refunds r ON r.order_id=o.id WHERE o.id=?""",(oid,)).fetchone()
        conn.close()
        if not row or not row[0].startswith("สถานะถูกยกเลิก") and row[0]!="คืนเงินสำเร็จ":
            messagebox.showwarning("คืนเงิน","เลือกออเดอร์ที่รอคืนเงินก่อน");return
        win=tk.Toplevel(self.root);win.title(f"คืนเงิน Order #{oid}");win.geometry("550x630")
        tk.Label(win,text=f"ยอดคืนเงิน {row[4]:,.2f} บาท",font=("Noto Sans Thai",16,"bold")).pack(pady=8)
        tk.Label(win,text=f"ธนาคาร: {row[1] or '-'}\nชื่อบัญชี: {row[2] or '-'}\nเลขบัญชี: {row[3] or '-'}",justify="left").pack(pady=5)
        tk.Label(win,text="โอนเงินผ่านแอปธนาคารก่อน แล้วจึงแนบสลิป",fg="#a16207").pack()
        chosen=tk.StringVar(value=row[5] or "")
        preview=tk.Label(win,text="ยังไม่มีสลิป",height=14);preview.pack(pady=8)
        # def show: โหลดภาพสลิปมาแสดงในหน้าต่างคืนเงิน
        def show(path):
            if not path:return
            candidate=Path(path);candidate=candidate if candidate.is_absolute() else ROOT/candidate
            if not candidate.is_file():return
            try:
                picture=photo(str(candidate),(350,330));preview.picture=picture
                preview.config(image=picture,text="",height=330)
            except Exception as exc:messagebox.showerror("สลิป",str(exc))
        show(chosen.get())
        # def choose: เปิดหน้าต่างเลือกไฟล์สลิป แล้วเก็บเส้นทางไฟล์ที่เลือก
        def choose():
            path=filedialog.askopenfilename(filetypes=[("รูปภาพ","*.jpg *.jpeg *.png *.webp")])
            if path:chosen.set(path);show(path)
        if row[6]!="คืนเงินสำเร็จ":
            ActionButton(win,text="เลือกสลิปคืนเงิน",command=choose).pack(pady=5)
            # def save: ตรวจหลักฐานและยืนยันโอนคืนแล้ว บันทึกสลิปคืนเงินและคืน Stock ตามเงื่อนไข
            def save():
                src=Path(chosen.get())
                if not src.is_file():messagebox.showwarning("สลิป","กรุณาเลือกไฟล์สลิป");return
                if not all(row[i] for i in (1,2,3)):
                    messagebox.showwarning("บัญชี","ออเดอร์นี้ไม่มีข้อมูลบัญชีคืนเงิน กรุณาติดต่อผู้ซื้อก่อนคืนเงิน");return
                if not messagebox.askyesno("ยืนยันคืนเงิน",f"ยืนยันว่าโอนคืน {row[4]:,.2f} บาท ไปยังบัญชี {row[3]} จริงแล้ว?"):return
                import shutil,uuid
                upload=ROOT/"uploads"/"refunds";upload.mkdir(parents=True,exist_ok=True)
                dest=upload/f"refund_{oid}_{uuid.uuid4().hex}{src.suffix.lower()}"
                try:
                    shutil.copy2(src,dest)
                    conn=get_connection();conn.execute("BEGIN IMMEDIATE")
                    state=conn.execute("SELECT order_status,payment_status FROM orders WHERE id=?",(oid,)).fetchone()
                    if not state or not state[0].startswith("สถานะถูกยกเลิก"):
                        conn.rollback();messagebox.showwarning("สถานะ","ออเดอร์ไม่อยู่ระหว่างคืนเงิน");return
                    # ต้องตรวจยอดรับเงินจริงก่อนบันทึกว่าคืนเงินเสร็จ
                    if state[1]!="ชำระเงินแล้ว":
                        conn.rollback();messagebox.showwarning("ตรวจยอดรับเงิน","กรุณาตรวจสลิปและยืนยันการชำระเงินก่อนคืนเงิน");return
                    changed=conn.execute("UPDATE refunds SET slip=?,refund_status='คืนเงินสำเร็จ',refund_date=CURRENT_TIMESTAMP WHERE order_id=? AND refund_status!='คืนเงินสำเร็จ'",(str(dest.relative_to(ROOT)),oid))
                    if changed.rowcount!=1:raise ValueError("ไม่พบรายการคืนเงินที่รอดำเนินการ")
                    conn.execute("UPDATE orders SET order_status='คืนเงินสำเร็จ' WHERE id=?",(oid,))
                    conn.commit();win.destroy();self.load();self.select_order(oid)
                    messagebox.showinfo("สำเร็จ","บันทึกสลิปคืนเงินให้ลูกค้าแล้ว")
                except Exception as exc:
                    try:conn.rollback()
                    except Exception:pass
                    messagebox.showerror("คืนเงิน",str(exc))
                finally:
                    try:conn.close()
                    except Exception:pass
            ActionButton(win,text="ยืนยันคืนเงินและส่งสลิปให้ลูกค้า",command=save,bg="#15803D",fg="white",activebackground="#166534",activeforeground="white").pack(pady=8)

    # def refund_done: บันทึกคืนเงินเสร็จพร้อมหลักฐาน และคืน Stock ตามเงื่อนไขป้องกันคืนซ้ำ
    def refund_done(self):
        self.refund_slip_dialog()

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        self.frame.destroy(); self.back_callback()
