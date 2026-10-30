from ui.modern_widgets import ActionButton,RoundedCard
# ไฟล์นี้: จัดการสินค้า หมวดหมู่ รูปภาพ ไซซ์ และ Stock รายไซซ์
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database.database import get_connection
from ui.image_utils import photo, store_image
from ui.gallery import images_for, save_gallery
from ui.admin.size_editor import SizeEditor


# คลาส AdminProductsPage: เก็บข้อมูลและพฤติกรรมของ จัดการสินค้า หมวดหมู่ รูปภาพ ไซซ์ และ Stock รายไซซ์
class AdminProductsPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,back_callback):
        self.root=root; self.back_callback=back_callback; self.selected=None; self.new_image=None; self.preview_photo=None; self.gallery_paths=[]; self.gallery_new=[]; self.gallery_index=0
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True); self.build(); self.load()

    # def build: แบ่งฟอร์มเลื่อนทางซ้าย ตารางสินค้าและแจ้งเตือนทางขวาตาม PDF
    def build(self):
        from ui.customer_style import header,scroll_body,polish
        header(self.frame,"จัดการสินค้า",self.back)
        shell=tk.Frame(self.frame,bg="#F3F5F9");shell.pack(fill="both",expand=True,padx=20,pady=16)
        shell.grid_columnconfigure(1,weight=1);shell.grid_rowconfigure(0,weight=1)
        left=tk.Frame(shell,width=500,bg="white");left.grid(row=0,column=0,sticky="nsew",padx=(0,20));left.grid_propagate(False)
        left.pack_propagate(False)
        form=scroll_body(left)
        right=tk.Frame(shell,bg="white",padx=14,pady=14);right.grid(row=0,column=1,sticky="nsew")
        self.preview_label=tk.Label(form,text="ไม่มีรูปภาพ",bg="white");self.preview_label.pack(pady=12)
        self.gallery_count=tk.Label(form,text="0 / 0");self.gallery_count.pack()
        gallery_buttons=tk.Frame(form);gallery_buttons.pack(pady=6)
        for label,action in [("◀",self.previous_image),("เพิ่มรูปภาพ",self.pick_image),("ลบรูปนี้",self.remove_image),("▶",self.next_image)]:
            ActionButton(gallery_buttons,text=label,command=action).pack(side="left",padx=3)
        ActionButton(form,text="ตั้งเป็นรูปหลัก",command=self.make_cover).pack(pady=5)
        fields=tk.Frame(form);fields.pack(fill="x",padx=14,pady=10);fields.grid_columnconfigure(1,weight=1)
        self.name=tk.Entry(fields,width=26);self.brand=ttk.Combobox(fields,width=23,state="readonly")
        self.price=tk.Entry(fields,width=26);self.stock=tk.Entry(fields,width=26)
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
        btn=tk.Frame(form);btn.pack(pady=12)
        for text,cmd in [("เพิ่ม",self.add),("แก้ไข",self.update),("ลบ",self.delete),("ล้าง",self.clear)]:
            ActionButton(btn,text=text,width=9,command=cmd).pack(side="left",padx=3)
        searchbar=tk.Frame(right,bg="white");searchbar.pack(fill="x",pady=(0,10))
        searchbar.grid_columnconfigure(1,weight=1)
        tk.Label(searchbar,text="ค้นหา:",bg="white").grid(row=0,column=0,padx=(0,6))
        self.search_keyword=tk.StringVar()
        search_entry=tk.Entry(searchbar,textvariable=self.search_keyword,width=20)
        search_entry.grid(row=0,column=1,sticky="ew",padx=(0,8))
        search_entry.bind("<Return>",self.filter_products)
        tk.Label(searchbar,text="Category:",bg="white").grid(row=0,column=2,padx=5)
        self.filter_category=tk.StringVar(value="ทุกหมวด")
        self.category_filter=ttk.Combobox(searchbar,textvariable=self.filter_category,state="readonly",width=20)
        self.category_filter.grid(row=0,column=3,padx=5)
        self.category_filter.bind("<<ComboboxSelected>>",self.filter_products)
        ActionButton(searchbar,text="ค้นหา",command=self.filter_products,bg="#4145F1",fg="white").grid(row=1,column=1,sticky="e",pady=5)
        ActionButton(searchbar,text="ล้างตัวกรอง",command=self.reset_filters).grid(row=1,column=3,sticky="e",pady=5)
        self.search_count=tk.Label(right,text="",anchor="w",bg="white",fg="#64748B");self.search_count.pack(fill="x",pady=(0,5))
        table=tk.Frame(right);table.pack(fill="both",expand=True)
        self.tree=ttk.Treeview(table,columns=("id","name","brand","price","stock","featured"),show="headings",height=10)
        for c,t,w in (("id","ID",45),("name","สินค้า",240),("brand","Brand",100),("price","ราคา",85),("stock","Stock",65),("featured","แนะนำ",65)):
            self.tree.heading(c,text=t);self.tree.column(c,width=w,minwidth=45,stretch=c=="name")
        vertical=ttk.Scrollbar(table,command=self.tree.yview);vertical.pack(side="right",fill="y")
        horizontal=ttk.Scrollbar(table,orient="horizontal",command=self.tree.xview);horizontal.pack(side="bottom",fill="x")
        self.tree.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set);self.tree.pack(fill="both",expand=True)
        self.tree.tag_configure("low",background="#FFF2D5",foreground="#8A4B00")
        self.tree.tag_configure("empty",background="#FEE2E2",foreground="#991B1B")
        self.tree.bind("<<TreeviewSelect>>",self.select)
        self.alert_summary=tk.Label(right,text="แจ้งเตือนสินค้าใกล้หมด (เหลือไม่เกิน 3 ชิ้น)",anchor="w",font=("Noto Sans Thai",12,"bold"));self.alert_summary.pack(fill="x",pady=(14,8))
        alert_frame=tk.Frame(right);alert_frame.pack(fill="both",expand=True)
        self.alert_tree=ttk.Treeview(alert_frame,columns=("name","size","stock","status"),show="headings",height=7)
        for key,title,width in (("name","สินค้า",240),("size","ไซซ์",70),("stock","เหลือ",55),("status","สถานะ",95)):
            self.alert_tree.heading(key,text=title);self.alert_tree.column(key,width=width,minwidth=45,stretch=key=="name")
        bar=ttk.Scrollbar(alert_frame,command=self.alert_tree.yview);bar.pack(side="right",fill="y")
        self.alert_tree.configure(yscrollcommand=bar.set);self.alert_tree.pack(fill="both",expand=True)
        self.alert_tree.tag_configure("low",background="#FFF2D5",foreground="#8A4B00");self.alert_tree.tag_configure("empty",background="#FEE2E2",foreground="#991B1B")
        self.alert_tree.bind("<<TreeviewSelect>>",self.open_alert)
        ActionButton(right,text="รีเฟรช Stock / แจ้งเตือน",command=self.load).pack(pady=10)
        polish(form);self.render_gallery()
        self.alert_job=self.root.after(5000,self.poll_alerts)
        self.frame.bind("<Destroy>",self.stop_polling,add="+")

    # def refresh_alerts: อ่าน Stock จริง แสดงสีและจำนวนรายการเตือน โดยไม่แก้ฟอร์มที่กำลังพิมพ์
    def refresh_alerts(self):
        from database.stock_alerts import low_stock_rows
        rows=low_stock_rows();self.alert_ids={}
        for item in self.alert_tree.get_children():self.alert_tree.delete(item)
        for index,(pid,name,size,stock,status) in enumerate(rows):
            item=self.alert_tree.insert("",tk.END,values=(name,size or "-",stock,status),tags=("empty" if stock==0 else "low",))
            self.alert_ids[item]=pid
        empty=sum(row[3]==0 for row in rows)
        self.alert_summary.configure(text=f"แจ้งเตือน: ใกล้หมด {len(rows)-empty} รายการ · หมด {empty} รายการ" if rows else "Stock ปกติ — ไม่มีสินค้าเหลือไม่เกิน 3 ชิ้น")

    # def open_alert: เลือกรายการเตือนแล้วเปิดสินค้าในฟอร์มด้านซ้าย
    def open_alert(self,event=None):
        selected=self.alert_tree.selection()
        if not selected:return
        pid=self.alert_ids.get(selected[0])
        if not any(self.tree.item(item)["values"][0]==pid for item in self.tree.get_children()):
            self.reset_filters()
        for item in self.tree.get_children():
            if self.tree.item(item)["values"][0]==pid:
                self.tree.selection_set(item);self.tree.see(item);self.select();return

    # def poll_alerts: อัปเดตแจ้งเตือนทุก 5 วินาทีขณะหน้านี้เปิดอยู่
    def poll_alerts(self):
        if self.frame.winfo_exists():
            try:self.refresh_alerts()
            finally:self.alert_job=self.root.after(5000,self.poll_alerts)

    # def stop_polling: ยกเลิกงานตรวจ Stock เมื่อปิดหน้า ไม่ทิ้ง callback ค้าง
    def stop_polling(self,event):
        if event.widget==self.frame and getattr(self,"alert_job",None):
            self.root.after_cancel(self.alert_job);self.alert_job=None

    # def load: อ่านข้อมูลล่าสุดจากฐานข้อมูล แล้วเติมรายการในหน้าจอ
    def load(self):
        conn=get_connection(); cur=conn.cursor()
        cur.execute("SELECT id,name FROM brands ORDER BY name"); self.brands=cur.fetchall(); self.brand["values"]=[x[1] for x in self.brands]
        cur.execute("SELECT id,name FROM categories ORDER BY parent_id IS NOT NULL,id"); self.categories=cur.fetchall()
        self.cats.delete(0,tk.END)
        for x in self.categories: self.cats.insert(tk.END,x[1])
        conn.close()
        self.filter_categories={"ทุกหมวด":None}
        self.filter_categories.update({f"{name} [#{cid}]":cid for cid,name in self.categories})
        self.category_filter["values"]=list(self.filter_categories)
        if self.filter_category.get() not in self.filter_categories:self.filter_category.set("ทุกหมวด")
        self.filter_products()
        self.refresh_alerts()

    # def filter_products: กรองตารางโดยไม่เปลี่ยนข้อมูลในฟอร์มและแจ้งเตือนทุกหมวด
    def filter_products(self,event=None):
        from database.product_search import search_products
        cid=self.filter_categories.get(self.filter_category.get())
        rows=search_products(self.search_keyword.get(),cid)
        for item in self.tree.get_children():self.tree.delete(item)
        for r in rows:
            self.tree.insert("",tk.END,values=(r[0],r[1],r[2],f"{r[3]:,.2f}",r[4],"ใช่" if r[5] else "ไม่"),tags=("empty" if r[4]==0 else "low" if r[4]<=3 else "normal",))
        self.search_count.configure(text=f"พบ {len(rows)} สินค้า" if rows else "ไม่พบสินค้าตามเงื่อนไขที่เลือก")

    # def reset_filters: กลับไปแสดงสินค้าทุกหมวด รวมสินค้าหมดเพื่อให้เติม Stock ได้
    def reset_filters(self):
        self.search_keyword.set("");self.filter_category.set("ทุกหมวด");self.filter_products()

    # def pick_chart: เลือกและตรวจภาพเฉพาะสินค้า เก็บรอบันทึกเมื่อเพิ่ม/แก้ไขสินค้า
    def pick_chart(self):
        path=filedialog.askopenfilename(title="เลือกตารางไซซ์",filetypes=[("รูปภาพ","*.png *.jpg *.jpeg *.webp")])
        if not path:return
        from PIL import Image
        try:
            with Image.open(path) as im:im.verify()
        except OSError:messagebox.showwarning("ตารางไซซ์","เปิดภาพนี้ไม่ได้");return
        self.chart_new=path;self.chart_status.configure(text="ภาพเฉพาะสินค้า: "+path.rsplit('/',1)[-1])

    # def preview_chart: ดูภาพเฉพาะที่เลือกรอไว้หรือภาพอัตโนมัติของประเภทปัจจุบัน
    def preview_chart(self):
        from ui.size_chart import show_size_chart
        show_size_chart(self.root,self.size_type.get(),self.chart_new or self.chart_saved)

    # def reset_chart: กลับไปใช้ตารางอัตโนมัติ มีผลจริงเมื่อกดเพิ่ม/แก้ไข
    def reset_chart(self):
        self.chart_saved=None;self.chart_new=None;self.chart_status.configure(text="ใช้ตารางอัตโนมัติตามประเภทไซซ์")

    # def gallery_all: รวมรูปที่บันทึกแล้วกับรูปใหม่ที่ยังไม่ได้บันทึก
    def gallery_all(self):
        return self.gallery_paths + self.gallery_new

    # def render_gallery: แสดงรูปที่เลือกและตำแหน่งภาพในแกลเลอรี
    def render_gallery(self):
        paths=self.gallery_all()
        if paths: self.gallery_index %= len(paths)
        else: self.gallery_index=0
        self.preview_photo=photo(paths[self.gallery_index] if paths else None,(240,210))
        self.preview_label.config(image=self.preview_photo,text="")
        self.gallery_count.config(text=f"{self.gallery_index+1 if paths else 0} / {len(paths)}")

    # def pick_image: เลือกหลายภาพ ตรวจว่าเปิดได้ แล้วเพิ่มไว้ในรายการรอบันทึก
    def pick_image(self):
        paths=filedialog.askopenfilenames(title="เลือกรูปสินค้า",filetypes=[("Images","*.png *.jpg *.jpeg *.webp")])
        if not paths:return
        from PIL import Image
        try:
            for path in paths:
                with Image.open(path) as im: im.verify()
        except Exception as exc:
            messagebox.showerror("รูปภาพ",f"เปิดรูปไม่ได้: {exc}"); return
        self.gallery_new.extend(paths)
        self.gallery_index=len(self.gallery_all())-len(paths)
        self.render_gallery()

    # def previous_image: เลื่อนไปภาพก่อนหน้าแล้วแสดงแกลเลอรีใหม่
    def previous_image(self):
        if self.gallery_all(): self.gallery_index-=1; self.render_gallery()

    # def next_image: เลื่อนไปภาพถัดไปแล้วแสดงแกลเลอรีใหม่
    def next_image(self):
        if self.gallery_all(): self.gallery_index+=1; self.render_gallery()

    # def remove_image: ลบรูปที่กำลังแสดงออกจากรายการในฟอร์ม
    def remove_image(self):
        i=self.gallery_index
        if i<len(self.gallery_paths):self.gallery_paths.pop(i)
        elif self.gallery_new:self.gallery_new.pop(i-len(self.gallery_paths))
        self.render_gallery()

    # def make_cover: ย้ายรูปที่เลือกไปลำดับแรกเพื่อใช้เป็นรูปหลัก
    def make_cover(self):
        all_paths=self.gallery_all()
        if not all_paths:return
        chosen=all_paths.pop(self.gallery_index)
        all_paths.insert(0,chosen)
        self.gallery_paths=all_paths; self.gallery_new=[]; self.gallery_index=0
        self.render_gallery()

    # def persist_gallery: คัดลอกรูปใหม่และบันทึกแกลเลอรีลง connection ของธุรกรรมสินค้า
    def persist_gallery(self,conn,pid):
        paths=self.gallery_paths+[store_image(path) for path in self.gallery_new]
        save_gallery(conn,pid,paths)
        chart=store_image(self.chart_new) if self.chart_new else self.chart_saved
        conn.execute("UPDATE products SET size_chart=? WHERE id=?",(chart,pid))

    # def variants: ตรวจและคืนคู่ไซซ์/จำนวนจากตัวแก้ไขไซซ์
    def variants(self):
        return self.size_editor.values()

    # def save_variants: เพิ่ม/แก้ Stock รายไซซ์ รวม Stock สินค้า และห้ามลบไซซ์ที่มีประวัติคำสั่งซื้อ
    def save_variants(self,conn,pid):
        variants=self.variants(); kind=self.size_type.get()
        existing=dict(conn.execute("SELECT size,stock FROM product_variants WHERE product_id=?",(pid,)).fetchall())
        if self.selected and existing:
            for size,stock in existing.items():
                if size not in dict(variants) and conn.execute("SELECT 1 FROM order_items WHERE product_id=? AND size_label=? LIMIT 1",(pid,size)).fetchone():
                    raise ValueError("ลบไซซ์ที่เคยมีคำสั่งซื้อไม่ได้: "+size)
        conn.execute("UPDATE products SET size_type=?,stock=? WHERE id=?",(kind,sum(x[1] for x in variants) if kind!='none' else int(self.stock.get()),pid))
        for size,stock in variants:
            conn.execute("INSERT INTO product_variants(product_id,size,stock) VALUES(?,?,?) ON CONFLICT(product_id,size) DO UPDATE SET stock=excluded.stock",(pid,size,stock))
        for size in existing.keys()-dict(variants).keys():
            conn.execute("DELETE FROM product_variants WHERE product_id=? AND size=?",(pid,size))

    # def values: ตรวจข้อมูลฟอร์ม และคืนค่าที่พร้อมบันทึกลงฐานข้อมูล
    def values(self):
        variants=self.variants()
        name=self.name.get().strip()
        try: price=float(self.price.get()); stock=sum(qty for size,qty in variants) if self.size_type.get()!='none' else int(self.stock.get())
        except ValueError: raise ValueError("ราคาและ Stock ต้องเป็นตัวเลข")
        if not name or price<0 or stock<0: raise ValueError("ข้อมูลสินค้าไม่ถูกต้อง")
        inds=self.cats.curselection()
        if not inds: raise ValueError("กรุณาเลือก Category")
        brand_id=None
        for bid,bname in self.brands:
            if bname==self.brand.get(): brand_id=bid; break
        desc=self.desc.get("1.0",tk.END).strip()
        # URLs can be pasted directly into the description and become clickable in the shop.
        if self.featured.get():
            conn = get_connection()
            cur = conn.cursor()
            if self.selected:
                cur.execute("SELECT COUNT(*) FROM products WHERE is_featured=1 AND id<>?", (self.selected,))
            else:
                cur.execute("SELECT COUNT(*) FROM products WHERE is_featured=1")
            count = cur.fetchone()[0]
            conn.close()
            if count >= 6:
                raise ValueError("สินค้าแนะนำมีได้สูงสุด 6 ชิ้น กรุณายกเลิกสินค้าแนะนำรายการอื่นก่อน")
        return name,brand_id,price,stock,desc,(self.gallery_all()[0] if self.gallery_paths and self.gallery_all() else ""),self.featured.get(),[self.categories[i][0] for i in inds]

    # def add: ตรวจข้อมูลแล้วเพิ่มสินค้า หมวด รูป และไซซ์; rollback เมื่อบันทึกไม่สำเร็จ
    def add(self):
        try: vals=self.values()
        except ValueError as e: messagebox.showwarning("ข้อมูล",str(e)); return
        conn=get_connection(); cur=conn.cursor()
        try:
            cur.execute("INSERT INTO products(name,brand_id,price,stock,description,image,is_featured) VALUES(?,?,?,?,?,?,?)",vals[:7])
            pid=cur.lastrowid
            cur.executemany("INSERT INTO product_categories(product_id,category_id) VALUES(?,?)",[(pid,c) for c in vals[7]])
            self.persist_gallery(conn,pid)
            self.save_variants(conn,pid)
            conn.commit()
        except Exception as exc:
            conn.rollback();messagebox.showerror("บันทึกสินค้า",str(exc));return
        finally:conn.close()
        messagebox.showinfo("สำเร็จ","เพิ่มสินค้าแล้ว"); self.clear(); self.load(); return True

    # def select: อ่านข้อมูลรายการที่เลือกมาแสดงในฟอร์มหรือรายละเอียด
    def select(self,event=None):
        sel=self.tree.selection()
        if not sel:return
        pid=self.tree.item(sel[0])["values"][0]; self.selected=pid
        conn=get_connection(); cur=conn.cursor()
        cur.execute("SELECT name,brand_id,price,stock,description,image,is_featured,size_chart FROM products WHERE id=?",(pid,)); p=cur.fetchone()
        cur.execute("SELECT category_id FROM product_categories WHERE product_id=?",(pid,)); cats={x[0] for x in cur.fetchall()}; conn.close()
        self.chart_saved=p[7];self.chart_new=None
        self.chart_status.configure(text="ใช้ภาพตารางไซซ์เฉพาะสินค้า" if p[7] else "ใช้ตารางอัตโนมัติตามประเภทไซซ์")
        self.name.delete(0,tk.END); self.name.insert(0,p[0])
        self.brand.set(next((n for i,n in self.brands if i==p[1]),""))
        self.price.delete(0,tk.END); self.price.insert(0,p[2])
        self.stock.delete(0,tk.END); self.stock.insert(0,p[3])
        self.desc.delete("1.0",tk.END); self.desc.insert("1.0",p[4] or "")
        self.image.delete(0,tk.END); self.image.insert(0,p[5] or "")
        self.gallery_paths=images_for(pid,p[5]); self.gallery_new=[]; self.gallery_index=0; self.render_gallery()
        kind=cur_kind=None
        c=get_connection()
        kind=c.execute("SELECT size_type FROM products WHERE id=?",(pid,)).fetchone()[0]
        variants=c.execute("SELECT size,stock FROM product_variants WHERE product_id=? ORDER BY id",(pid,)).fetchall()
        c.close()
        self.size_type.set(kind);self.size_editor.previous_kind=kind
        self.size_editor.set_values(variants)
        self.featured.set(p[6]); self.cats.selection_clear(0,tk.END)
        for i,c in enumerate(self.categories):
            if c[0] in cats:self.cats.selection_set(i)

    # def update: ตรวจข้อมูลและปรับสินค้า หมวด รูป ไซซ์ในธุรกรรมเดียว
    def update(self):
        if not self.selected: messagebox.showwarning("ข้อมูล","กรุณาเลือกสินค้า"); return
        try: vals=self.values()
        except ValueError as e: messagebox.showwarning("ข้อมูล",str(e)); return
        conn=get_connection(); cur=conn.cursor()
        try:
            cur.execute("""UPDATE products SET name=?,brand_id=?,price=?,stock=?,description=?,image=?,is_featured=? WHERE id=?""",(*vals[:7],self.selected))
            cur.execute("DELETE FROM product_categories WHERE product_id=?",(self.selected,))
            cur.executemany("INSERT INTO product_categories(product_id,category_id) VALUES(?,?)",[(self.selected,c) for c in vals[7]])
            self.persist_gallery(conn,self.selected)
            self.save_variants(conn,self.selected)
            conn.commit()
        except Exception as exc:
            conn.rollback();messagebox.showerror("บันทึกสินค้า",str(exc));return
        finally:conn.close()
        messagebox.showinfo("สำเร็จ","แก้ไขสินค้าแล้ว"); self.clear(); self.load(); return True

    # def delete: ยืนยันก่อนลบสินค้า; แจ้งข้อผิดพลาดเมื่อสินค้ามีความสัมพันธ์ที่ลบไม่ได้
    def delete(self):
        if not self.selected: messagebox.showwarning("ข้อมูล","กรุณาเลือกสินค้า"); return
        if not messagebox.askyesno("ยืนยัน","ต้องการลบสินค้านี้หรือไม่?"): return
        conn=get_connection(); cur=conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE id=?",(self.selected,)); conn.commit()
            messagebox.showinfo("สำเร็จ","ลบสินค้าแล้ว")
        except Exception as e:
            conn.rollback(); messagebox.showerror("ลบไม่ได้","สินค้านี้อาจอยู่ในคำสั่งซื้อแล้ว\n"+str(e))
        finally: conn.close()
        self.clear(); self.load(); return True

    # def clear: ล้างข้อมูลฟอร์มและการเลือก เพื่อเริ่มรายการใหม่
    def clear(self):
        self.reset_chart()
        self.size_type.set("none");self.size_editor.previous_kind="none";self.size_editor.set_values([])
        self.selected=None; self.new_image=None; self.gallery_paths=[]; self.gallery_new=[]; self.gallery_index=0; self.render_gallery()
        self.name.delete(0,tk.END); self.brand.set(""); self.price.delete(0,tk.END); self.stock.delete(0,tk.END)
        self.desc.delete("1.0",tk.END); self.image.delete(0,tk.END); self.featured.set(0); self.cats.selection_clear(0,tk.END)
        for x in self.tree.selection(): self.tree.selection_remove(x)

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        self.frame.destroy(); self.back_callback()
