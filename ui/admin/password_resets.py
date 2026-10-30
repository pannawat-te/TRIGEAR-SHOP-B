from ui.modern_widgets import ActionButton,RoundedCard
# ไฟล์นี้: รายการคำขอรีเซ็ต: ตรวจสมาชิก อนุมัติ/ปฏิเสธ และแสดงรหัสชั่วคราว
import tkinter as tk
from tkinter import ttk,messagebox
from database.database import get_connection
from database.password_reset import process_reset
from ui.customer_style import header

# คลาส AdminPasswordResetsPage: เก็บข้อมูลและพฤติกรรมของ รายการคำขอรีเซ็ต
class AdminPasswordResetsPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,admin_id,back):
        self.root=root;self.admin_id=admin_id;self.back=back
        self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True)
        header(self.frame,'คำขอรีเซ็ตรหัสผ่าน',self.go_back)
        tk.Label(self.frame,text='ตรวจสอบเจ้าของบัญชีก่อนอนุมัติส่ง OTP ทางอีเมล • OTP มีอายุ 10 นาที').pack(pady=12)
        self.tree=ttk.Treeview(self.frame,columns=('username','email','phone','role','status','date'),show='headings',selectmode='browse')
        for col,title in zip(self.tree['columns'],('Username','อีเมล','เบอร์โทรติดต่อ','บทบาท','สถานะ','วันที่แจ้ง')):
            self.tree.heading(col,text=title);self.tree.column(col,width=135)
        bar=ttk.Scrollbar(self.frame,command=self.tree.yview);bar.pack(side='right',fill='y');self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(fill='both',expand=True,padx=20)
        self.verified=tk.BooleanVar()
        tk.Checkbutton(self.frame,text='ฉันได้ยืนยันว่าเป็นเจ้าของบัญชีแล้ว',variable=self.verified).pack(pady=8)
        buttons=tk.Frame(self.frame);buttons.pack(pady=15)
        for title,action in [('ดูข้อมูลสมาชิก',self.member_detail),('อนุมัติและส่ง OTP / ส่งซ้ำ',self.reset),('ปฏิเสธคำขอ',self.reject),('รีเฟรช',self.refresh)]:
            ActionButton(buttons,text=title,command=action).pack(side='left',padx=8)
        self.tree.bind("<<TreeviewSelect>>",lambda event:self.verified.set(False))
        self.refresh()
    # def refresh: โหลดและวาดรายการใหม่ เพื่อให้หน้าจอตรงกับข้อมูลล่าสุด
    def refresh(self):
        self.tree.delete(*self.tree.get_children());self.verified.set(False)
        conn=get_connection()
        try:rows=conn.execute("SELECT r.id,u.username,u.email,COALESCE(u.contact_phone,''),u.role,r.status,r.created_at FROM password_reset_requests r JOIN users u ON u.id=r.user_id ORDER BY r.status='pending' DESC,r.id DESC").fetchall()
        finally:conn.close()
        for row in rows:
            labels={'pending':'รอดำเนินการ','completed':'ดำเนินการแล้ว','rejected':'ปฏิเสธแล้ว','otp_sent':'ส่ง OTP แล้ว','expired':'OTP หมดอายุ'}
            self.tree.insert('', 'end',iid=str(row[0]),values=(*row[1:5],labels.get(row[5],row[5]),row[6]))
    # def act: ตรวจคำขอที่เลือกและการยืนยันเจ้าของ แล้วอนุมัติ/ปฏิเสธ; แสดงรหัสชั่วคราวเมื่ออนุมัติ
    def act(self,reject=False):
        selected=self.tree.selection()
        if not selected:messagebox.showwarning('เลือกคำขอ','กรุณาเลือกคำขอ');return
        if not reject and not self.verified.get():messagebox.showwarning('ยืนยันเจ้าของบัญชี','กรุณาตรวจสอบเจ้าของบัญชีก่อนรีเซ็ต');return
        if not messagebox.askyesno('ยืนยัน','ปฏิเสธคำขอนี้?' if reject else 'อนุมัติและส่ง OTP ไปยังอีเมลเดิมของบัญชีที่เลือก?'):return
        from ui.async_task import run_task
        request_id=int(selected[0])
        def done(result):
            self.refresh()
            messagebox.showinfo('คำขอ','ปฏิเสธคำขอแล้ว' if reject else 'ส่ง OTP ไปยังอีเมลที่สมัครไว้แล้ว\nลูกค้ากด “ได้รับ OTP แล้ว” ในหน้าลืมรหัสเพื่อตั้งรหัสใหม่')
        buttons=[w for w in self.frame.winfo_children() if isinstance(w,tk.Frame)]
        action_buttons=[w for f in buttons for w in f.winfo_children() if isinstance(w,tk.Button)]
        run_task(self.frame,action_buttons,lambda:process_reset(request_id,self.admin_id,reject),done,
                 lambda exc:messagebox.showerror('คำขอ',str(exc) if isinstance(exc,ValueError) else 'ดำเนินการไม่สำเร็จ กรุณาลองใหม่'))
    # def member_detail: หารหัสเจ้าของคำขอที่เลือก แล้วเปิดข้อมูลสมาชิกให้ Admin ตรวจสอบ
    def member_detail(self):
        selected=self.tree.selection()
        if not selected:messagebox.showwarning('คำขอ','กรุณาเลือกคำขอ');return
        conn=get_connection()
        try:row=conn.execute('SELECT user_id FROM password_reset_requests WHERE id=?',(int(selected[0]),)).fetchone()
        finally:conn.close()
        if row:
            from ui.admin.members import show_member_detail
            show_member_detail(self.root,self.admin_id,row[0])
    # def reset: เรียกขั้นตอนอนุมัติรีเซ็ตรหัสสำหรับคำขอที่เลือก
    def reset(self):self.act()
    # def reject: เรียกขั้นตอนปฏิเสธคำขอที่เลือก โดยไม่เปลี่ยนรหัส
    def reject(self):self.act(True)
    # def go_back: ปิดหน้าปัจจุบัน แล้วเรียกหน้าที่ส่ง callback เข้ามา
    def go_back(self):self.frame.destroy();self.back()
