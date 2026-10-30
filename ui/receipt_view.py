from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: ปุ่มเปิด บันทึก และพิมพ์ PDF สำหรับลูกค้าและ Admin
import os
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import messagebox,filedialog
from services.receipt import receipt_pdf

# def open_file: เปิด PDF ด้วยโปรแกรมอ่านเอกสารของระบบปฏิบัติการ
def open_file(path):
    if sys.platform=='win32':os.startfile(str(path))
    elif sys.platform=='darwin':subprocess.Popen(['open',str(path)])
    else:subprocess.Popen(['xdg-open',str(path)])

# def show_receipt: ตรวจสิทธิ์ สร้าง PDF แล้วแสดงเครื่องมืออ่าน/บันทึก/พิมพ์
# ปุ่มพิมพ์มีเฉพาะ Admin และทำงานเมื่อผู้ใช้กดเอง
def show_receipt(root,order_id,user_id=None,admin=False):
    try:path,status=receipt_pdf(order_id,user_id,admin)
    except Exception as exc:
        messagebox.showwarning('ใบเสร็จ',str(exc));return
    win=tk.Toplevel(root);win.title(f'ใบเสร็จ · Order #{order_id}');win.transient(root)
    tk.Label(win,text=path.stem,font=('Noto Sans Thai',15,'bold')).pack(padx=24,pady=15)
    tk.Label(win,text=f'สถานะคำสั่งซื้อปัจจุบัน: {status}',wraplength=450).pack(padx=20,pady=5)
    if status.startswith('สถานะถูกยกเลิก') or status=='คืนเงินสำเร็จ':
        tk.Label(win,text='คำสั่งซื้อนี้ถูกยกเลิก / คืนเงิน\nใบเสร็จเดิมเก็บไว้เป็นประวัติ โปรดดูหลักฐานคืนเงินประกอบ',fg='#b45309',wraplength=450).pack(pady=10)
    # def view: เปิด PDF โดยรายงานกรณีไม่มีโปรแกรมอ่าน
    def view():
        try:open_file(path)
        except OSError as exc:messagebox.showwarning('เปิดใบเสร็จ',str(exc))
    # def save: คัดลอก PDF ไปยังตำแหน่งที่ลูกค้าเลือก ไม่เปลี่ยนต้นฉบับ
    def save():
        dest=filedialog.asksaveasfilename(parent=win,defaultextension='.pdf',initialfile=path.name,filetypes=[('PDF','*.pdf')])
        if not dest:return
        try:
            if os.path.abspath(dest)!=str(path.resolve()):shutil.copy2(path,dest)
            messagebox.showinfo('ใบเสร็จ','บันทึก PDF แล้ว')
        except OSError as exc:messagebox.showwarning('บันทึกใบเสร็จ',str(exc))
    # def print_pdf: ใช้คำสั่งพิมพ์ Windows หรือเปิด PDF เพื่อเลือกพิมพ์บนระบบอื่น
    def print_pdf():
        try:
            if sys.platform=='win32':os.startfile(str(path),'print')
            else:view()
        except OSError:messagebox.showinfo('พิมพ์ใบเสร็จ','เปิด PDF แล้วกด Ctrl+P เพื่อเลือกเครื่องพิมพ์')
    ActionButton(win,text='เปิดดูใบเสร็จ PDF',command=view).pack(fill='x',padx=24,pady=5)
    ActionButton(win,text='บันทึกใบเสร็จ PDF',command=save).pack(fill='x',padx=24,pady=5)
    if admin:ActionButton(win,text='พิมพ์ใบเสร็จ',command=print_pdf).pack(fill='x',padx=24,pady=5)
    ActionButton(win,text='ปิด',command=win.destroy).pack(pady=12)
