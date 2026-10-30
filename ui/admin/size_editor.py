from ui.modern_widgets import ActionButton,RoundedCard
# ไฟล์นี้: ดรอปดาวน์ไซซ์สำเร็จรูป เพิ่มไซซ์เอง และกรอกจำนวนรายไซซ์
"""Dropdown size rows with per-size stock and custom sizes."""
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from decimal import Decimal, InvalidOperation

PRESETS={'shoe_cm':[f'{n/2:.1f}' for n in range(44,61)],'clothing':['S','M','L','XL','XXL','XXXL'],'road_bike':[str(n) for n in range(40,64)]}

# def normalize_size: ปรับรูปแบบไซซ์ตามประเภท เช่น CM เป็นตัวเลข และชื่อไซซ์เสื้อเป็นตัวพิมพ์ใหญ่
def normalize_size(kind,label):
    label=label.strip()
    if kind=='road_bike':
        # Brand labels (XS, S...) remain valid alongside numerical frame sizes.
        try:
            value=Decimal(label)
        except InvalidOperation:
            value=None
        if value is not None:
            if not value.is_finite() or value<=0:raise ValueError('ไซซ์เฟรมต้องเป็นตัวเลขที่มากกว่า 0')
            return format(value.normalize(),'f')
    if kind=='shoe_cm':
        try:
            value=Decimal(label)
            if not value.is_finite() or value<=0:raise ValueError()
            return format(value.normalize(),'f')+('.0' if value==value.to_integral() else '')
        except (InvalidOperation,ValueError):raise ValueError('ไซซ์รองเท้าต้องเป็นตัวเลข CM ที่มากกว่า 0')
    label=label.upper()
    if not label or len(label)>24 or any(c in label for c in '\n\r='):
        raise ValueError('กรุณาระบุชื่อไซซ์ไม่เกิน 24 ตัวอักษร')
    return label

# def validate_rows: ตรวจไซซ์ไม่ซ้ำ จำนวนเต็มไม่ติดลบ และคืนรายการพร้อมบันทึก
def validate_rows(kind,rows):
    if kind=='none':return []
    result=[];seen=set()
    for label,quantity in rows:
        size=normalize_size(kind,label)
        try:stock=int(quantity)
        except ValueError:raise ValueError('จำนวนคงเหลือต้องเป็นจำนวนเต็ม')
        if stock<0:raise ValueError('Stock ต้องไม่ติดลบ')
        if size in seen:raise ValueError('มีไซซ์ซ้ำ: '+size)
        seen.add(size);result.append((size,stock))
    if not result:raise ValueError('กรุณาเพิ่มไซซ์อย่างน้อยหนึ่งรายการ')
    return result

