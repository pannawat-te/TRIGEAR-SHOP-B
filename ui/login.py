from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: หน้าล็อกอิน: ตรวจรหัส แยกหน้าลูกค้า/Admin และเปิดหน้าลืมรหัส
import tkinter as tk
from tkinter import messagebox

from database.database import get_connection, verify_password
from ui.register import RegisterPage
from ui.customer_home import CustomerHome
from ui.admin.dashboard import AdminDashboard


# คลาส LoginPage: เก็บข้อมูลและพฤติกรรมของ หน้าล็อกอิน
class LoginPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root, show_login):
        self.root = root
        self.show_login = show_login
        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        self.build()

    # def build: สร้างช่องกรอก ปุ่ม และพื้นที่แสดงข้อมูล พร้อมผูกปุ่มกับฟังก์ชันที่จะเรียก
    def build(self):
        from ui.brand import logo, BLUE
        self.frame.configure(bg="#F2F4F8")
        shell = RoundedCard(self.frame, bg="white",padx=18,pady=18)
        shell.place(relx=.5, rely=.5, anchor="center", relwidth=.86, relheight=.78)
        shell.grid_columnconfigure(0, weight=1, uniform="halves")
        shell.grid_columnconfigure(1, weight=1, uniform="halves")
        shell.grid_rowconfigure(0, weight=1)
        brand = tk.Canvas(shell, highlightthickness=0)
        brand.grid(row=0, column=0, sticky="nsew")
        self.brand_logo = logo((300, 170))
        # def paint: วาดพื้นไล่สีและโลโก้ใหม่เมื่อขนาด Canvas เปลี่ยน
        def paint(event):
            brand.delete("all")
            for y in range(0, event.height, 3):
                t = y / max(event.height, 1)
                rgb = tuple(int(a+(b-a)*t) for a,b in zip((229,230,255),(65,69,241)))
                brand.create_rectangle(0,y,event.width,y+3,fill="#%02x%02x%02x" % rgb,outline="")
            brand.create_image(event.width/2,event.height/2,image=self.brand_logo)
        brand.bind("<Configure>",paint)
        panel = tk.Frame(shell,bg="white")
        panel.grid(row=0,column=1,sticky="nsew")
        form = tk.Frame(panel,bg="white")
        form.place(relx=.5,rely=.5,anchor="center",relwidth=.73)
        tk.Label(form,text="LOG IN TO ENTER",bg="white",fg="#111827",font=("Noto Sans Thai",17,"bold")).pack(pady=(0,30))
        tk.Label(form,text="Username",bg="white",fg="#88909D",font=("Noto Sans Thai",10)).pack(anchor="w")
        from ui.customer_style import entry
        self.username=entry(form,width=25)
        self.username.pack(fill="x",ipady=6)
        self.username.field.pack_configure(pady=(4,20))
        tk.Label(form,text="Password",bg="white",fg="#88909D",font=("Noto Sans Thai",10)).pack(anchor="w")
        from ui.customer_style import entry
        self.password=entry(form,show="*")
        self.password.pack(fill="x")
        self.password.field.pack_configure(pady=(4,0))
        ActionButton(form,text="ฉันลืมรหัส",command=self.forgot_password,
                  bg="white",fg=BLUE,activebackground="white",activeforeground="#3337CB",
                  relief="flat",bd=0,highlightthickness=0,cursor="hand2",
                  font=("Noto Sans Thai",9),padx=0,pady=2).pack(anchor="e",pady=(5,14))
        for text,command in [("Log In",self.login),("Register",self.register)]:
            ActionButton(form,text=text,command=command,bg=BLUE,fg="white",activebackground="#3337CB",activeforeground="white",bd=0,cursor="hand2",font=("Noto Sans Thai",11,"bold")).pack(fill="x",pady=4)
        self.password.bind("<Return>",lambda event:self.login())
        self.username.bind("<Return>",lambda event:self.password.focus_set())
        self.username.focus_set()

    # def login: ตรวจ Username/รหัส; บังคับเปลี่ยนรหัสชั่วคราว หรือเปิดหน้าตามบทบาทบัญชี
    def login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอก Username และ Password")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password, role, must_change_password, temporary_password_expires, is_blocked FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user is None:
            answer = messagebox.askyesno(
                "ไม่พบผู้ใช้",
                "ไม่พบผู้ใช้ กรุณาลงทะเบียนที่ปุ่ม Sign Up ต้องการสมัครสมาชิกตอนนี้ไหม?"
            )
            if answer:
                self.register()
            return

        if not verify_password(password, user[2]):
            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "Password ไม่ถูกต้อง")
            return

        if user[6]:
            messagebox.showerror('บัญชีถูกระงับ','บัญชีนี้ถูกบล็อก กรุณาติดต่อร้านค้า TRIGEAR โทร 0956466576')
            return
        if user[4]:
            from datetime import datetime
            if not user[5] or datetime.fromisoformat(user[5])<=datetime.now():
                messagebox.showwarning("รหัสหมดอายุ","รหัสชั่วคราวหมดอายุ กรุณาส่งคำขอรีเซ็ตใหม่");return
            from ui.password_reset import RequiredPasswordPage
            self.frame.destroy()
            RequiredPasswordPage(self.root,user[0],password,self.show_login)
            return
        self.root._session_user_id=user[0]
        self.frame.destroy()
        if user[3] == "admin":
            AdminDashboard(self.root, self.show_login, user[0])
        else:
            CustomerHome(self.root, user[0], user[1], self.show_login)

    # def forgot_password: ปิดหน้า Login แล้วเปิดฟอร์มส่งคำขอรีเซ็ตรหัส
    def forgot_password(self):
        from ui.password_reset import ForgotPasswordPage
        self.frame.destroy()
        ForgotPasswordPage(self.root,self.show_login)

    # def register: ปิดหน้า Login แล้วเปิดหน้าสมัครสมาชิก
    def register(self):
        self.frame.destroy()
        RegisterPage(self.root, self.show_login)
