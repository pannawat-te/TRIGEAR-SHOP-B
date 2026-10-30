# ไฟล์นี้: ส่วนหน้าตาที่ใช้ร่วมกัน: ช่องกรอก หัวหน้า พื้นที่เลื่อน และสีปุ่ม
"""Customer UI components; editable controls retain native Tk behavior."""
import tkinter as tk
import customtkinter as ctk
from ui.brand import logo, BLUE


# def entry: สร้างช่องกรอกเส้นใต้พร้อมเปลี่ยนสีเมื่อโฟกัส คืน Entry ให้ผู้เรียกใช้งาน
def entry(parent, **kwargs):
    """CTkEntry มุมมน โดยยังให้ผู้เรียกใช้ get/insert/field ตามเดิม"""
    password_chars_only=kwargs.pop('password_chars_only',False)
    width=kwargs.pop('width',25)
    field=tk.Frame(parent,bg='white')
    control=ctk.CTkEntry(field,width=max(120,int(width)*8),height=42,corner_radius=10,
        border_width=1,border_color='#DCE2EE',fg_color='white',text_color='#14253D',
        font=('Noto Sans Thai',15),**kwargs)
    control.pack(side='left',fill='x',expand=True)
    if password_chars_only:
        from database.password_policy import allowed_characters
        control.configure(validate='key',validatecommand=(control.register(allowed_characters),'%P'))
    if kwargs.get('show'):
        from PIL import Image,ImageDraw
        icon=Image.new('RGBA',(24,18));draw=ImageDraw.Draw(icon)
        draw.ellipse((2,3,22,15),outline='#64748B',width=2);draw.ellipse((9,6,15,12),fill='#64748B')
        picture=ctk.CTkImage(light_image=icon,dark_image=icon,size=(24,18))
        def toggle_password():
            visible=bool(control.cget('show'));control.configure(show='' if visible else '*')
            control.focus_set()
        eye=ctk.CTkButton(field,text='',image=picture,command=toggle_password,width=40,height=42,
            corner_radius=10,fg_color='#EEF0F7',hover_color='#E0E4EF',bg_color='white')
        eye.image=picture;eye.pack(side='right',padx=(6,0));eye._password_eye=True
    control.bind('<FocusIn>',lambda e:control.configure(border_color=BLUE))
    control.bind('<FocusOut>',lambda e:control.configure(border_color='#DCE2EE'))
    control.pack=field.pack;control.field=field
    return control


# def header: สร้างแถบโลโก้ ชื่อหน้า และปุ่มย้อนกลับตาม callback ที่รับมา
def header(parent,title,back=None):
    parent.configure(bg="#F3F5F9")
    bar=tk.Frame(parent,bg="white",padx=26,pady=12)
    bar.pack(fill="x")
    picture=logo((100,48))
    label=tk.Label(bar,image=picture,bg="white");label.image=picture;label.pack(side="left")
    tk.Label(bar,text=title,bg="white",fg="#14243B",font=("Noto Sans Thai",19,"bold")).pack(side="left",padx=24)
    if back:
        ctk.CTkButton(bar,text='‹ กลับ',command=back,fg_color='#EEF0F7',text_color=BLUE,hover_color='#E0E4EF',corner_radius=10,width=100,height=40,font=('Noto Sans Thai',14)).pack(side="right")


# def scroll_body: สร้าง Canvas กับ Scrollbar และ Frame ภายในสำหรับหน้าที่มีเนื้อหายาว
def scroll_body(parent):
    outer=tk.Frame(parent,bg="#F3F5F9")
    outer.pack(fill="both",expand=True)
    canvas=tk.Canvas(outer,bg="#F3F5F9",highlightthickness=0)
    bar=ctk.CTkScrollbar(outer,command=canvas.yview,width=12,fg_color='#F3F5FA',button_color='#C5CDDD',button_hover_color='#A6B2C9')
    bar.pack(side="right",fill="y");canvas.pack(side="left",fill="both",expand=True)
    inner=tk.Frame(canvas,bg="#F3F5F9")
    window=canvas.create_window((0,0),window=inner,anchor="nw")
    inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>",lambda e:canvas.itemconfigure(window,width=e.width))
    from ui.safe_scrollbar import connect_scrollbar
    connect_scrollbar(canvas,bar)
    from ui.mouse_scroll import enable_mouse_scroll
    enable_mouse_scroll(canvas,inner)
    return inner


# def polish: ปรับสี ฟอนต์ และปุ่มของวิดเจ็ตภายในให้ใช้รูปแบบเดียวกัน
def polish(parent):
    for child in parent.winfo_children():
        if getattr(child,"_input_underline",False) or getattr(child,"_password_eye",False): continue
        if isinstance(child,ctk.CTkBaseClass):continue
        kind=child.winfo_class()
        if kind in ("Frame","Labelframe"):
            child.configure(bg="white")
            if kind=="Labelframe":child.configure(fg="#14243B",font=("Noto Sans Thai",12,"bold"),relief="flat",highlightthickness=1,highlightbackground="#E1E5ED")
        elif kind=="Label":
            child.configure(bg="white",font=("Noto Sans Thai",11))
        elif kind=="Button":
            child.configure(bg=BLUE,fg="white",activebackground="#3337CB",activeforeground="white",cursor="hand2",bd=0)
        polish(child)
