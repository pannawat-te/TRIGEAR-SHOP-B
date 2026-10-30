# ไฟล์นี้: เลือกตารางไซซ์ตามประเภทหรือภาพเฉพาะสินค้า และเปิดดูพร้อมซูม/เลื่อน
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from PIL import Image,ImageOps,ImageTk
from ui.mouse_scroll import enable_mouse_scroll
ROOT=Path(__file__).resolve().parent.parent
SIZE_LABELS={'none':'ไม่มีไซซ์','shoe_cm':'รองเท้า — CM','clothing':'เสื้อผ้า / ชุด','road_bike':'จักรยานเสือหมอบ'}
DEFAULT_CHARTS={'shoe_cm':'SHOES.png','clothing':'suit.jpg','road_bike':'BIKE.png'}

# def chart_path: ใช้ภาพเฉพาะสินค้าเมื่อกำหนดไว้ มิฉะนั้นเลือกภาพตามประเภทไซซ์
def chart_path(kind,custom=None):
    if custom:
        path=Path(custom);return path if path.is_absolute() else ROOT/path
    name=DEFAULT_CHARTS.get(kind)
    return ROOT/'assets'/'size_charts'/name if name else None

# def show_size_chart: เปิดภาพต้นฉบับใน Popup พร้อมแถบซูม Scrollbar และล้อเมาส์
def show_size_chart(parent,kind,custom=None):
    path=chart_path(kind,custom)
    try:
        if path is None:raise ValueError('ไม่มีตารางไซซ์สำหรับสินค้านี้')
        with Image.open(path) as im:source=ImageOps.exif_transpose(im).convert('RGB')
    except (OSError,ValueError) as exc:
        messagebox.showwarning('ตารางไซซ์',f'เปิดตารางไซซ์ไม่ได้: {exc}');return
    win=tk.Toplevel(parent);win.title('ตารางไซซ์ — '+SIZE_LABELS.get(kind,'สินค้า'));win.transient(parent.winfo_toplevel())
    width=min(950,parent.winfo_screenwidth()-100);height=min(760,parent.winfo_screenheight()-120)
    win.geometry(f'{width}x{height}')
    tk.Label(win,text='ตารางอ้างอิง โปรดตรวจสอบไซซ์ของแบรนด์และรุ่นก่อนเลือก',wraplength=800).pack(pady=8)
    zoom=tk.DoubleVar(value=min(1,(width-40)/source.width,(height-160)/source.height))
    tools=tk.Frame(win);tools.pack(fill='x',padx=12)
    canvas=tk.Canvas(win,bg='white',highlightthickness=0)
    sy=ttk.Scrollbar(win,command=canvas.yview);sy.pack(side='right',fill='y')
    sx=ttk.Scrollbar(win,orient='horizontal',command=canvas.xview);sx.pack(side='bottom',fill='x')
    canvas.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);canvas.pack(fill='both',expand=True)
    enable_mouse_scroll(canvas,canvas)
    # def render: ย่อ/ขยายโดยคงสัดส่วนและกำหนดพื้นที่เลื่อนตามภาพจริง
    def render(value=None):
        scale=zoom.get();picture=source.resize((max(1,round(source.width*scale)),max(1,round(source.height*scale))),Image.Resampling.LANCZOS)
        canvas.picture=ImageTk.PhotoImage(picture);canvas.delete('all');canvas.create_image(0,0,anchor='nw',image=canvas.picture);canvas.configure(scrollregion=canvas.bbox('all'))
    tk.Label(tools,text='ซูม').pack(side='left')
    tk.Scale(tools,from_=0.2,to=3,resolution=0.05,variable=zoom,orient='horizontal',command=render,length=260).pack(side='left')
    tk.Button(tools,text='ขนาดจริง',command=lambda:(zoom.set(1),render())).pack(side='left',padx=10)
    tk.Button(tools,text='ปิด',command=win.destroy).pack(side='right')
    render()
