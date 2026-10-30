from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: หน้าสมัครสมาชิก: ตรวจ Username อีเมล เบอร์โทร และรหัสก่อนสร้างบัญชี
from ui.customer_style import entry as customer_entry, header, scroll_body, polish
import tkinter as tk
from tkinter import messagebox
import re

from database.database import get_connection, hash_password
from database.password_policy import valid_password,PASSWORD_HINT


# คลาส RegisterPage: เก็บข้อมูลและพฤติกรรมของ หน้าสมัครสมาชิก
class RegisterPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root, show_login):
        self.root = root
        self.show_login = show_login
        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        self.build()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        header(self.frame,"สมัครสมาชิก",self.show_login)
        box = RoundedCard(self.frame,bg="white",padx=35,pady=18)
        box.pack(anchor="center",pady=12)

        tk.Label(box, text="CREATE ACCOUNT", font=("Noto Sans Thai", 24, "bold")).pack(pady=15)

        fields = [("Username", False), ("Email", False), ("เบอร์โทรติดต่อ", False), ("Password", True), ("Confirm Password", True)]
        self.entries = {}

        for label, secret in fields:
            tk.Label(box, text=label).pack(anchor="w")
            e = customer_entry(box, width=38, show="*" if secret else "",password_chars_only=secret)
            e.pack(fill="x",pady=(2,8))
            self.entries[label] = e

        tk.Label(
            box,
            text="Username ≥ 6 ตัว | Password ≥ 8 ตัว + A-Z + ตัวเลข (เฉพาะอังกฤษ/ตัวเลข)",
            fg="gray"
        ).pack(pady=6)

        self.submit_button = ActionButton(box, text="ส่ง OTP เพื่อสมัครสมาชิก", width=25, command=self.register)
        self.submit_button.pack(pady=10)
        ActionButton(box, text="BACK TO LOGIN", width=25, command=self.show_login).pack()
        polish(box)

    # def register: ตรวจข้อมูลสมัครและข้อมูลซ้ำ แล้วสร้างบัญชีลูกค้าพร้อมแฮชรหัส
    def register(self):
        username = self.entries["Username"].get().strip()
        email = self.entries["Email"].get().strip()
        phone = re.sub(r"[\s-]", "", self.entries["เบอร์โทรติดต่อ"].get().strip())
        password = self.entries["Password"].get()
        confirm = self.entries["Confirm Password"].get()

        if len(username) < 6:
            messagebox.showwarning("แจ้งเตือน", "Username ต้องมีอย่างน้อย 6 ตัวอักษร")
            return
        if "@" not in email or "." not in email:
            messagebox.showwarning("แจ้งเตือน", "รูปแบบ Email ไม่ถูกต้อง")
            return
        if not re.fullmatch(r"0[0-9]{8,9}", phone):
            messagebox.showwarning("เบอร์โทรติดต่อ", "กรุณากรอกเบอร์โทรศัพท์ไทย 9–10 หลัก เริ่มด้วย 0")
            return
        if not valid_password(password):
            messagebox.showwarning("แจ้งเตือน", PASSWORD_HINT)
            return
        if password != confirm:
            messagebox.showerror("แจ้งเตือน", "Password และ Confirm Password ไม่ตรงกัน")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if cur.fetchone():
            conn.close()
            messagebox.showerror("สมัครสมาชิกไม่สำเร็จ", "Username นี้ถูกใช้งานแล้ว")
            return
        cur.execute("SELECT 1 FROM users WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            messagebox.showerror("สมัครสมาชิกไม่สำเร็จ", "Email นี้ถูกใช้งานแล้ว")
            return

        conn.close()
        from database.email_otp import start_registration
        from ui.async_task import run_task
        # Capture an immutable registration snapshot; never store plaintext passwords.
        self.pending_registration=(username,email,hash_password(password),phone)
        run_task(self.frame,[self.submit_button],
                 lambda:start_registration(*self.pending_registration),
                 lambda token:self.verify_dialog(token,email),
                 lambda exc:messagebox.showerror("ส่ง OTP",str(exc) if isinstance(exc,ValueError) else "ส่งไม่สำเร็จ กรุณาลองใหม่"))

    def verify_dialog(self,token,email):
        from database.email_otp import finish_registration,start_registration
        from ui.async_task import run_task
        self.frame.pack_forget()
        page=tk.Frame(self.root,bg="#F3F5F9");page.pack(fill="both",expand=True)
        def back():
            page.destroy();self.frame.pack(fill="both",expand=True)
        header(page,"ยืนยันอีเมลด้วย OTP",back)
        body=scroll_body(page)
        box=RoundedCard(body,bg="white",padx=35,pady=25);box.pack(padx=30,pady=30)
        tk.Label(box,text="กรอกรหัส OTP",font=("Noto Sans Thai",24,"bold"),bg="white").pack(pady=15)
        tk.Label(box,text=f"ส่งรหัสไปที่ {email} แล้ว\nOTP มีอายุ 10 นาที และใช้ได้ครั้งเดียว",bg="white",wraplength=500).pack(pady=10)
        tk.Label(box,text="OTP 6 หลัก",bg="white").pack(anchor="w")
        import customtkinter as ctk
        code=ctk.CTkEntry(box,width=300,height=58,corner_radius=12,font=("Noto Sans Thai",26),justify="center",
                      validate="key",validatecommand=(page.register(lambda value:len(value)<=6 and (not value or (value.isascii() and value.isdigit()))),'%P'))
        code.pack(fill="x",pady=12);code.focus_set()
        status=tk.Label(box,text="กรอกผิดได้ไม่เกิน 5 ครั้ง",bg="white",wraplength=500);status.pack(pady=10)
        state={'token':token}
        def verify():
            if len(code.get())!=6:status.configure(text="กรุณากรอก OTP ให้ครบ 6 หลัก",fg="#DC2626");return
            try:finish_registration(state['token'],code.get())
            except ValueError as exc:status.configure(text=str(exc),fg="#DC2626");return
            except Exception:status.configure(text="บันทึกไม่สำเร็จ กรุณาลองใหม่",fg="#DC2626");return
            page.destroy();self.show_login()
        verify_button=ActionButton(box,text="ยืนยัน OTP และสมัครสมาชิก",command=verify);verify_button.pack(fill="x",pady=10)
        def resend():
            status.configure(text="กำลังส่ง OTP…",fg="#4145F1")
            def done(new_token):
                state['token']=new_token;code.delete(0,'end');status.configure(text="ส่ง OTP ใหม่แล้ว กรุณาใช้รหัสล่าสุด",fg="#15803D")
            run_task(page,[verify_button,resend_button],lambda:start_registration(*self.pending_registration),done,
                     lambda exc:status.configure(text=str(exc) if isinstance(exc,ValueError) else "ส่งไม่สำเร็จ กรุณาลองใหม่",fg="#DC2626"))
        resend_button=ActionButton(box,text="ส่ง OTP อีกครั้ง (เว้นอย่างน้อย 60 วินาที)",command=resend);resend_button.pack(fill="x",pady=6)
        ActionButton(box,text="กลับไปแก้ข้อมูลสมัคร",command=back).pack(fill="x",pady=6)
        polish(box)
