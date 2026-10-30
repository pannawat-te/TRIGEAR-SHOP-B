from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: ฟอร์มลืมรหัสและฟอร์มบังคับตั้งรหัสใหม่หลังใช้รหัสชั่วคราว
import tkinter as tk
from tkinter import messagebox
from ui.customer_style import entry,header,polish,scroll_body
from database.password_reset import request_reset,change_required_password

# คลาส ForgotPasswordPage: เก็บข้อมูลและพฤติกรรมของ ฟอร์มลืมรหัสและฟอร์มบังคับตั้งรหัสใหม่หลังใช้รหัสชั่วคราว
class ForgotPasswordPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,back):
        import customtkinter as ctk
        self.frame=tk.Frame(root,bg="#F3F5F9");self.frame.pack(fill="both",expand=True)
        header(self.frame,"ลืมรหัสผ่าน",back)
        body=scroll_body(self.frame)
        body.grid_columnconfigure(0,weight=1)
        body.grid_columnconfigure(2,weight=1)
        body.grid_columnconfigure(1,minsize=600)
        def fit(event):
            body.grid_columnconfigure(1,minsize=max(320,min(600,event.width-48)))
        body.bind('<Configure>',fit,add='+')
        box=ctk.CTkFrame(body,fg_color="white",corner_radius=20,border_width=1,border_color="#E1E6F0")
        box.grid(row=0,column=1,sticky="ew",pady=28,padx=0)
        form=tk.Frame(box,bg="white",padx=32,pady=28)
        form.pack(fill="both",expand=True,padx=3,pady=3)
        ctk.CTkLabel(form,text="กู้คืนบัญชีของคุณ",font=("Noto Sans Thai",26,"bold"),text_color="#14253D").pack(pady=(0,6))
        ctk.CTkLabel(form,text="กรอกข้อมูลบัญชีเพื่อส่งคำขอให้ Admin ตรวจสอบ",font=("Noto Sans Thai",14),text_color="#64748B",wraplength=460).pack(pady=(0,24))
        self.fields=[]
        for title in ("Username","อีเมลที่สมัคร"):
            ctk.CTkLabel(form,text=title,font=("Noto Sans Thai",15),text_color="#14253D").pack(anchor="w")
            field=entry(form,width=38)
            field.pack(fill="x",pady=(4,16));self.fields.append(field)
        note=ctk.CTkFrame(form,fg_color="#F0F2FF",corner_radius=12)
        note.pack(fill="x",pady=(2,20))
        ctk.CTkLabel(note,text="ขั้นตอนการรีเซ็ตรหัสผ่าน",font=("Noto Sans Thai",15,"bold"),text_color="#4145F1",anchor="w").pack(fill="x",padx=16,pady=(12,4))
        help_text=ctk.CTkLabel(note,text="Admin จะตรวจสอบเจ้าของบัญชีและส่ง OTP ไปยังอีเมลที่สมัครไว้\nอาจใช้เวลาประมาณ 10 นาที–1 ชั่วโมง ในช่วงเวลาทำการ\nหากเป็นบัญชี Admin ต้องให้ Admin คนอื่นดำเนินการ",font=("Noto Sans Thai",14),text_color="#526078",justify="left",anchor="w",wraplength=450)
        help_text.pack(fill="x",padx=16,pady=(0,14))
        note.bind('<Configure>',lambda e:help_text.configure(wraplength=max(200,e.width-32)),add='+')
        self.button=ctk.CTkButton(form,text="ส่งคำขอรีเซ็ตรหัสผ่าน",command=self.submit,height=46,corner_radius=10,fg_color="#4145F1",hover_color="#3337CB",font=("Noto Sans Thai",16,"bold"))
        self.button.pack(fill="x",pady=(0,10))
        ctk.CTkButton(form,text="ได้รับ OTP แล้ว / ตั้งรหัสผ่านใหม่",command=lambda:self.open_otp(root,back),height=44,corner_radius=10,fg_color="white",text_color="#4145F1",border_width=1,border_color="#DCE2EE",hover_color="#F0F2FF",font=("Noto Sans Thai",15)).pack(fill="x")
        ctk.CTkButton(form,text="กลับไปเข้าสู่ระบบ",command=back,height=36,fg_color="transparent",text_color="#64748B",hover_color="#F3F5F9",font=("Noto Sans Thai",14)).pack(pady=(12,0))
        self.fields[0].bind('<Return>',lambda e:self.fields[1].focus_set())
        self.fields[1].bind('<Return>',lambda e:self.submit())
        self.fields[0].focus_set()
    def open_otp(self,root,back):
        values=[field.get().strip() for field in self.fields]
        self.frame.pack_forget()
        def restore():self.frame.pack(fill="both",expand=True)
        ResetOTPPage(root,back,restore,values)

    # def submit: ตรวจ Username/อีเมลแล้วส่งคำขอรีเซ็ต โดยไม่เปิดเผยว่ามีบัญชีตรงกันหรือไม่
    def submit(self):
        username,email=(field.get().strip() for field in self.fields)
        if not username or '@' not in email or '.' not in email:
            messagebox.showwarning("ข้อมูลไม่ครบ","กรุณากรอก Username และอีเมลให้ถูกต้อง");return
        try:request_reset(username,email)
        except Exception:
            messagebox.showerror("ส่งคำขอ","ส่งไม่สำเร็จ กรุณาลองใหม่");return
        self.button.configure(state="disabled")
        messagebox.showinfo("รับคำขอ","หากข้อมูลตรงกับบัญชี ระบบจะส่งคำขอให้ Admin ตรวจสอบ\nกรุณาติดต่อร้านผ่านช่องทางเดิมเพื่อยืนยันตัวตน")

