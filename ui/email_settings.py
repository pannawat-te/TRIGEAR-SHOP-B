import tkinter as tk
from tkinter import messagebox
from database.database import get_connection
from services.email_sender import load_settings,save_settings

def show_email_settings(root,admin_id):
    conn=get_connection()
    try: admin=conn.execute('SELECT role,must_change_password FROM users WHERE id=?',(admin_id,)).fetchone()
    finally: conn.close()
    if admin != ('admin',0): return
    dialog=tk.Toplevel(root);dialog.title('ตั้งค่าอีเมล OTP');dialog.transient(root);dialog.grab_set()
    box=tk.Frame(dialog,padx=25,pady=20);box.pack(fill='both',expand=True)
    tk.Label(box,text='Gmail สำหรับส่ง OTP ของร้าน',font=('Noto Sans Thai',15,'bold')).pack(pady=10)
    tk.Label(box,text='SMTP: smtp.gmail.com • Port 587 • STARTTLS').pack(pady=5)
    tk.Label(box,text='Gmail ผู้ส่ง').pack(anchor='w')
    email=tk.Entry(box,width=45);email.pack(fill='x',pady=8)
    current=load_settings();email.insert(0,current.get('email',''))
    tk.Label(box,text='App Password (เว้นว่างเพื่อใช้รหัสเดิม)').pack(anchor='w')
    password=tk.Entry(box,show='*',width=45);password.pack(fill='x',pady=8)
    tk.Label(box,text='เก็บค่าบนเครื่องร้านนี้เท่านั้น\nห้ามแนบไฟล์ config/smtp.local.json เมื่อส่ง ZIP ให้ผู้อื่น',justify='left').pack(pady=12)
    def save():
        conn=get_connection()
        try: allowed=conn.execute('SELECT role,must_change_password FROM users WHERE id=?',(admin_id,)).fetchone()==('admin',0)
        finally: conn.close()
        if not allowed: messagebox.showerror('ตั้งค่า','สิทธิ์ Admin เปลี่ยนแล้ว');return
        if email.get().strip()!=current.get('email','') and not password.get().strip():
            messagebox.showwarning('ตั้งค่า','เมื่อเปลี่ยนอีเมล กรุณากรอก App Password ของบัญชีใหม่');return
        try: save_settings(email.get(),password.get() or current.get('password',''))
        except ValueError as exc: messagebox.showwarning('ตั้งค่า',str(exc));return
        messagebox.showinfo('ตั้งค่า','บันทึกแล้ว ระบบจะใช้ค่านี้เมื่อส่ง OTP');dialog.destroy()
    tk.Button(box,text='บันทึกการตั้งค่า',command=save).pack(pady=10)
