"""Product list and separate edit/read-only pages, reusing existing stock transactions."""
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from database.database import get_connection
from ui.image_utils import photo,store_image
from ui.gallery import images_for,save_gallery
from ui.admin.size_editor import SizeEditor
from ui.admin.products_base import AdminProductsPage as ProductTransactions
from ui.admin.modern_style import *

class AdminProductsPage(ProductTransactions):
    def __init__(self,root,back_callback):
        self.root=root;self.back_callback=back_callback;self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True)
        self.selected=None;self.new_image=None;self.preview_photo=None;self.gallery_paths=[];self.gallery_new=[];self.gallery_index=0
        main=chrome(self,'จัดการสินค้า','จัดการสินค้า รูปภาพ ไซส์ และจำนวนคงเหลือ','products')
        outer,canvas,body=scroll_area(main);outer.pack(fill='both',expand=True)
        self.work=tk.Frame(body,bg=BG);self.work.pack(fill='both',expand=True,padx=24,pady=(0,18))
        self.show_list()
        self.alert_job=self.root.after(5000,self.poll_alerts)
        self.frame.bind('<Destroy>',self.stop_polling,add='+')

    def poll_alerts(self):
        if not self.frame.winfo_exists():return
        if not self.editor_mode:self.refresh_alerts()
        self.alert_job=self.root.after(5000,self.poll_alerts)

    def show_list(self):
        for w in self.work.winfo_children():w.destroy()
        self.editor_mode=False;self.page=1;self.selected=None
        self.stat_values=metrics(self.work,[('สินค้าทั้งหมด','—'),('ใกล้หมด (รายการ/ไซส์)','—'),('หมดสต๊อก (รายการ/ไซส์)','—')])
        top=tk.Frame(self.work,bg=BG);top.pack(fill='x',pady=(0,12))
        self.alert_summary=label(top,'',14,color='#996000',anchor='w');self.alert_summary.pack(side='left')
        button(top,'+ เพิ่มสินค้า',lambda:self.edit_product()).pack(side='right')
        self.list_panel=panel(self.work);self.list_panel.pack(fill='both',expand=True)
        filters=tk.Frame(self.list_panel,bg=WHITE);filters.pack(fill='x',padx=16,pady=16)
        self.search_keyword=tk.StringVar();self.filter_category=tk.StringVar(value='ทุกหมวด');self.stock_filter=tk.StringVar(value='ทุกสถานะ')
        search=entry(filters,self.search_keyword,width=245,placeholder='ค้นหาชื่อสินค้า / ID');search.pack(side='left',fill='x',expand=True,padx=(0,8));search.bind('<Return>',self.filter_products)
        self.category_filter=menu(filters,self.filter_category,['ทุกหมวด'],lambda v:self.filter_products(),180);self.category_filter.pack(side='left',padx=4)
        menu(filters,self.stock_filter,['ทุกสถานะ','ใกล้หมด','หมดสต๊อก'],lambda v:self.filter_products(),135).pack(side='left',padx=4)
        button(filters,'ค้นหา',self.filter_products,width=80).pack(side='left',padx=4)
        box,self.tree=table(self.list_panel,[('id','ID',65),('name','สินค้า',270),('brand','แบรนด์',120),('price','ราคา',110),('stock','คงเหลือ',85),('featured','แนะนำ',85)],5)
        box.pack(fill='both',expand=True,padx=16);self.tree.bind('<Double-1>',lambda e:self.view_product())
        actions=tk.Frame(self.list_panel,bg=WHITE);actions.pack(fill='x',padx=16,pady=12)
        for title,cmd,kind in [('ดู',self.view_product,'secondary'),('แก้ไข',self.edit_selected,'primary'),('ลบ',self.delete_selected,'danger')]:button(actions,title,cmd,kind,width=95).pack(side='left',padx=(0,8))
        self.search_count=label(actions,'',13,color=MUTED);self.search_count.pack(side='right')
        nav=tk.Frame(self.list_panel,bg=WHITE);nav.pack(fill='x',padx=16,pady=(0,16))
        button(nav,'‹ ก่อนหน้า',lambda:self.render_page(self.page-1),'secondary',width=115).pack(side='left')
        self.page_label=label(nav,'',14);self.page_label.pack(side='left',padx=16)
        button(nav,'ถัดไป ›',lambda:self.render_page(self.page+1),'secondary',width=115).pack(side='left')
        self.alert_panel=panel(self.work);self.alert_panel.pack(fill='x',pady=(14,0))
        label(self.alert_panel,'สินค้า/ไซส์ที่เหลือไม่เกิน 3 ชิ้น · ดับเบิลคลิกเพื่อแก้ไข',14,True,anchor='w').pack(fill='x',padx=16,pady=(12,6))
        box,self.alert_tree=table(self.alert_panel,[('name','สินค้า',300),('size','ไซส์',90),('stock','คงเหลือ',80),('status','สถานะ',110)],3);box.pack(fill='x',padx=16,pady=(0,12))
        self.alert_tree.bind('<Double-1>',lambda e:self.edit_product(self.alert_ids.get(self.alert_tree.selection()[0])) if self.alert_tree.selection() else None)
        self.load()

    def load(self):
        with get_connection() as conn:
            self.brands=conn.execute('SELECT id,name FROM brands ORDER BY name').fetchall()
            self.categories=conn.execute('SELECT id,name FROM categories ORDER BY parent_id IS NOT NULL,id').fetchall()
            count=conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        self.filter_categories={'ทุกหมวด':None,**{f'{name} [#{cid}]':cid for cid,name in self.categories}}
        if self.editor_mode:
            self.brand['values']=[x[1] for x in self.brands];self.cats.delete(0,tk.END)
            for _,name in self.categories:self.cats.insert(tk.END,name)
            return
        self.category_filter.configure(values=list(self.filter_categories));self.filter_products();self.refresh_alerts()
        from database.stock_alerts import low_stock_rows
        alerts=low_stock_rows()
        for w,v in zip(self.stat_values,[count,sum(r[3]>0 for r in alerts),sum(r[3]==0 for r in alerts)]):w.configure(text=str(v))

    def filter_products(self,event=None):
        if self.editor_mode:return
        from database.product_search import search_products
        keyword=self.search_keyword.get().strip()
        rows=search_products('' if keyword.isdigit() else keyword,self.filter_categories.get(self.filter_category.get()))
        if keyword.isdigit():rows=[r for r in rows if str(r[0])==keyword]
        from database.stock_alerts import low_stock_rows
        low={r[0] for r in low_stock_rows() if r[3]>0};empty={r[0] for r in low_stock_rows() if r[3]==0}
        mode=self.stock_filter.get();self.rows=[r for r in rows if mode=='ทุกสถานะ' or r[0] in (low if mode=='ใกล้หมด' else empty)]
        self.render_page(1)

    def render_page(self,page):
        pages=max(1,(len(self.rows)+8)//9);self.page=max(1,min(pages,page))
        self.tree.delete(*self.tree.get_children())
        self.row_images=[]
        self.tree.configure(show='tree headings',style='ProductList.Admin.Treeview');self.tree.heading('#0',text='รูป');self.tree.column('#0',width=75,minwidth=75,stretch=False)
        ttk.Style(self.root).configure('ProductList.Admin.Treeview',rowheight=64)
        with get_connection() as conn:covers=dict(conn.execute('SELECT id,image FROM products'))
        for r in self.rows[(self.page-1)*9:self.page*9]:
            image=photo(covers.get(r[0]),(58,54));self.row_images.append(image)
            self.tree.insert('','end',iid=str(r[0]),image=image,values=(r[0],r[1],r[2],f'฿{r[3]:,.2f}',r[4],'ใช่' if r[5] else 'ไม่'),tags=('empty' if r[4]==0 else 'low' if r[4]<=3 else 'ok',))
        self.search_count.configure(text=f'พบ {len(self.rows)} สินค้า');self.page_label.configure(text=f'หน้า {self.page} / {pages}')

    def chosen(self):
        selection=self.tree.selection()
        if not selection:messagebox.showinfo('สินค้า','กรุณาเลือกสินค้าจากตาราง');return
        return int(self.tree.item(selection[0])['values'][0])

    def edit_selected(self):
        pid=self.chosen()
        if pid:self.edit_product(pid)

    def delete_selected(self):
        pid=self.chosen()
        if not pid:return
        self.selected=pid
        # Use the same deletion guard/foreign-key constraints without requiring an editor.
        if not messagebox.askyesno('ลบสินค้า','ต้องการลบสินค้าที่เลือกหรือไม่?'):return
        with get_connection() as conn:
            try:conn.execute('DELETE FROM products WHERE id=?',(pid,))
            except Exception as exc:messagebox.showerror('ลบไม่ได้','สินค้านี้อาจมีคำสั่งซื้อแล้ว\n'+str(exc));return
        self.load()

    def view_product(self):
        pid=self.chosen()
        if not pid:return
        with get_connection() as conn:
            p=conn.execute('SELECT name,price,stock,description,image,size_type,size_chart FROM products WHERE id=?',(pid,)).fetchone()
            variants=conn.execute('SELECT size,stock FROM product_variants WHERE product_id=? ORDER BY id',(pid,)).fetchall()
        for w in self.work.winfo_children():w.destroy()
        self.editor_mode=True
        button(self.work,'‹ กลับรายการ',self.show_list,'secondary').pack(anchor='w',pady=(0,12))
        body=tk.Frame(self.work,bg=BG);body.pack(fill='both',expand=True)
        card=panel(body);card.pack(fill='x',pady=8,padx=8)
        from ui.slide_gallery import SlideGallery
        SlideGallery(card,images_for(pid,p[4])).pack(fill='x',padx=18,pady=16)
        label(card,p[0],24,True,wraplength=650).pack(padx=20,pady=8)
        label(card,f'฿{p[1]:,.2f} · คงเหลือรวม {p[2]} ชิ้น',19,True,BLUE).pack(pady=8)
        label(card,'\n'.join(f'ไซส์ {size}: {stock} ชิ้น' for size,stock in variants) or 'สินค้าไม่มีไซส์',15).pack(pady=8)
        label(card,p[3] or 'ไม่มีคำอธิบาย',15,wraplength=650,justify='left').pack(padx=20,pady=16)
        from ui.size_chart import show_size_chart
        if p[5]!='none':button(card,'ดูตารางไซส์',lambda:show_size_chart(self.root,p[5],p[6]),'secondary').pack(pady=6)
        button(card,'แก้ไขสินค้า',lambda:self.edit_product(pid)).pack(pady=(8,20))

    def edit_product(self,pid=None):
        # Keep a private selection model for the unchanged transaction loader.
        for w in self.work.winfo_children():w.destroy()
        self.editor_mode=True;self.selected=None;self.gallery_paths=[];self.gallery_new=[];self.gallery_index=0
        line=tk.Frame(self.work,bg=BG);line.pack(fill='x',pady=(0,12))
        button(line,'‹ กลับรายการ',self.show_list,'secondary').pack(side='left')
        label(line,'เพิ่มสินค้า' if pid is None else f'แก้ไขสินค้า #{pid}',21,True).pack(side='left',padx=20)
        body=tk.Frame(self.work,bg=BG);body.pack(fill='both',expand=True)
        body.columnconfigure(0,weight=1);body.columnconfigure(2,weight=1);body.columnconfigure(1,minsize=700)
        body.bind('<Configure>',lambda e:body.columnconfigure(1,minsize=max(420,min(700,e.width-32))),add='+')
        box=panel(body);box.grid(row=0,column=1,padx=16,pady=10,sticky='ew')
        form=tk.Frame(box,bg=WHITE,width=680);form.pack(fill='both',expand=True,padx=22,pady=22)
        self.build_editor(form)
        self.tree=ttk.Treeview(self.work,columns=('id',),show='headings')
        self.load()
        if pid is not None:
            item=self.tree.insert('','end',values=(pid,));self.tree.selection_set(item);ProductTransactions.select(self)
        from ui.customer_style import polish
        polish(form)
        self.render_gallery()

    def add(self):
        if ProductTransactions.add(self):self.show_list()

    def update(self):
        if ProductTransactions.update(self):self.show_list()

    def build_editor(self,form):
        from ui.modern_widgets import ActionButton
        self.preview_label=tk.Label(form,text="ไม่มีรูปภาพ",bg="white");self.preview_label.pack(pady=12)
        self.gallery_count=tk.Label(form,text="0 / 0");self.gallery_count.pack()
        gallery_buttons=tk.Frame(form);gallery_buttons.pack(pady=6)
        for label,action in [("◀",self.previous_image),("เพิ่มรูปภาพ",self.pick_image),("ลบรูปนี้",self.remove_image),("▶",self.next_image)]:
            ActionButton(gallery_buttons,text=label,command=action).pack(side="left",padx=3)
        ActionButton(form,text="ตั้งเป็นรูปหลัก",command=self.make_cover).pack(pady=5)
        fields=tk.Frame(form);fields.pack(fill="x",padx=14,pady=10);fields.grid_columnconfigure(1,weight=1)
        self.name=entry(fields,width=300);self.brand=ttk.Combobox(fields,width=23,state="readonly")
        self.price=entry(fields,width=300);self.stock=entry(fields,width=300)
        for i,(label,widget) in enumerate((("ชื่อสินค้า",self.name),("Brand",self.brand),("ราคา",self.price),("Stock",self.stock))):
            tk.Label(fields,text=label,width=10,anchor="w").grid(row=i,column=0,sticky="w",pady=6)
            widget.grid(row=i,column=1,sticky="ew",pady=6)
        tk.Label(form,text="รายละเอียด",anchor="w").pack(fill="x",padx=14)
        self.desc=tk.Text(form,width=36,height=6,wrap="word");self.desc.pack(fill="x",padx=14,pady=6)
        # ช่องเส้นทางภาพเก็บไว้เพื่อรองรับโค้ดอ่าน/ล้างเดิม ใช้แกลเลอรีเป็น UI หลัก
        self.image=tk.Entry(form)
        self.featured=tk.IntVar();tk.Checkbutton(form,text="สินค้าแนะนำ",variable=self.featured).pack(anchor="w",padx=14,pady=6)
        options=tk.Frame(form);options.pack(fill="x",padx=14,pady=8);options.grid_columnconfigure(0,weight=1)
        tk.Label(options,text="Category").grid(row=0,column=0,sticky="w")
        self.cats=tk.Listbox(options,width=24,height=6,selectmode=tk.MULTIPLE,exportselection=False);self.cats.grid(row=1,column=0,sticky="ew",padx=(0,10))
        sizebox=tk.LabelFrame(options,text="ประเภทไซซ์");sizebox.grid(row=0,column=1,rowspan=2,sticky="ns")
        self.size_type=tk.StringVar(value="none")
        from ui.size_chart import SIZE_LABELS
        self.size_label=tk.StringVar(value=SIZE_LABELS['none'])
        type_selector=ttk.Combobox(sizebox,textvariable=self.size_label,values=list(SIZE_LABELS.values()),state="readonly",width=17);type_selector.pack(padx=6,pady=6)
        self.size_type.trace_add('write',lambda *args:self.size_label.set(SIZE_LABELS.get(self.size_type.get(),'ไม่มีไซซ์')))
        tk.Label(sizebox,text="เลือกประเภทให้ตรงสินค้า\nตารางไซซ์จะแสดงตามประเภท",justify="left").pack(padx=6,pady=6)
        self.size_editor=SizeEditor(form,self.size_type);self.size_editor.previous_kind="none";self.size_editor.pack(fill="x",padx=10,pady=8)
        # def choose_kind: แปลงชื่อไทยกลับเป็นรหัสเดิม ไม่เปลี่ยนข้อมูลประเภทไซซ์ที่บันทึกอยู่
        def choose_kind(event):
            self.size_type.set(next(k for k,v in SIZE_LABELS.items() if v==self.size_label.get()))
            self.size_editor.change_kind(event)
        type_selector.bind("<<ComboboxSelected>>",choose_kind)
        self.chart_saved=None;self.chart_new=None
        chartbox=tk.LabelFrame(form,text="ตารางไซซ์ของสินค้านี้",padx=8,pady=8);chartbox.pack(fill="x",padx=14,pady=8)
        self.chart_status=tk.Label(chartbox,text="ใช้ตารางอัตโนมัติตามประเภทไซซ์",wraplength=430);self.chart_status.pack(anchor="w",pady=5)
        chart_buttons=tk.Frame(chartbox);chart_buttons.pack()
        for title,action in [("เลือกรูปตารางไซซ์",self.pick_chart),("ดูตาราง",self.preview_chart),("ใช้อัตโนมัติ",self.reset_chart)]:
            ActionButton(chart_buttons,text=title,command=action).pack(side="left",padx=3)
        actions=tk.Frame(form,bg="white");actions.pack(fill="x",pady=16)
        button(actions,"บันทึกสินค้า",lambda:self.update() if self.selected else self.add()).pack(side="left",padx=5)
        button(actions,"ยกเลิก",self.show_list,"secondary").pack(side="left",padx=5)
