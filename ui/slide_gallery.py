"""300ms horizontal product-image transition, independent from page navigation."""
import tkinter as tk
from pathlib import Path
from collections import OrderedDict
import time
from PIL import Image,ImageTk,ImageOps,ImageDraw,ImageChops
import customtkinter as ctk
from ui.image_utils import ROOT
from ui.storefront_style import WHITE,BLUE,BORDER,MUTED,button,label
from ui.product_gallery import thumbnail_slots,show_gallery


def contained_image(path,size,background=WHITE,trim=False):
    size=(max(1,int(size[0])),max(1,int(size[1])))
    result=Image.new('RGB',size,background)
    source=Path(path) if path else None
    if source is not None and not source.is_absolute():source=ROOT/source
    try:
        with Image.open(source) as image:
            image=ImageOps.exif_transpose(image).convert('RGBA')
            if trim:
                flat=Image.new('RGB',image.size,WHITE);flat.paste(image,(0,0),image)
                corners=[flat.getpixel(p) for p in ((0,0),(flat.width-1,0),(0,flat.height-1),(flat.width-1,flat.height-1))]
                if all(min(pixel)>248 for pixel in corners):
                    mask=ImageChops.difference(flat,Image.new('RGB',flat.size,WHITE)).convert('L').point(lambda value:255 if value>8 else 0)
                    box=mask.getbbox()
                    if box and box[2]-box[0]>=8 and box[3]-box[1]>=8:image=image.crop(box)
            image.thumbnail((max(1,size[0]-16),max(1,size[1]-16)),Image.Resampling.LANCZOS)
            result.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2),image)
    except (OSError,ValueError,TypeError):
        draw=ImageDraw.Draw(result);x,y=size[0]//2,size[1]//2
        draw.rounded_rectangle((x-30,y-25,x+30,y+20),radius=8,outline='#B2BFD1',width=2)
        draw.text((x-25,y+30),'NO IMAGE',fill=MUTED)
    return result


class SlideGallery(ctk.CTkFrame):
    DURATION=.3
    def __init__(self,parent,paths):
        super().__init__(parent,fg_color=WHITE,corner_radius=12)
        self.paths=list(paths);self.index=0;self.job=None;self.resize_job=None;self.image_cache=OrderedDict();self.size=(400,400)
        self.current=None;self.incoming=None;self.target_photo=None;self.thumb_buttons=[]
        self.canvas=tk.Canvas(self,bg=WHITE,height=400,highlightthickness=0,bd=0);self.canvas.pack(fill='x')
        controls=ctk.CTkFrame(self,fg_color='transparent');controls.pack(pady=8)
        state='normal' if len(paths)>1 else 'disabled'
        button(controls,'‹',lambda:self.select(self.index-1,direction=-1),'secondary',width=42,state=state).pack(side='left')
        self.counter=label(controls,'',13,color=MUTED,width=100);self.counter.pack(side='left')
        button(controls,'›',lambda:self.select(self.index+1,direction=1),'secondary',width=42,state=state).pack(side='left')
        thumbs=ctk.CTkFrame(self,fg_color='transparent');thumbs.pack(pady=(4,12))
        for index,extra in thumbnail_slots(self.paths):
            image=ctk.CTkImage(light_image=contained_image(self.paths[index],(68,68)),size=(68,68))
            command=(lambda:show_gallery(self._root(),self.paths,self.select)) if extra else lambda n=index:self.select(n)
            b=ctk.CTkButton(thumbs,text=f'+{extra}' if extra else '',image=image,compound='top',command=command,
                fg_color=WHITE,text_color=BLUE,hover_color='#F3F2FF',border_width=1,border_color=BORDER,
                corner_radius=10,width=78,height=78,font=('Noto Sans Thai',12,'bold'))
            b.pack(side='left',padx=4);self.thumb_buttons.append((index,b))
        self.canvas.bind('<Configure>',self._resize);self.bind('<Destroy>',self._destroy,add='+')
        self.select(0,animate=False)
    def _destroy(self,event):
        if event.widget!=self:return
        for job in (self.job,self.resize_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        self.job=None;self.resize_job=None;self.image_cache.clear()
    def _resize(self,event):
        wanted=(max(220,min(760,event.width)),max(240,min(560,event.width)))
        if wanted==self.size:return
        self.size=wanted
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(60,self._render_resize)
    def _render_resize(self):
        self.resize_job=None
        if self.winfo_exists():self.canvas.configure(height=self.size[1]);self.select(self.index,animate=False)
    def _photo(self,index):
        path=self.paths[index] if self.paths else None;key=(path,self.size)
        if key not in self.image_cache:self.image_cache[key]=ImageTk.PhotoImage(contained_image(path,self.size))
        self.image_cache.move_to_end(key)
        while len(self.image_cache)>6:self.image_cache.popitem(last=False)
        return self.image_cache[key]
    def select(self,index,animate=True,direction=None):
        if not self.winfo_exists():return
        if self.job:self.after_cancel(self.job);self.job=None
        if self.target_photo is not None:self.current=self.target_photo;self.target_photo=None
        old=self.index;index=index%len(self.paths) if self.paths else 0;self.index=index
        picture=self._photo(index);self.counter.configure(text=f'{index+1 if self.paths else 0} / {len(self.paths)}')
        for n,b in self.thumb_buttons:b.configure(border_color=BLUE if n==index else BORDER,border_width=2 if n==index else 1)
        width=max(1,self.canvas.winfo_width());center=width/2;self.canvas.delete('all')
        if not animate or self.current is None or index==old:
            self.current=picture;self.canvas.create_image(center,0,image=picture,anchor='n');return
        sign=direction if direction else (1 if index>old else -1)
        self.target_photo=picture;old_item=self.canvas.create_image(center,0,image=self.current,anchor='n')
        new_item=self.canvas.create_image(center+sign*width,0,image=picture,anchor='n');started=time.perf_counter()
        def tick():
            elapsed=min(1.,(time.perf_counter()-started)/self.DURATION);offset=(1-(1-elapsed)**3)*width*sign
            self.canvas.coords(old_item,center-offset,0);self.canvas.coords(new_item,center+sign*width-offset,0)
            if elapsed<1:self.job=self.after(16,tick)
            else:self.canvas.delete(old_item);self.current=self.target_photo;self.target_photo=None;self.job=None
        tick()
