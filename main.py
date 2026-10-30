# ไฟล์นี้: จุดเริ่มโปรแกรม: ตั้งค่าหน้าต่าง โหลดฐานข้อมูล และเปิดหน้าเข้าสู่ระบบ
import tkinter as tk
from tkinter import ttk

from database.database import initialize_database
try:
    import customtkinter
except ImportError:
    raise SystemExit('Please run: py -m pip install customtkinter Pillow')

from ui.app_fonts import register_fonts
register_fonts()

from ui.login import LoginPage
from ui.theme import apply_theme


# คลาส App: เก็บข้อมูลและพฤติกรรมของ จุดเริ่มโปรแกรม
class App:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self, root):
        self.root = root
        self.root._logout_callback=self.show_login
        self.root.title("TRI GEAR | Sports Equipment")
        self.root.configure(bg="#f3f7fb")
        self.root.geometry("1100x720")
        self.root.minsize(1000, 650)
        apply_theme(self.root)
        self.fullscreen = False
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.show_login()
        self.root.after(1000,self.check_session)
        self.root.after_idle(self.enter_fullscreen)

    # def enter_fullscreen: ขยายโปรแกรมเต็มจอโดยซ่อนแถบชื่อหน้าต่างและ Taskbar
    def enter_fullscreen(self):
        self.root.attributes('-fullscreen', True)
        self.fullscreen = True

    # def exit_fullscreen: Esc ออกเป็นหน้าต่างขยายเต็มจอ ไม่ปิดโปรแกรม
    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.root.attributes('-fullscreen', False)
            self.fullscreen = False
            try:
                self.root.state('zoomed')
            except tk.TclError:
                try:
                    self.root.attributes('-zoomed', True)
                except tk.TclError:
                    self.root.geometry(f'{self.root.winfo_screenwidth()}x{max(650,self.root.winfo_screenheight()-80)}+0+0')
        return 'break'

    # def toggle_fullscreen: F11 สลับ Full Screen กับหน้าต่างขยายเต็มจอ
    def toggle_fullscreen(self, event=None):
        if self.fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()
        return 'break'

    def check_session(self):
        uid=getattr(self.root,'_session_user_id',None)
        if uid is not None:
            from database.database import get_connection
            conn=get_connection()
            try:row=conn.execute('SELECT is_blocked FROM users WHERE id=?',(uid,)).fetchone()
            finally:conn.close()
            if not row or row[0]:
                from tkinter import messagebox
                self.show_login()
                messagebox.showwarning('บัญชีถูกระงับ','บัญชีถูกระงับการใช้งาน กรุณาติดต่อร้านค้า',parent=self.root)
        self.root.after(1000,self.check_session)

    # def clear: ทำลายวิดเจ็ตทั้งหมดก่อนเปลี่ยนหน้าหลักของโปรแกรม
    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # def show_login: ล้างหน้าปัจจุบันแล้วสร้างหน้า Login ใหม่
    def show_login(self):
        self.root._session_user_id=None
        self.clear()
        LoginPage(self.root, self.show_login)

    # def run: เริ่ม mainloop เพื่อรับเหตุการณ์ปุ่มและวาดหน้าต่างต่อเนื่อง
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    initialize_database()
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    style=ttk.Style()
    style.configure("Treeview",rowheight=30,font=("Segoe UI",10))
    style.configure("Treeview.Heading",font=("Segoe UI",10,"bold"))
    App(root).run()