# คลาส RequiredPasswordPage: เก็บข้อมูลและพฤติกรรมของ ฟอร์มลืมรหัสและฟอร์มบังคับตั้งรหัสใหม่หลังใช้รหัสชั่วคราว
class RequiredPasswordPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,user_id,temporary,back):
        self.user_id=user_id;self.temporary=temporary;self.back=back
        self.frame=tk.Frame(root);self.frame.pack(fill="both",expand=True)
        header(self.frame,"ตั้งรหัสผ่านใหม่",back)
        box=RoundedCard(self.frame,bg="white",padx=35,pady=25);box.pack(padx=70,pady=35,fill="x")
        tk.Label(box,text="ตั้งรหัสใหม่อย่างน้อย 8 ตัว มี A-Z และตัวเลข ใช้เฉพาะอังกฤษ/ตัวเลข").pack(pady=10)
        self.fields=[]
        for label in ("รหัสผ่านใหม่","ยืนยันรหัสผ่านใหม่"):
            tk.Label(box,text=label).pack(anchor="w")
            field=entry(box,show="*",password_chars_only=True);field.pack(fill="x",pady=8);self.fields.append(field)
        ActionButton(box,text="บันทึกรหัสใหม่",command=self.save).pack(pady=12);polish(box)
    # def save: ตรวจรหัสใหม่และการยืนยัน แล้วเปลี่ยนรหัสชั่วคราวเป็นรหัสใหม่ก่อนกลับ Login
    def save(self):
        password,confirm=(f.get() for f in self.fields)
        if password!=confirm:messagebox.showwarning("รหัสผ่าน","รหัสผ่านไม่ตรงกัน");return
        try:change_required_password(self.user_id,self.temporary,password)
        except ValueError as exc:messagebox.showwarning("รหัสผ่าน",str(exc));return
        except Exception:messagebox.showerror("รหัสผ่าน","บันทึกไม่สำเร็จ กรุณาลองใหม่");return
        self.temporary=None
        messagebox.showinfo("สำเร็จ","ตั้งรหัสใหม่แล้ว กรุณาเข้าสู่ระบบอีกครั้ง");self.back()


class ResetOTPPage:
    def __init__(self,root,back,restore,values=None):
        from database.email_otp import finish_reset
        page=tk.Frame(root);page.pack(fill='both',expand=True)
        def go_back():page.destroy();restore()
        header(page,'ตั้งรหัสผ่านด้วย OTP',go_back)
        body=scroll_body(page)
        box=RoundedCard(body,bg='white',padx=35,pady=20);box.pack(padx=30,pady=20)
        tk.Label(box,text='กรอก OTP ที่ Admin ส่งไปยังอีเมลเดิมของคุณ\nOTP มีอายุ 10 นาที และใช้ได้ครั้งเดียว').pack(pady=10)
        fields=[]
        for label in ('Username','อีเมลที่สมัคร','OTP 6 หลัก','รหัสผ่านใหม่','ยืนยันรหัสผ่านใหม่'):
            tk.Label(box,text=label).pack(anchor='w')
            secret='รหัสผ่าน' in label
            field=entry(box,width=40,show='*' if secret else '',password_chars_only=secret)
            field.pack(fill='x',pady=5);fields.append(field)
        if values:
            for field,value in zip(fields,values):field.insert(0,value)
        status=tk.Label(box,text='',wraplength=500);status.pack(pady=5)
        tk.Label(box,text='รหัสใหม่ ≥ 8 ตัว มี A-Z และตัวเลข ใช้เฉพาะอังกฤษ/ตัวเลข').pack(pady=8)
        def save():
            username,email,code,password,confirm=(f.get() for f in fields)
            if password!=confirm:status.configure(text='รหัสผ่านไม่ตรงกัน',fg='#DC2626');return
            try:finish_reset(username,email,code,password)
            except ValueError as exc:status.configure(text=str(exc),fg='#DC2626');return
            except Exception:status.configure(text='บันทึกไม่สำเร็จ กรุณาลองใหม่',fg='#DC2626');return
            page.destroy();back()
        ActionButton(box,text='ยืนยัน OTP และบันทึกรหัสใหม่',command=save).pack(fill='x',pady=10)
        ActionButton(box,text='ย้อนกลับ',command=go_back).pack(fill='x',pady=6)
        polish(box)
