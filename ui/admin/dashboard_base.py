from ui.modern_widgets import ActionButton,RoundedCard
"""หน้า Admin Dashboard พร้อมรายงานจากฐานข้อมูลจริง"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from database.database import get_connection
from services.analytics import dashboard_data,date_range,local_day
from ui.customer_style import scroll_body
from ui.date_picker import pick_date
from ui.admin.products import AdminProductsPage
from ui.admin.orders import AdminOrdersPage

NAVY='#14253D';BLUE='#4942F6';BG='#F3F5FA';MUTED='#6B778C';WHITE='white'

class AdminDashboard:
    def __init__(self,root,logout_callback,admin_id=None):
        self.root=root;self.logout_callback=logout_callback;self.admin_id=admin_id
        self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True);self.build()

    def label(self,parent,text,size=11,bold=False,fg=NAVY):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=fg,font=('Noto Sans Thai',size,'bold' if bold else 'normal'),anchor='w')

    def button(self,parent,text,command,primary=True):
        return ActionButton(parent,text=text,command=command,bg=BLUE if primary else '#E9EAF5',
            fg=WHITE if primary else NAVY,activebackground='#3530D0',activeforeground=WHITE,
            bd=0,padx=12,pady=7,cursor='hand2',font=('Noto Sans Thai',10))

    def panel(self,parent,title):
        frame=RoundedCard(parent,bg=WHITE,highlightbackground='#DCE2ED',highlightthickness=1,padx=20,pady=18)
        frame.pack(fill='x',pady=(0,18))
        self.label(frame,title,16,True).pack(anchor='w',pady=(0,12))
        return frame

    def build(self):
        self.frame.configure(bg=BG)
        side=tk.Frame(self.frame,bg=NAVY,width=205);side.pack(side='left',fill='y');side.pack_propagate(False)
        self.label(side,'TRI\nGEAR',23,True,WHITE).pack(anchor='w',padx=24,pady=(28,32))
        for title,action in [('ภาพรวมร้านค้า',self.back),('จัดการสินค้า',self.products),('คำสั่งซื้อ / สลิป',self.orders),
            ('จัดการสมาชิก',self.members),('คำขอรีเซ็ตรหัส',self.password_resets),('ตั้งค่าอีเมล OTP',self.email_settings),('ออกจากระบบ',self.logout_callback)]:
            ActionButton(side,text=title,command=action,bg=BLUE if title=='ภาพรวมร้านค้า' else NAVY,fg=WHITE,
                activebackground='#263B59',activeforeground=WHITE,bd=0,anchor='w',padx=22,pady=13,
                cursor='hand2',font=('Noto Sans Thai',11)).pack(fill='x',pady=3)
        body=scroll_body(self.frame);body.configure(bg=BG)
        content=tk.Frame(body,bg=BG,padx=24,pady=24);content.pack(fill='both',expand=True)
        self.label(content,'Admin Dashboard',26,True).pack(anchor='w')
        self.label(content,'ภาพรวมยอดขายและคำสั่งซื้อของ TRIGEAR',11,fg=MUTED).pack(anchor='w',pady=(4,14))
        conn=get_connection()
        try:pending=conn.execute("SELECT COUNT(*) FROM password_reset_requests WHERE status='pending'").fetchone()[0]
        finally:conn.close()
        self.button(content,f'คำขอรีเซ็ตรหัสรอดำเนินการ {pending} รายการ  →',self.password_resets).pack(anchor='w',pady=(0,16))
        self.card_box=tk.Frame(content,bg=BG);self.card_box.pack(fill='x',pady=(0,18))
        self.card_values=[];self.cards=[]
        for i,title in enumerate(['สินค้าทั้งหมด','คำสั่งซื้อทั้งหมด','ลูกค้า','รับชำระรวม VAT','รับชำระหักคืนเงิน']):
            self.card_box.columnconfigure(i,weight=1,uniform='cards')
            card=RoundedCard(self.card_box,bg=WHITE,highlightbackground='#DCE2ED',highlightthickness=1,padx=10,pady=15)
            self.cards.append(card)
            card.grid(row=0,column=i,sticky='nsew',padx=(0,8))
            self.label(card,title,10,fg=MUTED).pack(anchor='w')
            val=self.label(card,'—',19,True);val.pack(anchor='w',pady=(10,0));self.card_values.append(val)
        self.card_box.bind('<Configure>',self.reflow_cards)
        chart=self.panel(content,'ยอดขายรวมและแนวโน้มยอดขาย')
        self.start=tk.StringVar();self.end=tk.StringVar();a,b=date_range('เดือนนี้');self.start.set(str(a));self.end.set(str(b))
        self.range_controls(chart,self.start,self.end,self.refresh)
        self.money_label=self.label(chart,'',11,fg=MUTED);self.money_label.pack(fill='x',pady=(8,5))
        self.money_label.bind('<Configure>',lambda e:self.money_label.configure(wraplength=max(200,e.width-10)))
        self.label(chart,'ยอดรับชำระอ้างอิงวันสร้างออเดอร์ • คืนเงินอ้างอิงวันที่คืนเงินจริง',10,fg=MUTED).pack(anchor='w')
        modes=tk.Frame(chart,bg=WHITE);modes.pack(anchor='w',pady=10)
        self.mode=tk.StringVar(value='ยอดขายรวม')
        for title in ('ยอดขายรวม','จำนวนออเดอร์'):
            tk.Radiobutton(modes,text=title,value=title,variable=self.mode,command=self.draw_chart,bg=WHITE,fg=NAVY,selectcolor='#E9E8FF').pack(side='left',padx=(0,18))
        self.chart=tk.Canvas(chart,height=285,bg=WHITE,highlightthickness=0);self.chart.pack(fill='x')
        self.chart.bind('<Configure>',lambda e:self.draw_chart())
        self.status_panel=self.panel(content,'สถานะคำสั่งซื้อในช่วงวันที่ที่เลือก')
        self.status_box=tk.Frame(self.status_panel,bg=WHITE);self.status_box.pack(fill='x')
        best=self.panel(content,'อันดับสินค้าขายดี · 10 อันดับ')
        self.best_start=tk.StringVar(value=str(a));self.best_end=tk.StringVar(value=str(b))
        self.range_controls(best,self.best_start,self.best_end,self.refresh_best)
        filters=tk.Frame(best,bg=WHITE);filters.pack(fill='x',pady=10)
        self.label(filters,'เรียงตาม').pack(side='left')
        self.rank=tk.StringVar(value='จำนวนชิ้น');box=ttk.Combobox(filters,textvariable=self.rank,values=['จำนวนชิ้น','มูลค่าสินค้า'],state='readonly',width=16);box.pack(side='left',padx=8);box.bind('<<ComboboxSelected>>',lambda e:self.refresh_best())
        self.category=tk.StringVar(value='สินค้าทั้งหมด');self.category_box=ttk.Combobox(filters,textvariable=self.category,state='readonly',width=24);self.category_box.pack(side='left',padx=8);self.category_box.bind('<<ComboboxSelected>>',lambda e:self.refresh_best())
        self.button(filters,'ล้างตัวกรอง',self.reset_best,False).pack(side='left')
        cols=('rank','name','qty','money');self.best_tree=ttk.Treeview(best,columns=cols,show='headings',height=10)
        for key,title,width in [('rank','อันดับ',65),('name','สินค้า',340),('qty','จำนวนชิ้น',100),('money','มูลค่าก่อน VAT',160)]:
            self.best_tree.heading(key,text=title);self.best_tree.column(key,width=width,minwidth=50,anchor='w' if key=='name' else 'center')
        self.best_tree.pack(fill='x');self.best_note=self.label(best,'',10,fg=MUTED);self.best_note.pack(anchor='w',pady=(8,0))
        self.label(best,'รวมทุกไซส์ของสินค้าเดียวกัน • นับเฉพาะชำระแล้วและไม่ยกเลิก • มูลค่าจากราคาในคำสั่งซื้อ',10,fg=MUTED).pack(anchor='w')
        self.refresh();self.refresh_best()

    def reflow_cards(self,event):
        columns=5 if event.width>=1100 else 3
        for col in range(5):self.card_box.columnconfigure(col,weight=1 if col<columns else 0,uniform='cards' if col<columns else '')
        for i,card in enumerate(self.cards):card.grid(row=i//columns,column=i%columns,sticky='nsew',padx=(0,8),pady=(0,8))

    def range_controls(self,parent,start,end,refresh):
        row=tk.Frame(parent,bg=WHITE);row.pack(fill='x')
        for text,var in [('จาก',start),('ถึง',end)]:
            self.label(row,text).pack(side='left',padx=(0,5))
            field=ttk.Entry(row,textvariable=var,width=11);field.pack(side='left');field.bind('<Return>',lambda e:refresh())
            self.button(row,'ปฏิทิน',lambda v=var:pick_date(self.root,v),False).pack(side='left',padx=(4,10))
        self.button(row,'แสดง',refresh).pack(side='left')
        presets=tk.Frame(parent,bg=WHITE);presets.pack(anchor='w',pady=(8,0))
        for title in ['วันนี้','เดือนนี้','ปีนี้']:
            def choose(t=title):
                a,b=date_range(t);start.set(str(a));end.set(str(b));refresh()
            self.button(presets,title,choose,False).pack(side='left',padx=(0,8))
        self.label(presets,'รูปแบบวันที่ YYYY-MM-DD',10,fg=MUTED).pack(side='left')

    def refresh(self):
        try:data=dashboard_data(self.admin_id,self.start.get(),self.end.get())
        except ValueError as exc:messagebox.showwarning('รายงาน',str(exc));return
        self.data=data
        self.report_start=date.fromisoformat(self.start.get());self.report_end=date.fromisoformat(self.end.get())
        vals=[str(data['counts']['products']),str(data['counts']['orders']),str(data['counts']['customers']),f"฿{data['gross']:,.2f}",f"฿{data['net']:,.2f}"]
        for w,v in zip(self.card_values,vals):w.config(text=v)
        self.money_label.config(text=f"ก่อน VAT ฿{data['subtotal']:,.2f}   |   VAT ฿{data['vat']:,.2f}   |   คืนแล้ว ฿{data['refunds']:,.2f}   |   ชำระแล้ว {data['paid_count']} ออเดอร์")
        for w in self.status_box.winfo_children():w.destroy()
        statuses=['กำลังตรวจสอบ','ยืนยันคำสั่งซื้อ','กำลังจัดส่ง','จัดส่งสำเร็จ','รับสินค้าแล้ว','สถานะถูกยกเลิก - รอคืนเงิน','คืนเงินสำเร็จ','ยกเลิกแล้ว']
        statuses+=sorted(set(data['statuses'])-set(statuses))
        for i,status in enumerate(statuses):
            self.status_box.columnconfigure(i%3,weight=1,uniform='status')
            button=self.button(self.status_box,f"{status}  ({data['statuses'].get(status,0)})",lambda s=status:self.status_orders(s),False)
            button.configure(wraplength=200,height=2);button.grid(row=i//3,column=i%3,sticky='ew',padx=4,pady=4)
        self.draw_chart()

    def refresh_best(self):
        cat=getattr(self,'category_map',{}).get(self.category.get())
        try:data=dashboard_data(self.admin_id,self.best_start.get(),self.best_end.get(),cat,'quantity' if self.rank.get()=='จำนวนชิ้น' else 'revenue')
        except ValueError as exc:messagebox.showwarning('สินค้าขายดี',str(exc));return
        self.category_map={'สินค้าทั้งหมด':None,**{f'{name} (#{cid})':cid for cid,name in data['categories']}}
        self.category_box.configure(values=list(self.category_map))
        self.best_tree.delete(*self.best_tree.get_children())
        for i,row in enumerate(data['best'],1):self.best_tree.insert('','end',values=(i,row['name'],row['quantity'],f"฿{row['revenue']:,.2f}"))
        self.best_note.config(text=f"ช่วง {self.best_start.get()} ถึง {self.best_end.get()}"+(' · ไม่มีสินค้าที่เข้าเงื่อนไข' if not data['best'] else ''))

    def reset_best(self):
        a,b=date_range('เดือนนี้');self.best_start.set(str(a));self.best_end.set(str(b));self.category.set('สินค้าทั้งหมด');self.rank.set('จำนวนชิ้น');self.refresh_best()

    def draw_chart(self):
        if not hasattr(self,'data'):return
        c=self.chart;c.delete('all');width=max(c.winfo_width(),400);height=285;left=75;right=width-20;top=28;bottom=225
        rows=list(self.data['trend'].items());money=self.mode.get()=='ยอดขายรวม'
        values=[float(v['sales'] if money else v['orders']) for k,v in rows];maximum=max(values+[1])
        if money:maximum=max(maximum,max([float(v['refunds']) for k,v in rows]+[0]))
        for i in range(5):
            y=bottom-(bottom-top)*i/4;v=maximum*i/4
            c.create_line(left,y,right,y,fill='#E8EDF5');c.create_text(left-10,y,text=f'{v:,.0f}',anchor='e',fill=MUTED,font=('Noto Sans Thai',9))
        c.create_text(left,12,text='บาท (รวม VAT) · น้ำเงิน: รับชำระ / ส้ม: คืนเงินจริง' if money else 'จำนวนออเดอร์ทั้งหมดที่สร้าง',anchor='w',fill=MUTED,font=('Noto Sans Thai',10))
        n=len(rows);xs=[left+(right-left)*(i+.5)/max(n,1) for i in range(n)]
        def series(vals,color):
            coords=[]
            for x,v in zip(xs,vals):coords.extend([x,bottom-(bottom-top)*v/maximum])
            if len(coords)>=4:c.create_line(*coords,fill=color,width=3)
            if n<=32:
                for x,v in zip(xs,vals):
                    y=bottom-(bottom-top)*v/maximum;c.create_oval(x-3,y-3,x+3,y+3,fill=color,outline=WHITE)
        series(values,BLUE)
        if money:series([float(v['refunds']) for k,v in rows],'#F59E0B')
        step=max(1,(n+7)//8)
        for i,(key,v) in enumerate(rows):
            if i%step==0 or i==n-1:c.create_text(xs[i],bottom+18,text=key[5:] if self.data['bucket']=='day' else key,fill=MUTED,font=('Noto Sans Thai',9))
        c.create_text((left+right)/2,277,text={'day':'รายวัน','month':'รายเดือน','year':'รายปี'}[self.data['bucket']],fill=MUTED)
        if not any(values):c.create_text((left+right)/2,110,text='ไม่มีข้อมูลในช่วงวันที่ที่เลือก',fill=MUTED,font=('Noto Sans Thai',12))
        def hover(e):
            if not xs:return
            i=min(range(len(xs)),key=lambda j:abs(xs[j]-e.x));key,v=rows[i]
            c.delete('tooltip');text=f"{key}  |  "+(f"รับชำระ ฿{v['sales']:,.2f} / คืน ฿{v['refunds']:,.2f}" if money else f"{v['orders']} ออเดอร์")
            c.create_text(right,top,text=text,anchor='ne',fill=NAVY,font=('Noto Sans Thai',10,'bold'),tags='tooltip')
        c.bind('<Motion>',hover);c.bind('<Leave>',lambda e:c.delete('tooltip'))

    def status_orders(self,status):
        start=self.report_start;end=self.report_end
        conn=get_connection()
        try:rows=conn.execute('SELECT id,order_date,total_price,payment_status FROM orders WHERE order_status=? ORDER BY id DESC',(status,)).fetchall()
        finally:conn.close()
        rows=[r for r in rows if start<=local_day(r[1])<=end]
        win=tk.Toplevel(self.root);win.title(status);win.geometry('750x450')
        self.label(win,f'{status} · {len(rows)} รายการ',15,True).pack(pady=12)
        tree=ttk.Treeview(win,columns=('id','date','money','payment'),show='headings')
        for key,title in [('id','Order'),('date','วันที่'),('money','ยอดรวม VAT'),('payment','การชำระเงิน')]:tree.heading(key,text=title);tree.column(key,width=160)
        bar=ttk.Scrollbar(win,command=tree.yview);bar.pack(side='right',fill='y');tree.configure(yscrollcommand=bar.set);tree.pack(fill='both',expand=True,padx=12)
        for oid,stamp,total,payment in rows:tree.insert('','end',iid=str(oid),values=(oid,stamp,f'{total:,.2f}',payment))
        def open_order():
            selected=tree.selection()
            if not selected:return
            oid=int(selected[0]);win.destroy();self.frame.destroy();page=AdminOrdersPage(self.root,self.back);page.select_order(oid)
        self.button(win,'เปิดคำสั่งซื้อที่เลือก',open_order).pack(pady=12);tree.bind('<Double-1>',lambda e:open_order())

    # def members: เปิดหน้าจัดการสมาชิกพร้อมรหัส Admin ปัจจุบัน
    def members(self):
        from ui.admin.members import AdminMembersPage
        self.frame.destroy();AdminMembersPage(self.root,self.admin_id,self.back)

    # def password_resets: เปิดรายการคำขอรีเซ็ตพร้อมรหัส Admin ปัจจุบัน
    def password_resets(self):
        from ui.admin.password_resets import AdminPasswordResetsPage
        self.frame.destroy(); AdminPasswordResetsPage(self.root,self.admin_id,self.back)

    # def products: เปิดหน้าจัดการสินค้าแล้วส่ง callback สำหรับกลับ Dashboard
    def products(self):
        self.frame.destroy(); AdminProductsPage(self.root,self.back)

    # def orders: เปิดหน้าคำสั่งซื้อของบทบาทที่ใช้งานหน้านี้
    def orders(self):
        self.frame.destroy(); AdminOrdersPage(self.root,self.back)

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        # Refresh the dashboard without stacking a second page over the first.
        if self.frame.winfo_exists():
            self.frame.destroy()
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)
        self.build()

    def email_settings(self):
        from ui.email_settings import show_email_settings
        show_email_settings(self.root,self.admin_id)
