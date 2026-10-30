"""Order overview and focused action pages; existing payment/stock guards retained."""
import tkinter as tk
from tkinter import messagebox,filedialog
from pathlib import Path
from datetime import date
from database.database import get_connection
from ui.admin.orders_base import AdminOrdersPage as OrderTransactions
from ui.admin.modern_style import *
from ui.image_utils import photo,ROOT

class AdminOrdersPage(OrderTransactions):
    def __init__(self,root,back_callback):
        self.root=root;self.back_callback=back_callback;self.oid=None
        self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True)
        main=chrome(self,'จัดการคำสั่งซื้อ','ตรวจสลิป ติดตามการจัดส่ง และจัดการคืนเงิน','orders')
        outer,canvas,body=scroll_area(main);outer.pack(fill='both',expand=True)
        self.work=tk.Frame(body,bg=BG);self.work.pack(fill='both',expand=True,padx=24,pady=(0,18))
        self.query=tk.StringVar();self.status_filter=tk.StringVar(value='ทั้งหมด');self.start=tk.StringVar();self.end=tk.StringVar();self.load()

    def selected_id(self):return self.oid

    def load(self):
        self.oid=None
        for w in self.work.winfo_children():w.destroy()
        with get_connection() as conn:
            self.rows=conn.execute('SELECT o.id,u.username,o.total_price,o.order_status,o.payment_status,o.order_date FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC').fetchall()
        metrics(self.work,[('ทั้งหมด',len(self.rows)),('รอตรวจสลิป',sum(r[4]=='รอตรวจสอบสลิป' for r in self.rows)),('เตรียมจัดส่ง',sum(r[3]=='ยืนยันคำสั่งซื้อ' for r in self.rows)),('รอคืนเงิน',sum(r[3].startswith('สถานะถูกยกเลิก') for r in self.rows))])
        card=panel(self.work);card.pack(fill='both',expand=True)
        tabs=tk.Frame(card,bg=WHITE);tabs.pack(fill='x',padx=14,pady=(14,8))
        menu(tabs,self.status_filter,['ทั้งหมด','รอตรวจสลิป','เตรียมจัดส่ง','กำลังจัดส่ง','จัดส่งสำเร็จ','รอคืนเงิน','คืนเงินสำเร็จ','ยกเลิกแล้ว'],lambda v:self.filter_orders(),200).pack(side='left')
        search=entry(tabs,self.query,260,'ค้นหา Order / ชื่อลูกค้า');search.pack(side='left',fill='x',expand=True,padx=8);search.bind('<Return>',lambda e:self.filter_orders())
        button(tabs,'ค้นหา',self.filter_orders,width=90).pack(side='left')
        dates=tk.Frame(card,bg=WHITE);dates.pack(fill='x',padx=14,pady=8)
        from ui.date_picker import pick_date
        for title,var in [('จาก',self.start),('ถึง',self.end)]:
            label(dates,title,13).pack(side='left',padx=(0,5));entry(dates,var,125).pack(side='left')
            button(dates,'ปฏิทิน',lambda v=var:pick_date(self.root,v),'secondary',width=85).pack(side='left',padx=5)
        button(dates,'กรองวันที่',self.filter_orders,'secondary',width=100).pack(side='left',padx=5)
        button(dates,'ล้าง',self.clear_filters,'secondary',width=70).pack(side='left')
        box,self.tree=table(card,[('id','Order',80),('user','ลูกค้า',130),('total','รวม VAT',120),('order','สถานะออเดอร์',230),('payment','การชำระเงิน',150),('date','วันที่',160)],10);box.pack(fill='both',expand=True,padx=14,pady=8)
        self.tree.bind('<<TreeviewSelect>>',self.select);self.tree.bind('<Double-1>',lambda e:self.open_action('details'))
        actions=tk.Frame(card,bg=WHITE);actions.pack(fill='x',padx=14,pady=10)
        for title,kind,color in [('ตรวจสลิป','slip','primary'),('จัดการ','manage','secondary'),('ดูรายละเอียด','details','secondary'),('คืนเงิน','refund','danger')]:button(actions,title,lambda k=kind:self.open_action(k),color,width=130).pack(side='left',padx=(0,8))
        pager=tk.Frame(card,bg=WHITE);pager.pack(fill='x',padx=14,pady=(0,14))
        button(pager,'‹ ก่อนหน้า',lambda:self.render(self.page-1),'secondary',width=120).pack(side='left')
        self.page_label=label(pager,'',14);self.page_label.pack(side='left',padx=16)
        button(pager,'ถัดไป ›',lambda:self.render(self.page+1),'secondary',width=120).pack(side='left')
        self.filter_orders()

    def clear_filters(self):
        self.query.set('');self.status_filter.set('ทั้งหมด');self.start.set('');self.end.set('');self.filter_orders()

    def filter_orders(self):
        from services.analytics import local_day
        try:
            start=date.fromisoformat(self.start.get()) if self.start.get() else None;end=date.fromisoformat(self.end.get()) if self.end.get() else None
            if start and end and start>end:raise ValueError()
        except ValueError:messagebox.showwarning('วันที่','ใช้วันที่ YYYY-MM-DD และวันที่เริ่มต้นไม่เกินวันที่สิ้นสุด');return
        q=self.query.get().strip().lower();status=self.status_filter.get()
        def matches(r):
            d=local_day(r[5]);match=status=='ทั้งหมด' or status=='รอตรวจสลิป' and r[4]=='รอตรวจสอบสลิป' or status=='เตรียมจัดส่ง' and r[3]=='ยืนยันคำสั่งซื้อ' or status=='รอคืนเงิน' and r[3].startswith('สถานะถูกยกเลิก') or status==r[3]
            return match and (not q or q in str(r[0]) or q in r[1].lower()) and (not start or d and d>=start) and (not end or d and d<=end)
        self.filtered=[r for r in self.rows if matches(r)];self.render(1)

    def render(self,page):
        pages=max(1,(len(self.filtered)+8)//9);self.page=max(1,min(pages,page));self.oid=None
        self.tree.delete(*self.tree.get_children())
        for r in self.filtered[(self.page-1)*9:self.page*9]:self.tree.insert('','end',iid=str(r[0]),values=(r[0],r[1],f'฿{r[2]:,.2f}',r[3],r[4],r[5]),tags=('empty' if r[3].startswith('สถานะถูกยกเลิก') else 'low' if r[4]=='รอตรวจสอบสลิป' else 'ok',))
        self.page_label.configure(text=f'หน้า {self.page} / {pages} · {len(self.filtered)} รายการ')

    def select(self,event=None):
        selected=self.tree.selection()
        if selected:self.oid=int(selected[0])

    def select_order(self,oid):self.oid=int(oid);self.open_action('details')

    def action_row(self,parent,oid):
        row=tk.Frame(parent,bg=WHITE);row.pack(fill='x',pady=14)
        for text,kind in [('ดูรายละเอียด','details'),('ตรวจสลิป','slip'),('จัดการ','manage'),('คืนเงิน','refund')]:button(row,text,lambda k=kind:self.open_action(k),'secondary',width=115).pack(side='left',padx=(0,8))

    def open_action(self,kind):
        oid=self.oid
        if not oid:messagebox.showinfo('คำสั่งซื้อ','กรุณาเลือกคำสั่งซื้อก่อน');return
        with get_connection() as conn:
            cur=conn.execute('SELECT o.*,u.username FROM orders o JOIN users u ON o.user_id=u.id WHERE o.id=?',(oid,));row=cur.fetchone()
            if row is None:messagebox.showwarning('คำสั่งซื้อ','ไม่พบคำสั่งซื้อ');self.load();return
            order=dict(zip([c[0] for c in cur.description],row))
            payment=conn.execute('SELECT slip FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1',(oid,)).fetchone()
        self.oid=oid
        for w in self.work.winfo_children():w.destroy()
        button(self.work,'‹ กลับรายการคำสั่งซื้อ',self.load,'secondary',width=220).pack(anchor='w',pady=(0,12))
        body=tk.Frame(self.work,bg=BG);body.pack(fill='both',expand=True)
        card=panel(body);card.pack(fill='x',padx=8,pady=8)
        form=tk.Frame(card,bg=WHITE,padx=24,pady=22);form.pack(fill='both',expand=True,padx=2,pady=2)
        titles={'details':'รายละเอียดคำสั่งซื้อ','slip':'ตรวจสลิปการชำระเงิน','manage':'จัดการคำสั่งซื้อ','refund':'คืนเงินให้ลูกค้า'}
        label(form,f'{titles[kind]} · Order #{oid}',24,True,anchor='w').pack(fill='x')
        label(form,f"ลูกค้า {order['username']} · {order['order_status']} · {order['payment_status']}",14,color=MUTED,anchor='w',wraplength=680).pack(fill='x',pady=(8,16))
        self.action_row(form,oid)
        if kind=='slip':
            label(form,f"ยอดที่ต้องชำระ ฿{order['total_price']:,.2f}",25,True,BLUE).pack(anchor='w',pady=12)
            self.slip_label=tk.Label(form,bg='#F5F7FB',text='ยังไม่มีสลิป');self.slip_label.pack(pady=10)
            self.show_slip(payment[0] if payment else None)
            actions=tk.Frame(form,bg=WHITE);actions.pack(pady=10)
            button(actions,'ขยายสลิป',self.open_slip,'secondary').pack(side='left',padx=5)
            button(actions,'อนุมัติการชำระเงิน',self.confirm_payment).pack(side='left',padx=5)
            button(actions,'ไม่ผ่าน',self.reject_payment,'danger').pack(side='left',padx=5)
        elif kind=='refund':self.refund_form(form,order)
        else:
            shipping=' '.join(str(order.get(k) or '') for k in ['shipping_address','shipping_subdistrict','shipping_district','shipping_province','shipping_postcode'])
            label(form,f"ผู้รับ: {order.get('shipping_name') or '-'}\nโทร: {order.get('shipping_phone') or '-'}\nที่อยู่: {shipping or '-'}",15,anchor='w',justify='left',wraplength=680).pack(fill='x',pady=12)
            from ui.order_previews import show_order_items
            button(form,'ดูสินค้าที่สั่ง',lambda:show_order_items(self.root,order['user_id'],oid),'secondary').pack(anchor='w',pady=6)
            if kind=='details':
                text=f"ราคาก่อน VAT: ฿{order['subtotal']:,.2f}\nVAT: ฿{order.get('vat_amount') or 0:,.2f}\nรวม: ฿{order['total_price']:,.2f}" if order.get('subtotal') is not None else f"ยอดเดิมรวม: ฿{order['total_price']:,.2f}"
                label(form,text,19,True,anchor='w',justify='left').pack(fill='x',pady=16)
                button(form,'เปิด / บันทึกใบเสร็จ',self.view_receipt,'secondary').pack(anchor='w',pady=8)
                with get_connection() as conn:
                    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='admin_shipments'").fetchone()
                    tracking=conn.execute('SELECT carrier,tracking_number FROM admin_shipments WHERE order_id=?',(oid,)).fetchone() if exists else None
                if tracking:label(form,f'ขนส่ง: {tracking[0]} · เลขพัสดุ: {tracking[1]}',15).pack(anchor='w',pady=12)
            else:
                if order['order_status']=='กำลังตรวจสอบ':button(form,'ยืนยันคำสั่งซื้อและตัดสต๊อก',self.confirm_order).pack(anchor='w',pady=14)
                if order['order_status']=='ยืนยันคำสั่งซื้อ':
                    label(form,'บริษัทขนส่ง',15).pack(anchor='w',pady=(12,4));self.carrier=entry(form,width=340);self.carrier.pack(anchor='w')
                    label(form,'เลขติดตามพัสดุ',15).pack(anchor='w',pady=(12,4));self.tracking=entry(form,width=340);self.tracking.pack(anchor='w')
                    button(form,'ยืนยันจัดส่ง',self.save_shipping).pack(anchor='w',pady=16)
                elif order['order_status']=='กำลังจัดส่ง':button(form,'บันทึกจัดส่งสำเร็จ',self.delivered).pack(anchor='w',pady=16)
                else:label(form,'ปุ่มดำเนินการจะแสดงตามสถานะปัจจุบันของคำสั่งซื้อ',14,color=MUTED).pack(anchor='w',pady=16)

    def save_shipping(self):
        carrier=self.carrier.get().strip();tracking=self.tracking.get().strip()
        if not carrier or not tracking:messagebox.showwarning('จัดส่ง','กรุณาระบุขนส่งและเลขติดตามพัสดุ');return
        if not messagebox.askyesno('ยืนยันจัดส่ง',f'บันทึก {carrier}\nเลขพัสดุ {tracking} และเปลี่ยนเป็นกำลังจัดส่ง?'):return
        with get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT order_status FROM orders WHERE id=?',(self.oid,)).fetchone()
            if not row or row[0]!='ยืนยันคำสั่งซื้อ':messagebox.showwarning('สถานะ','คำสั่งซื้อไม่ได้อยู่ระหว่างเตรียมจัดส่ง');return
            conn.execute('CREATE TABLE IF NOT EXISTS admin_shipments(order_id INTEGER PRIMARY KEY REFERENCES orders(id),carrier TEXT NOT NULL,tracking_number TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
            conn.execute('INSERT INTO admin_shipments(order_id,carrier,tracking_number) VALUES(?,?,?) ON CONFLICT(order_id) DO UPDATE SET carrier=excluded.carrier,tracking_number=excluded.tracking_number',(self.oid,carrier,tracking))
            conn.execute("UPDATE orders SET order_status='กำลังจัดส่ง' WHERE id=?",(self.oid,))
        self.load()

    def refund_form(self,parent,order):
        with get_connection() as conn:r=conn.execute('SELECT amount,slip,refund_status FROM refunds WHERE order_id=?',(self.oid,)).fetchone()
        if not r or not (order['order_status'].startswith('สถานะถูกยกเลิก') or order['order_status']=='คืนเงินสำเร็จ'):
            label(parent,'ออเดอร์นี้ไม่มีรายการคืนเงินที่รอดำเนินการ',16).pack(pady=20);return
        label(parent,f'ยอดคืนเงิน ฿{r[0]:,.2f}',28,True,'#B82A3C').pack(anchor='w',pady=12)
        label(parent,f"ธนาคาร: {order.get('refund_bank') or '-'}\nชื่อบัญชี: {order.get('refund_account_name') or '-'}\nเลขบัญชี: {order.get('refund_account_number') or '-'}",16,anchor='w',justify='left').pack(fill='x',pady=12)
        label(parent,'โอนเงินผ่านธนาคารก่อน แล้วแนบหลักฐานเพื่อบันทึกการคืนเงิน',14,color='#996000',wraplength=650).pack(anchor='w',pady=10)
        self.refund_path=tk.StringVar(value=r[1] or '')
        preview=tk.Label(parent,bg=WHITE);preview.pack(pady=8)
        def show():
            if self.refund_path.get():
                image=photo(self.refund_path.get(),(320,260));preview.configure(image=image);preview.image=image
        def choose():
            path=filedialog.askopenfilename(filetypes=[('รูปภาพ','*.jpg *.jpeg *.png *.webp')])
            if path:self.refund_path.set(path);show()
        show()
        if r[2]!='คืนเงินสำเร็จ':
            button(parent,'+ แนบหลักฐานคืนเงิน',choose,'secondary').pack(anchor='w',pady=10)
            button(parent,'ตรวจสอบและยืนยันว่าคืนเงินแล้ว',lambda:self.save_refund(order,r[0]),'danger').pack(anchor='w',pady=10)

    def save_refund(self,order,amount):
        from PIL import Image
        import shutil,uuid
        path=self.refund_path.get();src=Path(path);src=src if src.is_absolute() else ROOT/src
        try:
            with Image.open(src) as im:im.verify()
        except (OSError,ValueError):messagebox.showwarning('หลักฐาน','กรุณาเลือกภาพหลักฐานคืนเงินที่เปิดได้');return
        if not all(order.get(k) for k in ('refund_bank','refund_account_name','refund_account_number')):messagebox.showwarning('บัญชี','ไม่พบข้อมูลบัญชีรับเงินคืนครบถ้วน กรุณาติดต่อลูกค้า');return
        if not messagebox.askyesno('ยืนยันคืนเงิน',f"โอนคืน ฿{amount:,.2f} ไปยัง {order['refund_account_number']} จริงแล้วใช่หรือไม่?"):return
        dest=None
        try:
            with get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                state=conn.execute('SELECT order_status,payment_status FROM orders WHERE id=?',(self.oid,)).fetchone()
                if not state or not state[0].startswith('สถานะถูกยกเลิก') or state[1]!='ชำระเงินแล้ว':
                    raise ValueError('ต้องเป็นออเดอร์รอคืนเงินและยืนยันยอดรับเงินจริงแล้ว กรุณาตรวจสลิปก่อน')
                directory=ROOT/'uploads/refunds';directory.mkdir(parents=True,exist_ok=True);dest=directory/f'refund_{self.oid}_{uuid.uuid4().hex}{src.suffix.lower()}';shutil.copy2(src,dest)
                result=conn.execute("UPDATE refunds SET slip=?,refund_status='คืนเงินสำเร็จ',refund_date=CURRENT_TIMESTAMP WHERE order_id=? AND refund_status!='คืนเงินสำเร็จ'",(str(dest.relative_to(ROOT)),self.oid))
                if result.rowcount!=1:raise ValueError('ไม่พบรายการคืนเงินที่รอดำเนินการ')
                conn.execute("UPDATE orders SET order_status='คืนเงินสำเร็จ' WHERE id=?",(self.oid,))
        except Exception as exc:
            if dest:dest.unlink(missing_ok=True)
            messagebox.showwarning('คืนเงิน',str(exc));return
        messagebox.showinfo('สำเร็จ','บันทึกการคืนเงินและหลักฐานแล้ว');self.load()
