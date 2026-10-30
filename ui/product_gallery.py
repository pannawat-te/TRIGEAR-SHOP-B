# ไฟล์นี้: จัดภาพย่อแนวตั้ง และเปิดภาพที่เหลือเมื่อมีมากกว่า 4 ภาพ
import tkinter as tk
from ui.image_utils import photo
from ui.customer_style import scroll_body

# def thumbnail_slots: ถ้าเกิน 4 ภาพ แสดง 3 ภาพแรก และช่อง +จำนวนภาพที่เหลือ
def thumbnail_slots(paths):
    return [(i,0) for i in range(len(paths))] if len(paths)<=4 else [(0,0),(1,0),(2,0),(3,len(paths)-3)]

# def show_gallery: เปิดภาพย่อทั้งหมดใน Popup เลื่อนด้วยล้อเมาส์ เลือกเพื่อเปลี่ยนภาพหลัก
def show_gallery(parent,paths,on_select):
    win=tk.Toplevel(parent);win.title(f'รูปสินค้า ({len(paths)} ภาพ)');win.transient(parent.winfo_toplevel());win.geometry('660x560')
    tk.Label(win,text='เลือกรูปเพื่อแสดงในหน้ารายละเอียดสินค้า',font=('Noto Sans Thai',13,'bold')).pack(pady=12)
    tk.Button(win,text='ปิด',command=win.destroy).pack(side='bottom',pady=10)
    body=scroll_body(win)
    # def select: ส่งหมายเลขรูปกลับไปยังภาพหลักแล้วปิด Popup
    def select(index):on_select(index);win.destroy()
    for index,path in enumerate(paths):
        picture=photo(path,(180,160))
        button=tk.Button(body,image=picture,text=f'{index+1} / {len(paths)}',compound='top',command=lambda n=index:select(n),bg='white',padx=4,pady=4)
        button.image=picture;button.grid(row=index//3,column=index%3,padx=8,pady=8)
    for col in range(3):body.grid_columnconfigure(col,weight=1)
