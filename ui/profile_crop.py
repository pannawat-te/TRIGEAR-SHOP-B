from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: Crop รูปโปรไฟล์แบบจัตุรัส ลากภาพและซูมก่อนยืนยัน
import tkinter as tk
from PIL import Image,ImageTk,ImageOps

# def clamp_position: จำกัดตำแหน่งภาพไม่ให้มีช่องว่างในกรอบ Crop
def clamp_position(x,y,width,height,side):
    return min(0,max(side-width,x)),min(0,max(side-height,y))

# def crop_square: แปลงกรอบบนหน้าจอกลับไปตำแหน่งต้นฉบับ แล้วสร้างรูป 512x512
def crop_square(image,x,y,scale,side):
    left=max(0,-x/scale);top=max(0,-y/scale);length=side/scale
    return image.crop((left,top,min(image.width,left+length),min(image.height,top+length))).resize((512,512),Image.Resampling.LANCZOS)

# คลาส ProfileCrop: เก็บภาพต้นฉบับ ตำแหน่ง และระดับซูมจนผู้ใช้เลือกใช้รูป
class ProfileCrop(tk.Toplevel):
    # def __init__: สร้างกรอบ Crop ปุ่มซูม และภาพตัวอย่างผลลัพธ์
    def __init__(self,parent,image,on_accept):
        super().__init__(parent);self.title('จัดรูปโปรไฟล์');self.transient(parent.winfo_toplevel())
        self.image=ImageOps.exif_transpose(image).convert('RGB');self.on_accept=on_accept
        self.side=min(340,max(200,self.winfo_screenwidth()-100),max(200,self.winfo_screenheight()-300))
        self.base=max(self.side/self.image.width,self.side/self.image.height)
        self.zoom=tk.DoubleVar(value=1.0);self.scale=self.base
        self.x=(self.side-self.image.width*self.scale)/2;self.y=(self.side-self.image.height*self.scale)/2
        tk.Label(self,text='ลากรูปเพื่อจัดตำแหน่ง และเลื่อนแถบเพื่อซูม',font=('Noto Sans Thai',11)).pack(pady=10)
        self.canvas=tk.Canvas(self,width=self.side,height=self.side,bg='#e5e7eb',highlightthickness=1,highlightbackground='#4145F1')
        self.canvas.pack(padx=18);self.canvas.bind('<ButtonPress-1>',self.start_drag);self.canvas.bind('<B1-Motion>',self.drag)
        tk.Scale(self,from_=1,to=4,resolution=0.01,orient='horizontal',variable=self.zoom,label='ซูม',command=self.set_zoom,length=self.side).pack()
        self.preview=tk.Label(self);self.preview.pack(pady=5)
        controls=tk.Frame(self);controls.pack(pady=12)
        ActionButton(controls,text='เริ่มใหม่',command=self.reset).pack(side='left',padx=5)
        ActionButton(controls,text='ใช้รูปนี้',command=self.accept).pack(side='left',padx=5)
        ActionButton(controls,text='ยกเลิก',command=self.destroy).pack(side='left',padx=5)
        self.render();self.grab_set()
    # def render: วาดภาพ Crop และตัวอย่างโดยคงสัดส่วนและไม่ให้เห็นช่องว่าง
    def render(self):
        width=max(self.side,round(self.image.width*self.scale));height=max(self.side,round(self.image.height*self.scale))
        self.x,self.y=clamp_position(self.x,self.y,width,height,self.side)
        # วาดเฉพาะพื้นที่ Crop เพื่อไม่สร้างภาพซูมขนาดใหญ่ในหน่วยความจำ
        result=crop_square(self.image,self.x,self.y,self.scale,self.side)
        self.picture=ImageTk.PhotoImage(result.resize((self.side,self.side),Image.Resampling.LANCZOS))
        self.canvas.delete('all');self.canvas.create_image(0,0,anchor='nw',image=self.picture)
        self.small=ImageTk.PhotoImage(result.resize((100,100),Image.Resampling.LANCZOS));self.preview.configure(image=self.small)
    # def start_drag: เก็บตำแหน่งเมาส์ก่อนลาก
    def start_drag(self,event):self.last=(event.x,event.y)
    # def drag: เลื่อนภาพตามระยะลากแล้วตรวจขอบกรอบ
    def drag(self,event):
        self.x+=event.x-self.last[0];self.y+=event.y-self.last[1];self.last=(event.x,event.y);self.render()
    # def set_zoom: ซูมรอบจุดกึ่งกลางกรอบเพื่อไม่ให้ตำแหน่งใบหน้ากระโดด
    def set_zoom(self,value):
        new=self.base*float(value)
        cx=(self.side/2-self.x)/self.scale;cy=(self.side/2-self.y)/self.scale
        self.scale=new;self.x=self.side/2-cx*new;self.y=self.side/2-cy*new;self.render()
    # def reset: คืนระดับซูมและวางภาพไว้กลางกรอบ
    def reset(self):
        self.scale=self.base;self.x=(self.side-self.image.width*self.scale)/2;self.y=(self.side-self.image.height*self.scale)/2
        self.zoom.set(1);self.render()
    # def accept: ส่งเฉพาะภาพที่ Crop แล้วกลับไปแสดงในบัญชี ยังไม่เขียนฐานข้อมูล
    def accept(self):
        result=crop_square(self.image,self.x,self.y,self.scale,self.side)
        self.destroy();self.on_accept(result)
