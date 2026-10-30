"""ภาพหลักขนาดใหญ่และ Slide 300ms เฉพาะตอนเปลี่ยนรูปสินค้า"""
import tkinter as tk
import time
from ui.image_utils import photo
from ui.shop_style import WHITE,BLUE,MUTED,button
from ui.product_gallery import thumbnail_slots,show_gallery

class ProductViewer(tk.Frame):
    def __init__(self,parent,paths):
        super().__init__(parent,bg=WHITE)
        self.paths=paths;self.index=0;self.size=400;self.job=None;self.current=None;self.next_photo=None
        self.canvas=tk.Canvas(self,bg=WHITE,height=400,highlightthickness=0);self.canvas.pack(fill='x')
        nav=tk.Frame(self,bg=WHITE);nav.pack(pady=10)
        button(nav,'‹',lambda:self.select((self.index-1)%len(paths)) if paths else None,'secondary',state='normal' if len(paths)>1 else 'disabled').pack(side='left')
        self.counter=tk.Label(nav,bg=WHITE,fg=MUTED);self.counter.pack(side='left',padx=15)
        button(nav,'›',lambda:self.select((self.index+1)%len(paths)) if paths else None,'secondary',state='normal' if len(paths)>1 else 'disabled').pack(side='left')
        thumbs=tk.Frame(self,bg=WHITE);thumbs.pack(pady=8)
        for i,extra in thumbnail_slots(paths):
            im=photo(paths[i],(64,64));cmd=(lambda:show_gallery(self._root(),paths,lambda n:self.select(n))) if extra else lambda n=i:self.select(n)
            b=tk.Button(thumbs,image=im,text=f'+{extra}' if extra else '',compound='center',command=cmd,bg=WHITE,fg=BLUE,bd=1,padx=0,pady=0);b.image=im;b.pack(side='left',padx=4)
        self.canvas.bind('<Configure>',self.resize);self.bind('<Destroy>',self.cleanup)
        self.select(0,animate=False)
    def cleanup(self,e):
        if e.widget==self and self.job:
            try:self.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
    def resize(self,e):
        size=max(240,min(640,e.width))
        if size!=self.size:
            self.size=size;self.canvas.configure(height=size);self.select(self.index,animate=False)
    def select(self,index,animate=True):
        if self.job:self.after_cancel(self.job);self.job=None
        if not self.winfo_exists():return
        old_index=self.index;self.index=index
        image=photo(self.paths[index] if self.paths else None,(self.size,self.size))
        self.counter.configure(text=f'{index+1 if self.paths else 0} / {len(self.paths)}')
        if not animate or self.current is None or old_index==index:
            self.canvas.delete('all');self.current=image;self.canvas.create_image(self.canvas.winfo_width()/2,0,image=image,anchor='n');return
        self.next_photo=image;self.canvas.delete('all');center=self.canvas.winfo_width()/2
        old=self.canvas.create_image(center,0,image=self.current,anchor='n');new=self.canvas.create_image(center+self.size,0,image=image,anchor='n')
        start=time.monotonic()
        def tick():
            elapsed=min(1,(time.monotonic()-start)/.3);ease=1-(1-elapsed)**3;offset=ease*self.size
            self.canvas.coords(old,center-offset,0);self.canvas.coords(new,center+self.size-offset,0)
            if elapsed<1:self.job=self.after(16,tick)
            else:
                self.current=self.next_photo;self.next_photo=None;self.canvas.delete(old);self.job=None
        tick()
