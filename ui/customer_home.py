# ไฟล์นี้: หน้าร้านลูกค้า: ค้นหา หมวดหมู่ รายละเอียดสินค้า ภาพ และเลือกไซซ์
from ui.customer_style import entry as customer_entry, header, scroll_body, polish
import tkinter as tk
import customtkinter as ctk
from ui.storefront_style import BG,WHITE,NAVY,BLUE,MUTED,BORDER,panel,button,label,scroll_area
from ui.slide_gallery import contained_image
from tkinter import ttk, messagebox
import re
import webbrowser

from database.database import get_connection
from ui.image_utils import photo
from ui.gallery import images_for
from ui.cart import CartPage
from ui.orders import OrdersPage
from ui.account import AccountPage


# คลาส CustomerHome: เก็บข้อมูลและพฤติกรรมของ หน้าร้านลูกค้า
class CustomerHome:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root, user_id, username, logout_callback):
        self.root = root
        self.user_id = user_id
        CartPage.load_saved(user_id)
        self.username = username
        self.logout_callback = getattr(root,'_logout_callback',None) or logout_callback
        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        self.sort_value=tk.StringVar(value="ค่าเริ่มต้น")
        self.current_products=[]
        self.featured_mode=False
        self.build()
        self.show_products()

    # def clear_content: ลบวิดเจ็ตในส่วนเนื้อหาก่อนวาดหน้าร้านใหม่
    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def _build_nav(self,parent):
        nav=panel(parent);nav.pack(fill='x',padx=20,pady=(16,12));nav.columnconfigure(1,weight=1)
        try:
            from ui.brand import logo
            picture=logo((108,48));brand=tk.Label(nav,image=picture,bg=WHITE);brand.image=picture
        except (OSError,ValueError):brand=tk.Label(nav,text='TRI GEAR',bg=WHITE,fg=NAVY,font=('Noto Sans Thai',19,'bold'))
        brand.grid(row=0,column=0,padx=(20,12),pady=12)
        session=ctk.CTkFrame(nav,fg_color='transparent');session.grid(row=0,column=2,padx=(8,16),pady=12)
        button(session,'ออกจากระบบ',self.logout_callback,'danger',width=112).pack(side='right',padx=(8,0))
        from ui.avatar import avatar_image
        conn=get_connection()
        try:row=conn.execute('SELECT profile_image FROM users WHERE id=?',(self.user_id,)).fetchone()
        finally:conn.close()
        image=ctk.CTkImage(light_image=avatar_image(row[0] if row else None),size=(40,40))
        ctk.CTkButton(session,image=image,text='',command=self.account,width=44,height=44,corner_radius=22,
            fg_color=WHITE,hover_color='#F0EFFF').pack(side='right',padx=4)
        menu=ctk.CTkFrame(nav,fg_color='transparent');menu.grid(row=0,column=1,sticky='e',pady=12)
        count=button(menu,f'ตะกร้า ({CartPage.total_quantity(self.user_id)})',self.cart,'secondary',width=116)
        count._store_cart_badge=True;count.pack(side='right',padx=5);self.cart_button=count
        button(menu,'Contact',self.contact,'secondary',width=82).pack(side='right',padx=5)
        button(menu,'คำสั่งซื้อ',self.orders,'secondary',width=100).pack(side='right',padx=5)
        button(menu,'สินค้าทั้งหมด',self._go_storefront,'muted',width=126).pack(side='right',padx=5)
        state={'wide':None}
        def adapt(e):
            wide=e.width>=900*ctk.ScalingTracker.get_widget_scaling(nav)
            if state['wide']==wide:return
            state['wide']=wide
            menu.grid_configure(row=0 if wide else 1,column=1 if wide else 0,columnspan=1 if wide else 3,
                sticky='e',padx=0 if wide else 12,pady=12 if wide else (0,12))
        nav.bind('<Configure>',adapt,add='+')

    def _go_storefront(self):
        if hasattr(self,'detail_page') and self.detail_page.winfo_exists():CustomerHome.back_from_details(self)
        self.filter_category_id(None)

    def _mark_category(self,cid):
        self.category_value.set(-1 if cid==-1 else cid or 0)
        for key,b in self.category_buttons.items():
            active=key==self.category_value.get()
            b.configure(fg_color='#EEEDFF' if active else WHITE,text_color=BLUE if active else MUTED)

    def build(self):
        self.frame.configure(bg=BG);self._build_nav(self.frame)
        body=tk.Frame(self.frame,bg=BG);body.pack(fill='both',expand=True,padx=20,pady=(0,16))
        side=panel(body,width=208);side.pack(side='left',fill='y',padx=(0,18));side.pack_propagate(False)
        label(side,'หมวดหมู่สินค้า',17,True).pack(anchor='w',padx=18,pady=(20,14))
        outer,canvas,cats=scroll_area(side,WHITE);outer.pack(fill='both',expand=True,padx=8,pady=(0,12))
        self.category_value=tk.IntVar(value=-1);self.category_buttons={}
        def add(title,cid,indent=0):
            def select():
                self._mark_category(cid)
                if cid==-1:self.show_products()
                else:self.filter_category_id(cid or None)
            b=ctk.CTkButton(cats,text=title,command=select,anchor='w',height=38,corner_radius=9,
                fg_color=WHITE,text_color=MUTED,hover_color='#F4F3FF',font=('Noto Sans Thai',14),width=150)
            if b._text_label is not None:
                b._text_label.configure(wraplength=145,justify='left')
                b.configure(height=max(38,b._text_label.winfo_reqheight()+12))
            b.pack(fill='x',padx=(indent+4,4),pady=3);self.category_buttons[cid]=b
        add('สินค้าแนะนำ',-1);add('สินค้าทั้งหมด',0)
        conn=get_connection()
        try:rows=conn.execute('SELECT id,name,parent_id FROM categories ORDER BY id').fetchall()
        finally:conn.close()
        for cid,name,parent in rows:
            if parent is not None:continue
            add(name,cid)
            for sid,sub,par in rows:
                if par==cid:add('ทั้งหมดในหมวดนี้' if sub==name else sub,sid,10)
        self._mark_category(-1)
        right=tk.Frame(body,bg=BG);right.pack(side='left',fill='both',expand=True)
        label(right,'อุปกรณ์สำหรับทุกเป้าหมาย',28,True,anchor='w').pack(fill='x',pady=(4,2))
        label(right,'ค้นหาอุปกรณ์วิ่ง ปั่น ว่าย ที่เหมาะกับคุณ',14,color=MUTED,anchor='w').pack(fill='x',pady=(0,14))
        search=ctk.CTkFrame(right,fg_color='transparent');search.pack(fill='x',pady=(0,14))
        self.search=ctk.CTkEntry(search,height=44,corner_radius=11,border_width=1,border_color=BORDER,
            fg_color=WHITE,text_color=NAVY,placeholder_text='ค้นหาสินค้า แบรนด์ หรือรายละเอียด...',font=('Noto Sans Thai',15))
        self.search.pack(side='left',fill='x',expand=True,padx=(0,8));self.search.bind('<Return>',lambda e:self.search_products())
        button(search,'ค้นหา',self.search_products,width=92).pack(side='right')
        self.content=tk.Frame(right,bg=BG);self.content.pack(fill='both',expand=True)

    # def filter_category_id: กรองรายการสินค้าตามรหัสหมวดหมู่ที่เลือก
    def filter_category_id(self, cid):
        self._mark_category(cid)
        conn=get_connection()
        query="SELECT DISTINCT p.id,p.name,COALESCE(b.name,'-'),p.price,p.stock,p.description,p.is_featured,p.image FROM products p LEFT JOIN brands b ON p.brand_id=b.id"
        params=()
        if cid is not None:
            query+=" JOIN product_categories pc ON p.id=pc.product_id WHERE pc.category_id IN (WITH RECURSIVE descendants(id) AS (SELECT id FROM categories WHERE id=? UNION ALL SELECT c.id FROM categories c JOIN descendants d ON c.parent_id=d.id) SELECT id FROM descendants)"
            params=(cid,)
        rows=conn.execute(query+" ORDER BY p.id DESC",params).fetchall();conn.close()
        self.show_products(rows)

    # def show_products: แสดงการ์ดสินค้าและปุ่มเปิดรายละเอียด/เพิ่มลงตะกร้า
    def show_products(self,products=None,page=1,featured_mode=False):
        self.clear_content()
        if products is None:
            conn=get_connection()
            try:products=conn.execute("SELECT p.id,p.name,COALESCE(b.name,'-'),p.price,p.stock,p.description,p.is_featured,p.image FROM products p LEFT JOIN brands b ON p.brand_id=b.id ORDER BY p.is_featured DESC,p.id DESC").fetchall()
            finally:conn.close()
            featured=[p for p in products if p[6]]
            if featured:products=featured[:6];featured_mode=True
        self.current_products=list(products);self.featured_mode=featured_mode
        toolbar=ctk.CTkFrame(self.content,fg_color='transparent');toolbar.pack(fill='x',pady=(0,8))
        label(toolbar,'สินค้าแนะนำ' if featured_mode else 'รายการสินค้า',18,True).pack(side='left')
        ctk.CTkOptionMenu(toolbar,variable=self.sort_value,values=['ค่าเริ่มต้น','ราคา: จากน้อยไปมาก','ราคา: จากมากไปน้อย'],
            command=lambda value:self.show_products(self.current_products,1,self.featured_mode),width=220,height=38,
            corner_radius=9,fg_color=WHITE,button_color='#E7EAF4',button_hover_color='#D9DFF0',text_color=NAVY,
            font=('Noto Sans Thai',13),dropdown_font=('Noto Sans Thai',13),dropdown_fg_color=WHITE,dropdown_text_color=NAVY).pack(side='right')
        from ui.pagination import page_items
        source=list(products);all_products=self.sorted_products(source,self.sort_value.get())
        products,current,pages=page_items(all_products,page)
        self.page_number=current
        if not products:label(self.content,'ไม่พบสินค้า ลองเปลี่ยนคำค้นหรือหมวดหมู่',17,color=MUTED).pack(pady=50);return
        pager=ctk.CTkFrame(self.content,fg_color='transparent');pager.pack(side='bottom',fill='x',pady=(10,0))
        button(pager,'‹ ก่อนหน้า',lambda:self.show_products(source,current-1,featured_mode),'secondary',width=112,state='normal' if current>1 else 'disabled').pack(side='left')
        label(pager,f'หน้า {current} / {pages} · {len(all_products)} สินค้า',13,color=MUTED).pack(side='left',padx=12)
        button(pager,'ถัดไป ›',lambda:self.show_products(source,current+1,featured_mode),'secondary',width=112,state='normal' if current<pages else 'disabled').pack(side='right')
        outer,canvas,inner=scroll_area(self.content);outer.pack(fill='both',expand=True)
        self._product_canvas=canvas;self._cards=[]
        for i,p in enumerate(products):
            c=panel(inner);c.grid(row=i//3,column=i%3,sticky='nsew',padx=5,pady=6)
            pic=ctk.CTkLabel(c,text='',height=190);pic.pack(fill='x',padx=12,pady=(12,8));pic.bind('<Button-1>',lambda e,pid=p[0]:self.details(pid))
            area=tk.Frame(c,bg=WHITE,height=62);area.pack(fill='x',padx=14);area.pack_propagate(False)
            title=tk.Label(area,text=p[1],font=('Noto Sans Thai',12,'bold'),bg=WHITE,fg=NAVY,justify='center',anchor='center',wraplength=220)
            title.pack(fill='both',expand=True)
            label(c,f'{p[2]} · '+(f'เหลือ {p[4]} ชิ้น' if p[4] else 'สินค้าหมด'),12,color=MUTED).pack(pady=(3,2))
            label(c,f'฿{p[3]:,.2f}',21,True,BLUE).pack(pady=(0,10))
            actions=ctk.CTkFrame(c,fg_color='transparent');actions.pack(fill='x',padx=12,pady=(0,14))
            actions.columnconfigure(0,weight=1,uniform='buttons');actions.columnconfigure(1,weight=1,uniform='buttons')
            button(actions,'ดูรายละเอียด',lambda pid=p[0]:self.details(pid),'secondary',width=90).grid(row=0,column=0,sticky='ew',padx=(0,4))
            button(actions,'เพิ่มลงตะกร้า',lambda pid=p[0]:self.add_to_cart(pid),width=90,state='normal' if p[4]>0 else 'disabled').grid(row=0,column=1,sticky='ew',padx=(4,0))
            self._cards.append((c,pic,area,title,p[7]))
        cards=self._cards;state={'job':None,'width':0}
        def layout():
            state['job']=None
            if not canvas.winfo_exists():return
            scale=ctk.ScalingTracker.get_widget_scaling(toolbar)
            width=max(400,canvas.winfo_width());columns=3 if width>=870*scale else 2
            for col in range(3):inner.columnconfigure(col,weight=1 if col<columns else 0,uniform='products' if col<columns else '')
            image_width=max(160,min(int(430*scale),width//columns-int(40*scale)))
            image_height=max(1,int(190*scale))
            for i,(card,image,area,title,path) in enumerate(cards):
                card.grid_configure(row=i//columns,column=i%columns)
                title.configure(wraplength=max(120,image_width-8))
                picture=ctk.CTkImage(light_image=contained_image(path,(image_width,image_height),trim=True),size=(image_width/scale,190))
                image.configure(image=picture);image._store_picture=picture
            inner.update_idletasks()
            height=max([int(62*scale)]+[title.winfo_reqheight()+int(10*scale) for c,pic,area,title,path in cards])
            for c,pic,area,title,path in cards:area.configure(height=height)
        def resize(e):
            if state['width']==e.width:return
            state['width']=e.width
            if state['job']:canvas.after_cancel(state['job'])
            state['job']=canvas.after(60,layout)
        def cleanup(e):
            if e.widget==canvas and state['job']:
                canvas.after_cancel(state['job']);state['job']=None
        canvas.bind('<Configure>',resize,add='+');canvas.bind('<Destroy>',cleanup,add='+')
        state['job']=canvas.after_idle(layout)

    @staticmethod
    def sorted_products(products,mode):
        # Preserve the original query order so default restores the original list.
        if mode=="ราคา: จากน้อยไปมาก":return sorted(products,key=lambda row:row[3])
        if mode=="ราคา: จากมากไปน้อย":return sorted(products,key=lambda row:row[3],reverse=True)
        return list(products)

    # def search_products: อ่านคำค้นและค้นสินค้าที่ตรงเงื่อนไข แล้วแสดงผล
    def search_products(self):
        q = self.search.get().strip()
        if not q:
            self.show_products()
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id,p.name,COALESCE(b.name,'-'),p.price,p.stock,p.description,p.is_featured,p.image
            FROM products p LEFT JOIN brands b ON p.brand_id=b.id
            WHERE p.name LIKE ? OR b.name LIKE ? OR p.description LIKE ?
            ORDER BY p.id DESC
        """, (f"%{q}%",f"%{q}%",f"%{q}%"))
        rows = cur.fetchall()
        conn.close()
        self.show_products(rows)

    # def filter_category: กรองสินค้าตามชื่อหมวดหมู่
    def filter_category(self, name):
        if name == "ทั้งหมด":
            self.filter_category_id(None)
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT p.id,p.name,COALESCE(b.name,'-'),p.price,p.stock,p.description,p.is_featured,p.image
            FROM products p
            LEFT JOIN brands b ON p.brand_id=b.id
            JOIN product_categories pc ON p.id=pc.product_id
            JOIN categories c ON pc.category_id=c.id
            WHERE c.name=? OR c.parent_id=(SELECT id FROM categories WHERE name=? AND parent_id IS NULL)
            ORDER BY p.id DESC
        """, (name,name))
        rows = cur.fetchall()
        conn.close()
        self.show_products(rows)

    # def details: เปิดหน้ารายละเอียด ภาพ คำอธิบาย และตัวเลือกไซซ์ของสินค้า
    def details(self,pid):
        conn=get_connection()
        try:
            product=conn.execute("SELECT p.name,COALESCE(b.name,'-'),p.price,p.stock,p.description,p.image,p.size_type,p.size_chart FROM products p LEFT JOIN brands b ON p.brand_id=b.id WHERE p.id=?",(pid,)).fetchone()
            variants=conn.execute('SELECT id,size,stock FROM product_variants WHERE product_id=? ORDER BY id',(pid,)).fetchall()
        finally:conn.close()
        if not product:return
        self.home_layout=[(child,child.pack_info()) for child in self.frame.winfo_children()]
        for child,options in self.home_layout:child.pack_forget()
        page=tk.Frame(self.frame,bg=BG);page.pack(fill='both',expand=True);self.detail_page=page
        self._build_nav(page)
        line=ctk.CTkFrame(page,fg_color='transparent');line.pack(fill='x',padx=24,pady=(0,12))
        button(line,'‹ ย้อนกลับ',self.back_from_details,'secondary',width=150).pack(side='left')
        label(line,'รายละเอียดสินค้า',18,True).pack(side='left',padx=18)
        outer,canvas,body=scroll_area(page);outer.pack(fill='both',expand=True,padx=20,pady=(0,18))
        left=panel(body);right=panel(body)
        left.grid(row=0,column=0,sticky='new',padx=(0,18),pady=6);right.grid(row=0,column=1,sticky='new',pady=6)
        body.columnconfigure(0,weight=6);body.columnconfigure(1,weight=5)
        from ui.slide_gallery import SlideGallery
        self.product_viewer=SlideGallery(left,images_for(pid,product[5]));self.product_viewer.pack(fill='x',padx=12,pady=12)
        info=ctk.CTkFrame(right,fg_color='transparent');info.pack(fill='x',padx=24,pady=24)
        name=label(info,product[0],24,True,anchor='w',justify='left',wraplength=400);name.pack(fill='x')
        info.bind('<Configure>',lambda e:name.configure(wraplength=max(180,e.width-4)),add='+')
        label(info,product[1],14,color=MUTED,anchor='w').pack(fill='x',pady=(6,10))
        label(info,f'฿{product[2]:,.2f}',31,True,BLUE,anchor='w').pack(fill='x',pady=(0,16))
        qty=tk.IntVar(value=1);self.detail_variant=tk.StringVar();self.detail_variant_map={};size_buttons=[]
        if product[6]!='none' or variants:
            from ui.size_chart import chart_path,show_size_chart
            if chart_path(product[6],product[7]) is not None:
                button(info,'ดูตารางไซส์',lambda:show_size_chart(self.root,product[6],product[7]),'muted',width=145).pack(anchor='w',pady=(0,12))
            label(info,'ตัวเลือกไซส์ (CM)' if product[6]=='shoe_cm' else 'ตัวเลือกไซส์',15,True,anchor='w').pack(fill='x',pady=(0,6))
            self.detail_variant_map={f'{size} — เหลือ {stock}':vid for vid,size,stock in variants if stock>0}
            choices=ctk.CTkFrame(info,fg_color='transparent');choices.pack(fill='x')
            for i,(vid,size,stock) in enumerate(variants):
                value=f'{size} — เหลือ {stock}'
                b=button(choices,str(size),lambda v=value:self.detail_variant.set(v),'secondary',width=64,state='normal' if stock>0 else 'disabled')
                b.grid(row=i//4,column=i%4,padx=(0,8),pady=4);size_buttons.append((value,b))
            if not self.detail_variant_map:label(info,'ไม่มีไซส์พร้อมขาย กรุณาติดต่อร้านค้า',13,color='#CA3445').pack(pady=6)
        label(info,'จำนวน',15,True,anchor='w').pack(fill='x',pady=(16,8))
        controls=ctk.CTkFrame(info,fg_color='transparent');controls.pack(anchor='w')
        def increase():
            maximum=CartPage.remaining(self.user_id,pid,self.detail_variant_map.get(self.detail_variant.get()))
            if qty.get()<maximum:qty.set(qty.get()+1)
            else:messagebox.showwarning('จำนวนสินค้า','เลือกได้สูงสุด 10 ชิ้นรวมกับในตะกร้า และไม่เกิน Stock ของไซส์ที่เลือก')
        button(controls,'−',lambda:qty.set(max(1,qty.get()-1)),'secondary',width=42).pack(side='left')
        label(controls,'',17,True,textvariable=qty,width=52).pack(side='left')
        button(controls,'+',increase,'secondary',width=42).pack(side='left')
        stock_label=label(info,f'คงเหลือรวม {product[3]} ชิ้น · สูงสุด 10 ชิ้นต่อสินค้า',13,color=MUTED,anchor='w');stock_label.pack(fill='x',pady=(10,16))
        def selected(*args):
            qty.set(1)
            for value,b in size_buttons:b.configure(fg_color=BLUE if value==self.detail_variant.get() else WHITE,text_color=WHITE if value==self.detail_variant.get() else BLUE)
            vid=self.detail_variant_map.get(self.detail_variant.get())
            chosen=next((v for v in variants if v[0]==vid),None)
            if chosen:stock_label.configure(text=f'ไซส์ {chosen[1]} · เหลือ {chosen[2]} ชิ้น · สูงสุด 10 ชิ้นต่อสินค้า')
        self.detail_variant.trace_add('write',selected)
        def buy():
            vid=self.detail_variant_map.get(self.detail_variant.get())
            if (product[6]!='none' or variants) and vid is None:
                messagebox.showwarning('ไซส์','กรุณาเลือกไซส์ที่มีสินค้า');return
            if not CartPage.can_add_product(self.user_id,pid):
                messagebox.showwarning('ตะกร้าเต็ม','ตะกร้ามีสินค้าแตกต่างกันครบ 30 อย่างแล้ว กรุณานำบางรายการออกก่อน');return
            if not CartPage.add_item(self.user_id,pid,vid,qty.get()):
                messagebox.showwarning('Stock','สินค้าชนิดเดียวรวมทุกไซส์ได้ไม่เกิน 10 ชิ้น และไม่เกินสินค้าคงเหลือ');return
            self.update_cart_count();messagebox.showinfo('สำเร็จ','เพิ่มสินค้าลงตะกร้าแล้ว')
        button(info,'เพิ่มลงตะกร้า',buy,state='normal' if product[3]>0 and ((product[6]=='none' and not variants) or self.detail_variant_map) else 'disabled').pack(fill='x',pady=(0,8))
        button(info,'เลือกซื้อสินค้าต่อ',self.back_from_details,'secondary').pack(fill='x')
        label(info,'รายละเอียดสินค้า',16,True,anchor='w').pack(fill='x',pady=(24,8))
        description=product[4] or 'ไม่มีคำอธิบายสินค้า'
        desc=tk.Text(info,wrap='word',height=7,width=30,relief='flat',bg=WHITE,fg=NAVY,font=('Noto Sans Thai',10),padx=0,pady=4)
        desc.pack(fill='x');desc.insert('1.0',description)
        for i,match in enumerate(re.finditer(r"https?://[^\s<>\"']+",description,re.I)):
            url=match.group(0).rstrip('.,;!?)');tag=f'url_{i}'
            desc.tag_add(tag,f'1.0+{match.start()}c',f'1.0+{match.start()+len(url)}c');desc.tag_config(tag,foreground=BLUE,underline=True)
            desc.tag_bind(tag,'<Button-1>',lambda e,link=url:webbrowser.open(link))
        desc.configure(state='disabled')
        # The native Text handles its own mouse wheel and keyboard without stealing page scrolling.
        state={'wide':None}
        def adapt(e):
            wide=e.width>=1040
            if state['wide']==wide:return
            state['wide']=wide
            if wide:
                body.columnconfigure(0,weight=6);body.columnconfigure(1,weight=5)
                left.grid_configure(row=0,column=0,columnspan=1,padx=(0,18));right.grid_configure(row=0,column=1,columnspan=1)
            else:
                body.columnconfigure(0,weight=1);body.columnconfigure(1,weight=0)
                left.grid_configure(row=0,column=0,columnspan=2,padx=0);right.grid_configure(row=1,column=0,columnspan=2)
        body.bind('<Configure>',adapt,add='+')

    # def back_from_details: กลับจากรายละเอียดไปแสดงรายการสินค้าหน้าร้าน
    def back_from_details(self):
        self.detail_page.destroy()
        for child, options in self.home_layout:
            child.pack(**options)

    # def add_to_cart: เพิ่มสินค้าเข้าตะกร้า หรือเปิดรายละเอียดให้เลือกไซซ์ก่อน
    def add_to_cart(self, pid):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name,price,stock FROM products WHERE id=?", (pid,))
        p = cur.fetchone()
        conn.close()
        if not p or p[2] <= 0:
            messagebox.showwarning("สินค้า", "สินค้าหมด")
            return
        kind=conn_kind=None
        c=get_connection();kind=c.execute("SELECT size_type FROM products WHERE id=?",(pid,)).fetchone()[0];c.close()
        vid=None
        if kind!='none':
            if not hasattr(self, 'detail_page') or not self.detail_page.winfo_exists():
                self.details(pid)
                return
            vid=self.detail_variant_map.get(self.detail_variant.get())
            if vid is None:
                messagebox.showwarning("ไซซ์","กรุณาเลือกไซซ์ที่มีสินค้า");return
        if not CartPage.can_add_product(self.user_id,pid):
            messagebox.showwarning("ตะกร้าเต็ม","ตะกร้ามีสินค้าแตกต่างกันครบ 30 อย่างแล้ว กรุณานำบางรายการออกก่อน");return
        if not CartPage.add_item(self.user_id, pid, vid):
            messagebox.showwarning("Stock", "จำนวนในตะกร้าถึงจำนวนคงเหลือแล้ว")
            return
        self.update_cart_count()
        messagebox.showinfo("สำเร็จ", f"เพิ่ม {p[0]} ลงตะกร้าแล้ว")

    # def update_cart_count: อัปเดตปุ่มข้อความจากจำนวนชิ้นทั้งหมดในตะกร้า
    def update_cart_count(self):
        def walk(w):
            if (getattr(w,'_store_cart_badge',False) or getattr(w,'_cart_uid',None)==self.user_id):w.configure(text=f'ตะกร้า ({CartPage.total_quantity(self.user_id)})')
            for child in w.winfo_children():walk(child)
        walk(self.root)

    # def cart: เปิดหน้าตะกร้าของลูกค้าที่เข้าสู่ระบบ
    def cart(self):
        self.frame.destroy()
        CartPage(self.root, self.user_id, self.username, self.show_home)

    # def orders: เปิดหน้าคำสั่งซื้อของบทบาทที่ใช้งานหน้านี้
    def orders(self):
        self.frame.destroy()
        OrdersPage(self.root, self.user_id, self.username, self.show_home)

    # def contact: เปิดหน้าติดต่อร้านจากปุ่มก่อนตะกร้า โดยเก็บตะกร้าและบัญชีเดิม
    def contact(self):
        from ui.contact import ContactPage
        self.frame.destroy();ContactPage(self.root,self.show_home,user_id=self.user_id,username=self.username)


    # def account: เปิดหน้าแก้ไขบัญชีและที่อยู่ของลูกค้า
    def account(self):
        self.frame.destroy()
        AccountPage(self.root, self.user_id, self.username, self.show_home)

    # def show_home: สร้างหน้าร้านใหม่หลังกลับจากหน้าลูกค้าอื่น
    def show_home(self):
        self.__init__(self.root, self.user_id, self.username, self.logout_callback)