# คลาส SizeEditor: เก็บข้อมูลและพฤติกรรมของ ดรอปดาวน์ไซซ์สำเร็จรูป เพิ่มไซซ์เอง และกรอกจำนวนรายไซซ์
class SizeEditor(tk.Frame):
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,parent,kind):
        super().__init__(parent);self.kind=kind;self.rows=[];self.custom=[];self.loaded=[]
        toolbar=tk.Frame(self);toolbar.pack(fill='x')
        ActionButton(toolbar,text='เพิ่มรายการไซซ์',command=self.add_row).pack(side='left',padx=4)
        ActionButton(toolbar,text='เพิ่มไซซ์อื่น',command=self.add_custom).pack(side='left',padx=4)
        self.summary=tk.Label(toolbar);self.summary.pack(side='left',padx=12)
        canvas=tk.Canvas(self,height=105,highlightthickness=0)
        scroll=ttk.Scrollbar(self,command=canvas.yview);scroll.pack(side='right',fill='y');canvas.pack(fill='x',expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        self.body=tk.Frame(canvas);win=canvas.create_window((0,0),window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
        self.canvas=canvas
        from ui.mouse_scroll import enable_mouse_scroll
        enable_mouse_scroll(canvas,self.body)
    # def choices: รวมไซซ์เริ่มต้น ไซซ์เพิ่มเอง และไซซ์ในฟอร์ม โดยตัดชื่อซ้ำ
    def choices(self):return list(dict.fromkeys(PRESETS.get(self.kind.get(),[])+self.custom+[r[1].get() for r in self.rows if r[1].get()]))
    # def add_row: เพิ่มหนึ่งแถวที่มีดรอปดาวน์ไซซ์ ช่องจำนวน และปุ่มลบ
    def add_row(self,size=None,stock=0):
        if self.kind.get()=='none':messagebox.showwarning('ประเภทไซซ์','เลือกประเภทรองเท้าหรือเสื้อผ้าก่อน');return
        choices=self.choices()
        if size is None:
            used={r[1].get() for r in self.rows};size=next((s for s in choices if s not in used),'')
        line=tk.Frame(self.body);line.pack(fill='x',pady=2)
        tk.Label(line,text='ไซซ์').pack(side='left',padx=4)
        label=tk.StringVar(value=size);count=tk.StringVar(value=str(stock))
        combo=ttk.Combobox(line,textvariable=label,values=choices,state='readonly',width=15);combo.pack(side='left',padx=4)
        tk.Label(line,text='จำนวน').pack(side='left',padx=6)
        ttk.Entry(line,textvariable=count,width=10).pack(side='left')
        row=(line,label,count,combo);self.rows.append(row)
        ActionButton(line,text='ลบ',command=lambda:self.remove(row)).pack(side='left',padx=8)
        count.trace_add('write',lambda *args:self.update_summary());self.refresh_choices();self.update_summary()
    # def remove: ลบรายการที่เลือกออกจากตะกร้าหรือฟอร์มของหน้านี้
    def remove(self,row):self.rows.remove(row);row[0].destroy();self.update_summary()
    # def refresh_choices: เติมรายการตัวเลือกล่าสุดให้ดรอปดาวน์ของทุกแถว
    def refresh_choices(self):
        for row in self.rows:row[3].configure(values=self.choices())
    # def update_summary: รวมจำนวนในฟอร์มและแสดงสรุปจำนวนไซซ์กับ Stock
    def update_summary(self):
        try:total=sum(int(row[2].get()) for row in self.rows);text=f'{len(self.rows)} ไซซ์ · รวม {total} ชิ้น'
        except ValueError:text='กรุณากรอกจำนวนเต็ม'
        self.summary.config(text=text)
    # def add_custom: รับชื่อไซซ์นอกชุดเริ่มต้น ตรวจสอบ และเพิ่มเป็นแถวใหม่
    def add_custom(self):
        if self.kind.get()=='none':messagebox.showwarning('ประเภทไซซ์','เลือกประเภทไซซ์ก่อน');return
        label=simpledialog.askstring('เพิ่มไซซ์อื่น','ระบุไซซ์เพิ่มเติม เช่น 64, 52.5 หรือ XS',parent=self)
        if label is None:return
        try:label=normalize_size(self.kind.get(),label)
        except ValueError as exc:messagebox.showwarning('ไซซ์',str(exc));return
        if label in [row[1].get() for row in self.rows]:messagebox.showwarning('ไซซ์','ไซซ์นี้มีอยู่แล้ว');return
        if label not in self.custom:self.custom.append(label)
        self.add_row(label)
    # def set_values: ล้างแถวเดิมแล้วโหลดไซซ์/จำนวนที่รับเข้ามา
    def set_values(self,values):
        for row in self.rows:row[0].destroy()
        self.rows=[];self.custom=[size for size,stock in values];self.loaded=list(values)
        for size,stock in values:self.add_row(size,stock)
        self.update_summary()
    # def change_kind: ยืนยันก่อนเปลี่ยนประเภทไซซ์และล้างแถว; ย้อนค่าประเภทเมื่อยกเลิก
    def change_kind(self,event=None):
        if self.rows:
            if not messagebox.askyesno('เปลี่ยนประเภทไซซ์','การเปลี่ยนประเภทจะล้างรายการไซซ์ในฟอร์มนี้ ต้องการดำเนินการหรือไม่?'):
                self.kind.set(self.previous_kind);return
        self.set_values([]);self.previous_kind=self.kind.get()
        if self.kind.get()!='none':self.add_row()
    # def values: ตรวจข้อมูลฟอร์ม และคืนค่าที่พร้อมบันทึกลงฐานข้อมูล
    def values(self):return validate_rows(self.kind.get(),[(r[1].get(),r[2].get()) for r in self.rows])
