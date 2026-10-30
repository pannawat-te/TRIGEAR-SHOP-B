from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: รูปโปรไฟล์จากเครื่องหรือกล้อง พร้อมตัวอย่างก่อนบันทึก
import tkinter as tk
from tkinter import filedialog,messagebox
from pathlib import Path
from uuid import uuid4
from PIL import Image,ImageTk,ImageOps,ImageDraw

# def load_profile: เปิดและจัดภาพเป็นสี่เหลี่ยมสำหรับตัวอย่างและบันทึก
def load_profile(path,cropped=True):
    path=Path(path)
    if not path.is_absolute():path=Path(__file__).resolve().parent.parent/path
    with Image.open(path) as image:
        image=ImageOps.exif_transpose(image).convert('RGB')
        return ImageOps.fit(image,(512,512)) if cropped else image.copy()

# def save_profile: บันทึกภาพที่ยืนยันแล้วเป็นไฟล์ใหม่ โดยไม่ทับต้นฉบับ
def save_profile(image):
    folder=Path(__file__).resolve().parent.parent/'uploads'/'profiles';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(uuid4().hex+'.jpg');image.save(target,'JPEG',quality=90)
    return target.relative_to(Path(__file__).resolve().parent.parent).as_posix()

# คลาส ProfilePicker: เก็บรูปที่เลือกในหน่วยความจำจนผู้ใช้กดบันทึกบัญชี
class ProfilePicker(tk.Frame):
    # def __init__: สร้างตัวอย่างรูปและปุ่มเลือก ถ่าย และลบ
    def __init__(self,parent,path=None,preview_size=160,vertical=False):
        super().__init__(parent,bg='white');self.image=None;self.changed=False;self.path=path;self.preview_size=preview_size
        self.preview=tk.Label(self,bg='white');self.preview.pack(pady=8)
        buttons=tk.Frame(self,bg='white');buttons.pack()
        for text,command in [('เลือกรูปจากเครื่อง',self.choose),('ถ่ายรูปจากกล้อง',self.camera),('ลบรูป',self.remove)]:
            ActionButton(buttons,text=text,command=command,bg='#4145F1',fg='white').pack(side='top' if vertical else 'left',fill='x' if vertical else None,padx=4,pady=4)
        if path:
            try:self.image=load_profile(path)
            except Exception:pass
        self.render()
    # def render: แสดงภาพตัวอย่างหรือข้อความเมื่อไม่มีรูป
    def render(self):
        size=self.preview_size
        picture=Image.new('RGB',(size,size),'#EAF0F7')
        mask=Image.new('L',(size,size),0);ImageDraw.Draw(mask).ellipse((3,3,size-4,size-4),fill=255)
        if self.image:
            picture.paste(ImageOps.fit(self.image,(size,size),method=Image.Resampling.LANCZOS),(0,0),mask)
        else:
            draw=ImageDraw.Draw(picture)
            draw.ellipse((size*.34,size*.18,size*.66,size*.50),fill='#94A3B8')
            draw.ellipse((size*.18,size*.55,size*.82,size*.95),fill='#94A3B8')
        output=Image.new('RGB',(size,size),'white');output.paste(picture,(0,0),mask)
        ImageDraw.Draw(output).ellipse((2,2,size-3,size-3),outline='#14243B',width=3)
        self.photo=ImageTk.PhotoImage(output)
        self.preview.configure(image=self.photo,text='')
    # def choose: ตรวจไฟล์ภาพและเก็บภาพที่เลือกเป็นตัวอย่าง
    def choose(self):
        path=filedialog.askopenfilename(filetypes=[('รูปภาพ','*.jpg *.jpeg *.png *.webp')])
        if not path:return
        try:image=load_profile(path,cropped=False)
        except Exception:messagebox.showerror('รูปโปรไฟล์','เปิดภาพนี้ไม่ได้');return
        self.crop(image)
    # def crop: เปิดหน้าจัดรูปและเปลี่ยนภาพตัวอย่างเฉพาะเมื่อกดใช้รูปนี้
    def crop(self,image):
        from ui.profile_crop import ProfileCrop
        # def accept_crop: เก็บรูปที่ Crop แล้ว การเปลี่ยนรูปจริงรอปุ่มบันทึกบัญชี
        def accept_crop(result):
            self.image=result;self.changed=True;self.render()
        ProfileCrop(self,image,accept_crop)
    # def remove: ลบรูปในฟอร์ม การลบมีผลเมื่อบันทึกบัญชี
    def remove(self):self.image=None;self.changed=True;self.render()
    # def camera: เปิดหน้ากล้องให้ถ่าย ถ่ายใหม่ และยืนยัน โดยคืนอุปกรณ์เมื่อปิด
    def camera(self):
        try:import cv2
        except ImportError:messagebox.showinfo('กล้อง','ส่วนกล้องยังไม่พร้อม กรุณาเปิด INSTALL_CAMERA.bat เพื่อติดตั้งเพิ่มเติม หรือเลือกรูปจากเครื่องได้ตามปกติ');return
        if getattr(self,'camera_window',None) is not None and self.camera_window.winfo_exists():return
        cap=cv2.VideoCapture(0)
        if not cap.isOpened():cap.release();messagebox.showwarning('กล้อง','เปิดกล้องไม่ได้ ตรวจการเชื่อมต่อและสิทธิ์ใช้งานกล้อง');return
        win=tk.Toplevel(self);self.camera_window=win;win.title('ถ่ายรูปโปรไฟล์');win.transient(self.winfo_toplevel())
        preview=tk.Label(win);preview.pack(padx=12,pady=12)
        state={'latest':None,'captured':None,'job':None,'closed':False}
        # def close: ยกเลิกการอ่านภาพและคืนกล้องทุกครั้งที่ปิดหน้าต่าง
        def close():
            if state['closed']:return
            state['closed']=True
            if state['job']:
                try:win.after_cancel(state['job'])
                except tk.TclError:pass
            cap.release()
            if win.winfo_exists():win.destroy()
        # def tick: อ่านเฟรมกล้องด้วย after เพื่อไม่เรียก mainloop ซ้อน
        def tick():
            if state['closed']:return
            if state['captured'] is None:
                ok,frame=cap.read()
                if not ok:close();messagebox.showwarning('กล้อง','อ่านภาพจากกล้องไม่ได้');return
                state['latest']=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            image=state['captured'] or state['latest']
            show=image.copy();show.thumbnail((600,380));preview.photo=ImageTk.PhotoImage(show);preview.configure(image=preview.photo)
            state['job']=win.after(60,tick)
        # def capture: หยุดภาพล่าสุดไว้เพื่อให้ตรวจสอบก่อนเลือกใช้
        def capture():
            if state['latest']:state['captured']=state['latest'].copy();use.configure(state='normal')
        # def retake: กลับไปดูภาพสดและปิดปุ่มใช้รูปจนถ่ายใหม่
        def retake():state['captured']=None;use.configure(state='disabled')
        # def accept: ใช้ภาพที่ถ่ายเป็นตัวอย่างแล้วปิดกล้อง ยังไม่บันทึกบัญชี
        def accept():
            if state['captured'] is None:return
            image=state['captured'].copy();close();self.crop(image)
        controls=tk.Frame(win);controls.pack(pady=10)
        for text,command in [('ถ่ายรูป',capture),('ถ่ายใหม่',retake)]:ActionButton(controls,text=text,command=command).pack(side='left',padx=5)
        use=ActionButton(controls,text='ใช้รูปนี้',command=accept,state='disabled');use.pack(side='left',padx=5)
        win.protocol('WM_DELETE_WINDOW',close)
        win.bind('<Destroy>',lambda event:close() if event.widget==win else None)
        tick()
