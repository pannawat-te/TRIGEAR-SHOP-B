"""Scoped CustomTkinter components for storefront/details; other pages keep their APIs."""
import tkinter as tk
import customtkinter as ctk
from ui.mouse_scroll import enable_mouse_scroll

BG='#F3F5FA';WHITE='#FFFFFF';NAVY='#14253D';BLUE='#4145F1';MUTED='#718097';BORDER='#E3E8F2'
ctk.set_appearance_mode('light')


def panel(parent,**kwargs):
    return ctk.CTkFrame(parent,fg_color=WHITE,corner_radius=16,border_width=1,border_color=BORDER,**kwargs)


def button(parent,title,command,kind='primary',**kwargs):
    bg,fg,hover={'primary':(BLUE,WHITE,'#3337CD'),'secondary':(WHITE,BLUE,'#F0EFFF'),
        'muted':('#EEEDFF',BLUE,'#E1E0FF'),'danger':(WHITE,'#CA3445','#FFF0F2')}[kind]
    return ctk.CTkButton(parent,text=title,command=command,height=44,corner_radius=10,
        fg_color=bg,text_color=fg,hover_color=hover,border_width=0 if kind in ('primary','muted') else 1,
        border_color='#F2C8CE' if kind=='danger' else BORDER,font=('Noto Sans Thai',16,'bold'),**kwargs)


def label(parent,title,size=14,bold=False,color=NAVY,**kwargs):
    return ctk.CTkLabel(parent,text=title,text_color=color,font=('Noto Sans Thai',size,'bold' if bold else 'normal'),**kwargs)


def scroll_area(parent,bg=BG):
    outer=tk.Frame(parent,bg=bg)
    canvas=tk.Canvas(outer,bg=bg,highlightthickness=0,bd=0)
    scrollbar=ctk.CTkScrollbar(outer,command=canvas.yview,width=12,fg_color=bg,
        button_color='#CCD3E1',button_hover_color='#A7B4CA')
    scrollbar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    inner=tk.Frame(canvas,bg=bg);window=canvas.create_window((0,0),window=inner,anchor='nw')
    inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
    from ui.safe_scrollbar import connect_scrollbar
    connect_scrollbar(canvas,scrollbar)
    enable_mouse_scroll(canvas,inner)
    return outer,canvas,inner
