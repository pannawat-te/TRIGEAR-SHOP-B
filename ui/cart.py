from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: ตะกร้าในหน่วยความจำ: เก็บสินค้าแยกบัญชีและไซซ์ พร้อมตรวจ Stock
from ui.customer_style import header, scroll_body, polish
import tkinter as tk
from tkinter import messagebox, ttk
from database.database import get_connection
from ui.image_utils import photo
from services.pricing import amount,totals


# คลาส CartPage: เก็บข้อมูลและพฤติกรรมของ ตะกร้าในหน่วยความจำ
class CartPage:
    carts = {}
    unchecked = {}
    loaded_users=set()

    # def load_saved: โหลดตะกร้าที่บันทึกไว้เมื่อเริ่มบัญชีหรือเปิดหน้าใหม่
    @classmethod
    def load_saved(cls,user_id):
        from database.cart_store import load_cart
        cls.carts[user_id],cls.unchecked[user_id]=load_cart(user_id)
        cls.loaded_users.add(user_id)

    # def ensure_loaded: โหลดครั้งแรกก่อนอ่านจำนวนหรือเพิ่มสินค้า
    @classmethod
    def ensure_loaded(cls,user_id):
        if user_id not in cls.loaded_users:cls.load_saved(user_id)

    # def persist: บันทึกทันที ไม่ต้องรอปิดโปรแกรม ถ้าล้มเหลวคืนค่าจากฐานข้อมูล
    @classmethod
    def persist(cls,user_id):
        from database.cart_store import save_cart
        try:save_cart(user_id,cls.carts.get(user_id,{}),cls.unchecked.get(user_id,set()))
        except Exception:
            cls.load_saved(user_id);raise


    # def selected_items: คืนเฉพาะรายการที่ติ๊กไว้ ค่าเริ่มต้นเลือกสินค้าทั้งหมด
    @classmethod
    def selected_items(cls,user_id):
        cls.ensure_loaded(user_id)
        return {k:q for k,q in cls.carts.get(user_id,{}).items() if k not in cls.unchecked.get(user_id,set())}

    # def total_quantity: รวมจำนวนชิ้นในตะกร้าโดยไม่เกี่ยวกับช่องติ๊ก
    @classmethod
    def total_quantity(cls,user_id):
        cls.ensure_loaded(user_id)
        return sum(cls.carts.get(user_id,{}).values())

    # def complete_purchase: นำเฉพาะรายการที่สั่งสำเร็จออก รายการอื่นคงเดิม
    @classmethod
    def complete_purchase(cls,user_id,purchased):
        cart=cls.carts.get(user_id,{})
        for key,qty in purchased.items():
            remaining=cart.get(key,0)-qty
            if remaining>0:cart[key]=remaining
            else:cart.pop(key,None);cls.unchecked.setdefault(user_id,set()).discard(key)

    MAX_PER_PRODUCT = 10
    MAX_DISTINCT_PRODUCTS = 30

    @classmethod
    def distinct_count(cls,user_id):
        cls.ensure_loaded(user_id)
        return len({k[0] if isinstance(k,tuple) else k for k in cls.carts.get(user_id,{})})

    @classmethod
    def can_add_product(cls,user_id,pid):
        cls.ensure_loaded(user_id)
        ids={k[0] if isinstance(k,tuple) else k for k in cls.carts.get(user_id,{})}
        return pid in ids or len(ids)<cls.MAX_DISTINCT_PRODUCTS


    # def product_total: รวมจำนวนสินค้าชนิดเดียวกันทุกไซซ์ในตะกร้า
    @classmethod
    def product_total(cls,user_id,product_id):
        cls.ensure_loaded(user_id)
        return sum(q for k,q in cls.carts.get(user_id,{}).items()
                   if (k[0] if isinstance(k,tuple) else k)==product_id)

    # def validate_limits: ตรวจจำนวนรวมทุกไซซ์ก่อนชำระเงิน
    @classmethod
    def validate_limits(cls,user_id,conn,items=None):
        cart=cls.carts.get(user_id,{}) if items is None else items
        if len({k[0] if isinstance(k,tuple) else k for k in cart})>cls.MAX_DISTINCT_PRODUCTS:
            raise ValueError("ตะกร้ามีสินค้าแตกต่างกันได้สูงสุด 30 อย่าง กรุณานำบางรายการออก")
        for key,qty in cart.items():
            if type(qty) is not int or qty<1:raise ValueError("จำนวนสินค้าต้องเป็นจำนวนเต็มตั้งแต่ 1 ชิ้น")
            pid=key[0] if isinstance(key,tuple) else key
            total=sum(q for k,q in cart.items() if (k[0] if isinstance(k,tuple) else k)==pid)
            if total>cls.MAX_PER_PRODUCT:raise ValueError("สินค้าชนิดเดียวรวมทุกไซซ์ได้ไม่เกิน 10 ชิ้น")
            row=conn.execute("SELECT stock FROM products WHERE id=?",(pid,)).fetchone()
            if not row or total>row[0]:raise ValueError("จำนวนรวมทุกไซซ์เกิน Stock ที่เหลือ")

    # def remaining: คำนวณจำนวนที่เพิ่มได้โดยหักจำนวนในตะกร้าและตรวจ Stock ไซซ์
    @classmethod
    def remaining(cls,user_id,pid,vid=None):
        if not cls.can_add_product(user_id,pid):return 0
        conn=get_connection()
        try:
            row=conn.execute("SELECT size_type,stock FROM products WHERE id=?",(pid,)).fetchone()
            if not row:return 0
            total=cls.product_total(user_id,pid)
            available=min(cls.MAX_PER_PRODUCT-total,row[1]-total)
            if row[0]!='none':
                v=conn.execute("SELECT stock FROM product_variants WHERE id=? AND product_id=?",(vid,pid)).fetchone()
                if not v:return 0
                available=min(available,v[0]-cls.carts.get(user_id,{}).get((pid,vid),0))
            return max(0,available)
        finally:conn.close()


    # def add_item: ตรวจสินค้า/ไซซ์และ Stock ก่อนเพิ่มจำนวนลงตะกร้าของ user_id
    @classmethod
    def add_item(cls,user_id,product_id,variant_id=None,quantity=1):
        if type(quantity) is not int or quantity<1:return False
        if quantity>cls.remaining(user_id,product_id,variant_id):return False
        conn=get_connection()
        kind=conn.execute("SELECT size_type,stock FROM products WHERE id=?",(product_id,)).fetchone()
        if not kind:conn.close();return False
        if kind[0]!='none':
            row=conn.execute("SELECT stock FROM product_variants WHERE id=? AND product_id=?",(variant_id,product_id)).fetchone()
            if not row:conn.close();return False
            available=row[0]
        else:available=kind[1];variant_id=None
        conn.close()
        key=(product_id,variant_id)
        cart=cls.carts.setdefault(user_id,{})
        if cart.get(key,0)+quantity>available:return False
        if key not in cart:cls.unchecked.setdefault(user_id,set()).discard(key)
        cart[key]=cart.get(key,0)+quantity
        cls.persist(user_id)
        return True

    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root, user_id, username, back_callback):
        self.ensure_loaded(user_id)
        self.root=root; self.user_id=user_id; self.username=username; self.back_callback=back_callback
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True)
        self.build()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        from ui.shop_style import customer_header,heading,body,card,text,button,money_summary,two_columns,BG,WHITE,MUTED
        self.cart_button=customer_header(self.frame,self.user_id,self,active='cart')
        heading(self.frame,'ตะกร้าสินค้า','เลือกสินค้าที่ต้องการสั่งซื้อ • สูงสุด 30 อย่าง และ 10 ชิ้นต่อสินค้า รวมทุกไซส์')
        content=body(self.frame)
        shell=tk.Frame(content,bg=BG);shell.pack(fill='x')
        left=card(shell);right=tk.Frame(shell,bg=BG)
        two_columns(shell,left,right,ratio=(7,3),threshold=1200)
        toolbar=tk.Frame(left,bg=WHITE);toolbar.pack(fill='x',pady=(0,12))
        self.all_selected=tk.BooleanVar(value=True)
        CheckBox(toolbar,text='เลือกทั้งหมด',variable=self.all_selected,command=self.toggle_all,bg=WHITE,fg='#14253D',selectcolor='#EEEDFF',font=('Noto Sans Thai',12,'bold')).pack(side='left')
        self.selected_label=text(left,'',10,color=MUTED);self.selected_label.pack(anchor='w',pady=(0,12))
        self.list_frame=tk.Frame(left,bg=WHITE);self.list_frame.pack(fill='x')
        summary,labels=money_summary(right,0,0,0);summary.pack(fill='x')
        self.subtotal_label,self.vat_label,self.total_label=labels
        self.checkout_button=button(summary,'ดำเนินการชำระเงิน',self.checkout);self.checkout_button.pack(fill='x',pady=7)
        button(summary,'เลือกซื้อสินค้าต่อ',self.back,'secondary').pack(fill='x',pady=7)
        self.refresh()

    # def open_product: เปิดรายละเอียดสินค้าจากรายการในตะกร้า
    def open_product(self,pid):
        from ui.customer_home import CustomerHome
        self.frame.destroy()
        home=CustomerHome(self.root,self.user_id,self.username,self.back_callback)
        home.back_from_details=lambda: (home.frame.destroy(),CartPage(self.root,self.user_id,self.username,self.back_callback))
        home.details(pid)

    # def change_size: ย้ายรายการในตะกร้าไปไซซ์ใหม่ พร้อมตรวจ Stock และจำนวนที่รวมกัน
    def change_size(self,key,new_vid):
        cart=self.carts.setdefault(self.user_id,{})
        pid,old_vid=key
        if new_vid==old_vid:return
        qty=cart.get(key,0);new_key=(pid,new_vid)
        conn=get_connection();row=conn.execute("SELECT stock FROM product_variants WHERE id=? AND product_id=?",(new_vid,pid)).fetchone();conn.close()
        if not row or cart.get(new_key,0)+qty>row[0]:
            messagebox.showwarning("Stock","ไซซ์ใหม่มีสินค้าไม่พอ");self.refresh();return
        unchecked=self.unchecked.setdefault(self.user_id,set());was_unchecked=key in unchecked
        merging=new_key in cart
        cart.pop(key,None);unchecked.discard(key);cart[new_key]=cart.get(new_key,0)+qty
        if not merging and was_unchecked:unchecked.add(new_key)
        self.refresh()

    # def refresh: โหลดและวาดรายการใหม่ เพื่อให้หน้าจอตรงกับข้อมูลล่าสุด
    def refresh(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        cart=self.carts.get(self.user_id,{})
        total=amount(0)
        if not cart:
            tk.Label(self.list_frame,text="ตะกร้าว่าง").pack(pady=30)
        for key,qty in list(cart.items()):
            pid,vid=key if isinstance(key,tuple) else (key,None)
            conn=get_connection(); cur=conn.cursor()
            cur.execute("SELECT name,price,stock,image FROM products WHERE id=?",(pid,))
            p=cur.fetchone(); conn.close()
            if not p:
                cart.pop(key,None); continue
            if vid is not None:
                c=get_connection();r=c.execute("SELECT size,stock FROM product_variants WHERE id=?",(vid,)).fetchone();c.close()
                if not r:cart.pop(key,None);continue
                label_size=f" (ไซซ์ {r[0]})";available=r[1]
            else:label_size="";available=p[2]
            if available<=0:
                cart.pop(key,None);continue
            if qty>available:
                cart[key]=available;qty=available
            chosen=key not in self.unchecked.get(self.user_id,set())
            subtotal=amount(p[1])*qty
            if chosen:total+=subtotal
            from ui.shop_style import text,button,WHITE,MUTED,BORDER
            row=tk.Frame(self.list_frame,bg=WHITE,padx=0,pady=16);row.pack(fill='x')
            tk.Frame(self.list_frame,bg=BORDER,height=1).pack(fill='x')
            row.columnconfigure(2,weight=1)
            for col,width in [(0,26),(1,90),(2,140),(3,118),(4,105),(5,55)]:row.columnconfigure(col,minsize=width)
            tick=tk.BooleanVar(value=chosen)
            CheckBox(row,variable=tick,bg=WHITE,selectcolor='#EEEDFF',command=lambda k=key,v=tick:self.toggle_item(k,v.get())).grid(row=0,column=0,rowspan=2)
            picture=photo(p[3],(84,84));label=tk.Label(row,image=picture,bg=WHITE);label.image=picture;label.grid(row=0,column=1,rowspan=2,padx=(0,8))
            title=tk.Label(row,text=p[0],bg=WHITE,fg='#14253D',font=('Noto Sans Thai',11,'bold'),anchor='w',justify='left',wraplength=180,cursor='hand2')
            title.bind('<Button-1>',lambda e,x=pid:self.open_product(x))
            title.grid(row=0,column=2,sticky='ew',padx=(0,8))

            if vid is not None:
                conn=get_connection();variants=conn.execute('SELECT id,size,stock FROM product_variants WHERE product_id=? ORDER BY id',(pid,)).fetchall();conn.close()
                mapping={f'{size} · เหลือ {stock}':v for v,size,stock in variants if stock>0 or v==vid}
                choice=tk.StringVar(value=next((name for name,v in mapping.items() if v==vid),''))
                combo=option_menu(row,choice,list(mapping),width=150,command=lambda value,k=key,m=mapping:self.change_size(k,m[value]))
                combo.grid(row=1,column=2,sticky='w',pady=(7,0))

            else:text(row,f'฿{p[1]:,.2f} / ชิ้น',10,color=MUTED).grid(row=1,column=2,sticky='w')
            controls=tk.Frame(row,bg=WHITE);controls.grid(row=0,column=3,padx=4)
            for symbol,delta in [('−',-1),('+',1)]:
                if delta==1:tk.Label(controls,text=str(qty),width=3,bg=WHITE,font=('Noto Sans Thai',11,'bold')).pack(side='left')
                button(controls,symbol,lambda k=key,d=delta:self.change(k,d),'secondary',width=1,
                       state='normal' if delta<0 or self.remaining(self.user_id,pid,vid)>0 else 'disabled').pack(side='left')
            text(row,f'เหลือ {available} ชิ้น',9,color=MUTED).grid(row=1,column=3,pady=(6,0))
            text(row,f'฿{subtotal:,.2f}',12,True).grid(row=0,column=4,padx=5)
            button(row,'ลบ',lambda k=key:self.remove(k),'danger',width=2).grid(row=0,column=5,padx=(6,0))
        selected=self.selected_items(self.user_id)
        self.unchecked.setdefault(self.user_id,set()).intersection_update(cart)
        self.persist(self.user_id)
        self.all_selected.set(bool(cart) and len(selected)==len(cart))
        self.selected_label.config(text=f"{self.distinct_count(self.user_id)}/30 อย่าง • เลือกแล้ว {sum(selected.values())} ชิ้น / ทั้งหมด {sum(cart.values())} ชิ้น")
        self.checkout_button.config(state="normal" if selected else "disabled")
        base,vat,total=totals([(total,1)])
        self.subtotal_label.config(text=f"฿{base:,.2f}")
        self.vat_label.config(text=f"฿{vat:,.2f}")
        self.total_label.config(text=f"฿{total:,.2f}")
        from ui.shop_style import refresh_badges
        refresh_badges(self.root,self.user_id)


    # def toggle_item: เปลี่ยนช่องติ๊กและคำนวณยอดใหม่ทันที
    def toggle_item(self,key,selected):
        unchecked=self.unchecked.setdefault(self.user_id,set())
        if selected:unchecked.discard(key)
        else:unchecked.add(key)
        self.refresh()

    # def toggle_all: เลือกหรือยกเลิกทั้งตะกร้า แล้วคำนวณยอดใหม่
    def toggle_all(self):
        self.unchecked[self.user_id]=set() if self.all_selected.get() else set(self.carts.get(self.user_id,{}))
        self.refresh()

    # def change: เพิ่มหรือลดจำนวนสินค้าในตะกร้าตาม delta โดยตรวจ Stock
    def change(self,key,delta):
        pid,vid=key if isinstance(key,tuple) else (key,None)
        cart=self.carts.setdefault(self.user_id,{})
        conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT stock FROM products WHERE id=?",(pid,)); p=cur.fetchone(); conn.close()
        if not p: return
        if vid is not None:
            c=get_connection();v=c.execute("SELECT stock FROM product_variants WHERE id=?",(vid,)).fetchone();c.close()
            if not v:return
            available=v[0]
        else:available=p[0]
        new=cart.get(key,0)+delta
        if new<=0: cart.pop(key,None)
        elif delta>0 and delta>self.remaining(self.user_id,pid,vid): messagebox.showwarning("จำนวนสินค้า","เพิ่มได้ไม่เกิน 10 ชิ้นต่อสินค้า รวมทุกไซซ์ และไม่เกิน Stock")
        elif new>available: messagebox.showwarning("Stock","จำนวนเกิน Stock ที่มี")
        else: cart[key]=new
        self.refresh()

    # def remove: ลบรายการที่เลือกออกจากตะกร้าหรือฟอร์มของหน้านี้
    def remove(self,key):
        self.carts.get(self.user_id,{}).pop(key,None); self.refresh()

    # def checkout: ตรวจตะกร้า แล้วเปิดหน้ากรอกข้อมูลชำระเงิน
    def checkout(self):
        from ui.checkout import CheckoutPage
        if not self.selected_items(self.user_id):
            messagebox.showwarning("ตะกร้า","กรุณาเลือกสินค้าที่ต้องการสั่งซื้อ")
            return
        self.frame.destroy(); CheckoutPage(self.root,self.user_id,self.username,self.back_callback)

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        self.frame.destroy(); self.back_callback()
