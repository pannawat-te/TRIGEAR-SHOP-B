from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: หน้าติดต่อร้านตามแบบ โลโก้ซ้าย ข้อมูลร้านและช่องทาง Admin ขวา
import tkinter as tk
from tkinter import messagebox
import webbrowser
from ui.customer_style import header,scroll_body
from ui.brand import logo

# คลาส ContactPage: แสดงข้อมูลที่ผู้ใช้ให้ โดยไม่เดาลิงก์บัญชี Facebook/LINE
class ContactPage:
    # def __init__: สร้างสองคอลัมน์และปุ่มคัดลอกข้อมูลติดต่อ
    def __init__(self,root,back_callback,user_id=None,username=None):
        self.root=root;self.back_callback=back_callback;self.user_id=user_id;self.username=username
        self.frame=tk.Frame(root,bg='#F3F5F9');self.frame.pack(fill='both',expand=True)
        if user_id is not None:
            from ui.shop_style import customer_header,heading
            customer_header(self.frame,user_id,self,active='contact')
            heading(self.frame,'ติดต่อ TRIGEAR')
        else:header(self.frame,'ติดต่อร้านค้า / Contact',self.back)
        body=scroll_body(self.frame)
        shell=tk.Frame(body,bg='#F3F5F9');shell.pack(fill='x',padx=45,pady=45)
        shell.grid_columnconfigure(0,weight=1);shell.grid_columnconfigure(1,weight=1)
        left=RoundedCard(shell,bg='white',padx=22,pady=45,highlightbackground='#DCE5F0',highlightthickness=1)
        left.grid(row=0,column=0,padx=(0,24))
        picture=logo((300,180));label=tk.Label(left,image=picture,bg='white');label.image=picture;label.pack()
        right=RoundedCard(shell,bg='white',padx=24,pady=30,highlightbackground='#DCE5F0',highlightthickness=1)
        right.grid(row=0,column=1,sticky='nsew')
        tk.Label(right,text='ที่อยู่ร้าน   เมืองขอนแก่น 40000',bg='white',font=('Noto Sans Thai',15,'bold'),wraplength=420,justify='left').pack(anchor='w',pady=12)
        phone=tk.Frame(right,bg='white');phone.pack(fill='x',pady=12)
        tk.Label(phone,text='เบอร์โทร',bg='white',font=('Noto Sans Thai',13,'bold')).pack(side='left')
        tk.Label(phone,text='0956466576',bg='white',fg='#4145F1',font=('Noto Sans Thai',16,'bold')).pack(side='left',padx=12)
        ActionButton(phone,text='คัดลอก',command=self.copy_phone,bg='#4145F1',fg='white').pack(side='left')
        tk.Label(right,text='ติดต่อ ADMIN ได้ที่',bg='white',font=('Noto Sans Thai',16,'bold')).pack(anchor='w',pady=(30,12))
        for label,value,color in [('Facebook','Pannawat Temjai','#0866FF'),('LINE','0956466576','#15803D'),('Instagram','c._pannawat_.r','#A21CAF')]:
            command=(lambda:webbrowser.open('https://www.instagram.com/c._pannawat_.r/')) if label=='Instagram' else (lambda v=value:self.copy_value(v))
            ActionButton(right,text=f'{label}: {value}',command=command,bg=color,fg='white',activebackground=color,activeforeground='white',anchor='w',font=('Noto Sans Thai',12,'bold'),padx=14,pady=12).pack(fill='x',pady=5)
        tk.Label(right,text='Facebook / LINE: คลิกเพื่อคัดลอก\nInstagram: คลิกเพื่อเปิดโปรไฟล์',bg='white',fg='#64748B',justify='left').pack(anchor='w',pady=12)
        ActionButton(right,text='กลับหน้าร้านค้า',command=self.back).pack(pady=12)
    # def copy_value: คัดลอกข้อมูลช่องทางที่เลือกไป Clipboard
    def copy_value(self,value):
        self.root.clipboard_clear();self.root.clipboard_append(value);messagebox.showinfo('ติดต่อร้าน','คัดลอกข้อมูลแล้ว')
    # def copy_phone: คัดลอกเบอร์โทรร้าน
    def copy_phone(self):self.copy_value('0956466576')
    # def back: กลับหน้าร้านโดยคงข้อมูลบัญชีและตะกร้า
    def back(self):self.frame.destroy();self.back_callback()
