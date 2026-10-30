"""Modern admin overview driven exclusively by the existing analytics service."""
import tkinter as tk
from tkinter import ttk,messagebox
from datetime import date
from database.database import get_connection
from database.stock_alerts import low_stock_rows
from services.analytics import dashboard_data,date_range
from ui.admin.dashboard_base import AdminDashboard as DashboardReports
from ui.admin.modern_style import *

class AdminDashboard(DashboardReports):
    def __init__(self,root,logout_callback,admin_id=None):
        self.root=root;self.logout_callback=logout_callback;self.admin_id=admin_id;self.back_callback=self.back
        root._admin_context={'id':admin_id,'logout':logout_callback}
        self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True);self.build()

    def build(self):
        main=chrome(self,'ภาพรวมร้านค้า','ติดตามยอดขายและรายการที่ต้องดูแล','home')
        outer,canvas,body=scroll_area(main);outer.pack(fill='both',expand=True)
        content=tk.Frame(body,bg=BG,padx=22,pady=4);content.pack(fill='both',expand=True)
        self.card_values=metrics(content,[('ยอดรับชำระรวม VAT','—'),('คำสั่งซื้อในช่วงวันที่','—'),('รอตรวจสลิปทั้งหมด','—'),('สินค้า/ไซส์ใกล้หมด','—')])
        self.start=tk.StringVar();self.end=tk.StringVar();a,b=date_range('เดือนนี้');self.start.set(str(a));self.end.set(str(b))
        filters=panel(content);filters.pack(fill='x',pady=(0,16));self.range_controls(filters,self.start,self.end,self.refresh)
        self.money_label=tk.Label(filters,text='',bg=WHITE,fg=MUTED,font=('Noto Sans Thai',10),anchor='w',justify='left',wraplength=700);self.money_label.pack(fill='x',padx=16,pady=(4,12))
        layout=tk.Frame(content,bg=BG);layout.pack(fill='x')
        layout.columnconfigure(0,weight=3);layout.columnconfigure(1,weight=2)
        chart=panel(layout);chart.grid(row=0,column=0,sticky='nsew',padx=(0,12))
        status=panel(layout);status.grid(row=0,column=1,sticky='nsew')
        label(chart,'แนวโน้มยอดขาย',19,True,anchor='w').pack(fill='x',padx=18,pady=(16,8))
        self.mode=tk.StringVar(value='ยอดขายรวม');menu(chart,self.mode,['ยอดขายรวม','จำนวนออเดอร์'],lambda v:self.draw_chart(),190).pack(anchor='w',padx=18,pady=(0,6))
        self.chart=tk.Canvas(chart,bg=WHITE,height=285,highlightthickness=0);self.chart.pack(fill='x',padx=12,pady=(0,10));self.chart.bind('<Configure>',lambda e:self.draw_chart())
        label(status,'สถานะคำสั่งซื้อ',19,True,anchor='w').pack(fill='x',padx=18,pady=(16,8))
        self.status_box=tk.Frame(status,bg=WHITE);self.status_box.pack(fill='both',expand=True,padx=14,pady=(0,16))
        state={'wide':None}
        def adapt(e):
            wide=e.width>=1050
            if state['wide']==wide:return
            state['wide']=wide
            chart.grid_configure(row=0,column=0,columnspan=1 if wide else 2,padx=(0,12) if wide else 0)
            status.grid_configure(row=0 if wide else 1,column=1 if wide else 0,columnspan=1 if wide else 2,pady=0 if wide else (14,0))
        layout.bind('<Configure>',adapt,add='+')
        best=panel(content);best.pack(fill='x',pady=16)
        label(best,'สินค้าขายดี · 10 อันดับ',20,True,anchor='w').pack(fill='x',padx=18,pady=(16,8))
        self.best_start=tk.StringVar(value=str(a));self.best_end=tk.StringVar(value=str(b));self.range_controls(best,self.best_start,self.best_end,self.refresh_best)
        row=tk.Frame(best,bg=WHITE);row.pack(fill='x',padx=18,pady=12)
        self.rank=tk.StringVar(value='จำนวนชิ้น');menu(row,self.rank,['จำนวนชิ้น','มูลค่าสินค้า'],lambda v:self.refresh_best(),160).pack(side='left',padx=(0,8))
        self.category=tk.StringVar(value='สินค้าทั้งหมด');self.category_box=menu(row,self.category,['สินค้าทั้งหมด'],lambda v:self.refresh_best(),220);self.category_box.pack(side='left')
        button(row,'ล้างตัวกรอง',self.reset_best,'secondary',width=120).pack(side='left',padx=8)
        box,self.best_tree=table(best,[('rank','อันดับ',70),('name','สินค้า',350),('qty','จำนวนชิ้น',100),('money','มูลค่าก่อน VAT',150)],5);box.pack(fill='x',padx=18)
        self.best_note=tk.Label(best,bg=WHITE,fg=MUTED,font=('Noto Sans Thai',10),anchor='w');self.best_note.pack(fill='x',padx=18,pady=12)
        low=panel(content);low.pack(fill='x',pady=(0,18))
        label(low,'สินค้า/ไซส์ใกล้หมด · เหลือไม่เกิน 3 ชิ้น',19,True,anchor='w').pack(fill='x',padx=18,pady=14)
        self.low_box=tk.Frame(low,bg=WHITE);self.low_box.pack(fill='x',padx=18)
        button(low,'จัดการสินค้า',self.products,'secondary').pack(anchor='e',padx=18,pady=14)
        self.refresh();self.refresh_best()

    def range_controls(self,parent,start,end,refresh):
        from ui.date_picker import pick_date
        row=tk.Frame(parent,bg=WHITE);row.pack(fill='x',padx=16,pady=(12,6))
        for title,var in [('จาก',start),('ถึง',end)]:
            label(row,title,13).pack(side='left',padx=(0,5));field=entry(row,var,125);field.pack(side='left');field.bind('<Return>',lambda e:refresh())
            button(row,'ปฏิทิน',lambda v=var:pick_date(self.root,v),'secondary',width=78).pack(side='left',padx=6)
        button(row,'แสดง',refresh,width=85).pack(side='left',padx=6)
        presets=tk.Frame(parent,bg=WHITE);presets.pack(anchor='w',padx=16,pady=(0,6))
        for title in ['วันนี้','เดือนนี้','ปีนี้']:
            def choose(t=title):
                a,b=date_range(t);start.set(str(a));end.set(str(b));refresh()
            button(presets,title,choose,'secondary',width=95).pack(side='left',padx=(0,8))

    def refresh(self):
        try:data=dashboard_data(self.admin_id,self.start.get(),self.end.get())
        except ValueError as exc:messagebox.showwarning('รายงาน',str(exc));return
        self.data=data;self.report_start=date.fromisoformat(self.start.get());self.report_end=date.fromisoformat(self.end.get())
        with get_connection() as conn:pending=conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status='รอตรวจสอบสลิป'").fetchone()[0]
        low=low_stock_rows()
        for w,value in zip(self.card_values,[f"฿{data['gross']:,.2f}",data['order_count'],pending,sum(r[3]>0 for r in low)]):w.configure(text=str(value))
        self.money_label.configure(text=f"ก่อน VAT ฿{data['subtotal']:,.2f} · VAT ฿{data['vat']:,.2f} · คืนแล้ว ฿{data['refunds']:,.2f} · รับชำระหักคืนเงิน ฿{data['net']:,.2f}\nยอดรับชำระอ้างอิงวันสร้างออเดอร์ · คืนเงินอ้างอิงวันที่คืนจริง")
        for w in self.status_box.winfo_children():w.destroy()
        colors=['#4145F1','#22B887','#E7A321','#EB5867','#7794CF','#9B77D0','#4BA6A5','#A5AFBF'];items=list(data['statuses'].items());total=sum(v for _,v in items)
        donut=tk.Canvas(self.status_box,width=200,height=170,bg=WHITE,highlightthickness=0);donut.pack()
        angle=90
        for i,(name,count) in enumerate(items):
            extent=360*count/max(1,total);donut.create_arc(35,8,175,148,start=angle,extent=extent,fill=colors[i%len(colors)],outline=WHITE);angle+=extent
        if not total:donut.create_oval(35,8,175,148,fill='#EEF0F7',outline='')
        donut.create_oval(62,35,148,121,fill=WHITE,outline=WHITE);donut.create_text(105,77,text=str(total),font=('Noto Sans Thai',25,'bold'),fill=NAVY)
        for i,(name,count) in enumerate(items):button(self.status_box,f'{name} ({count})',lambda s=name:self.status_orders(s),'secondary').pack(fill='x',pady=3)
        if not items:label(self.status_box,'ไม่มีคำสั่งซื้อในช่วงวันที่นี้',14,color=MUTED).pack(pady=12)
        for w in self.low_box.winfo_children():w.destroy()
        for pid,name,size,stock,status in low[:5]:
            label(self.low_box,f'{name} {"· ไซส์ "+size if size else ""} — เหลือ {stock} ชิ้น',14,color='#B82A3C' if stock==0 else '#996000',anchor='w',wraplength=720).pack(fill='x',pady=5)
        if not low:label(self.low_box,'ไม่มีสินค้าใกล้หมด',14,color=MUTED).pack(anchor='w')
        self.draw_chart()
