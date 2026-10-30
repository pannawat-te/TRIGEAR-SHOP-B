"""CustomTkinter widgets with explicit adapters for the existing Tkinter UI.

No global monkey-patching: database/services do not depend on this module.
"""
import math
import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk

BLUE='#4145F1';NAVY='#14253D';BG='#F3F5FA';BORDER='#E3E8F1'
ctk.set_appearance_mode('light')
ctk.set_default_color_theme('blue')


def background(parent):
    if isinstance(parent,ctk.CTkBaseClass):
        color=parent.cget('fg_color')
        if color!='transparent':return color
    try:return parent.cget('bg')
    except tk.TclError:return BG


def pixel_font(value=('Noto Sans Thai',10,'bold')):
    if isinstance(value,ctk.CTkFont):return value
    values=list(value);values[1]=max(12,round(abs(values[1])*4/3))
    return tuple(values)


class ActionButton(ctk.CTkButton):
    """Tk-like options are translated at this one boundary; CTk draws the shape."""
    def __init__(self,master,**kwargs):
        text=kwargs.pop('text','');command=kwargs.pop('command',None)
        width=kwargs.pop('width',None);height=kwargs.pop('height',None)
        font=kwargs.pop('font',('Noto Sans Thai',10,'bold'))
        wrap=kwargs.pop('wraplength',0)
        bg=kwargs.pop('bg',BLUE);fg=kwargs.pop('fg','white' if bg==BLUE else NAVY)
        hover=kwargs.pop('activebackground',None) or ('#3337D1' if bg==BLUE else '#EEEDFF')
        disabled=kwargs.pop('disabledforeground','#94A3B8')
        border=kwargs.pop('highlightbackground',BORDER)
        border_width=kwargs.pop('highlightthickness',0)
        for key in ('bd','borderwidth','relief','padx','pady','activeforeground','justify','overrelief'):
            kwargs.pop(key,None)
        if width is None:
            measure=tkfont.Font(root=master,font=font).measure(str(text))
            width=max(42,min(320,measure+30))
        else:width=max(34,int(width)*8+24)
        height=42 if height is None else max(36,int(height)*20+16)
        if wrap:
            width=min(width,wrap+30)
            lines=max(1,math.ceil(tkfont.Font(root=master,font=font).measure(str(text))/max(1,wrap)))
            height=max(height,min(lines,3)*20+16)
        super().__init__(master,text=text,command=command,width=width,height=height,
            corner_radius=11,border_width=min(1,border_width),border_color=border,
            fg_color=bg,text_color=fg,hover_color=hover,text_color_disabled=disabled,
            bg_color=background(master),font=pixel_font(font),**kwargs)
        self._legacy_wrap=wrap
        self._set_wrap()
    def _set_wrap(self):
        # CTk 5/6 render text with a native Label; wrap only that label.
        if self._legacy_wrap and self._text_label is not None:
            self._text_label.configure(wraplength=self._apply_widget_scaling(self._legacy_wrap))
    def configure(self,require_redraw=False,**kwargs):
        for old,new in [('bg','fg_color'),('fg','text_color'),('activebackground','hover_color'),('disabledforeground','text_color_disabled')]:
            if old in kwargs:kwargs[new]=kwargs.pop(old)
        for key in ('relief','bd','padx','pady','activeforeground'):kwargs.pop(key,None)
        if 'height' in kwargs and kwargs['height']<=5:kwargs['height']=int(kwargs['height'])*20+16
        if 'wraplength' in kwargs:self._legacy_wrap=kwargs.pop('wraplength')
        result=super().configure(require_redraw=require_redraw,**kwargs)
        if hasattr(self,'_legacy_wrap'):self._set_wrap()
        return result
    config=configure
    def cget(self,name):
        return super().cget({'bg':'fg_color','fg':'text_color','activebackground':'hover_color'}.get(name,name))


class RoundedCard(tk.Frame):
    """Padded native content inside a real CTkFrame, with external geometry on shell.

The returned content retains Tk bg/child semantics for existing page code.
The shell is owned by the original parent, so parent destruction removes both.
"""
    def __init__(self,parent,**kwargs):
        bg=kwargs.pop('bg','white');px=kwargs.pop('padx',20);py=kwargs.pop('pady',18)
        radius=kwargs.pop('corner_radius',18)
        border=kwargs.pop('highlightbackground',BORDER)
        bw=kwargs.pop('highlightthickness',1)
        width=kwargs.pop('width',200);height=kwargs.pop('height',100)
        self.shell=ctk.CTkFrame(parent,fg_color=bg,bg_color=background(parent),
            corner_radius=radius,border_width=bw,border_color=border,width=width,height=height)
        super().__init__(self.shell,bg=bg,**kwargs)
        tk.Frame.pack(self,fill='both',expand=True,padx=max(px,radius),pady=max(py,radius))
        self.pack=self.shell.pack;self.grid=self.shell.grid;self.place=self.shell.place
        self.pack_info=self.shell.pack_info;self.grid_info=self.shell.grid_info
        self.pack_forget=self.shell.pack_forget;self.grid_forget=self.shell.grid_forget
        self.grid_configure=self.shell.grid_configure;self.grid_config=self.shell.grid_configure
        self.pack_configure=self.shell.pack_configure;self.pack_config=self.shell.pack_configure
        self.pack_propagate=self.shell.pack_propagate;self.grid_propagate=self.shell.grid_propagate
    def configure(self,cnf=None,**kwargs):
        if 'bg' in kwargs and hasattr(self,'shell'):self.shell.configure(fg_color=kwargs['bg'])
        return super().configure(cnf,**kwargs)
    config=configure


class CheckBox(ctk.CTkCheckBox):
    def __init__(self,parent,**kwargs):
        text=kwargs.pop('text','');fg=kwargs.pop('fg',NAVY);bg=kwargs.pop('bg',background(parent))
        font=kwargs.pop('font',('Noto Sans Thai',11));wrap=kwargs.pop('wraplength',0)
        for key in ('selectcolor','justify','bd','relief','padx','pady'):kwargs.pop(key,None)
        super().__init__(parent,text=text,text_color=fg,bg_color=bg,fg_color=BLUE,hover_color='#3337D1',
            border_color='#A5B1C6',corner_radius=6,checkbox_width=22,checkbox_height=22,
            border_width=2,width=24 if not text else 150,height=30,font=pixel_font(font),**kwargs)
        if wrap and self._text_label:self._text_label.configure(wraplength=wrap,justify='left')


class SizeChoice(ActionButton):
    def __init__(self,parent,**kwargs):
        self.variable=kwargs.pop('variable');self.value=kwargs.pop('value');command=kwargs.pop('command',None)
        self._trace=None
        kwargs.pop('indicatoron',None);kwargs.pop('selectcolor',None)
        kwargs['command']=lambda:(self.variable.set(self.value),command() if command else None)
        kwargs['bg']='white';kwargs['fg']=BLUE;kwargs['highlightthickness']=1
        super().__init__(parent,**kwargs)
        self._trace=self.variable.trace_add('write',self._sync);self._sync()
    def _sync(self,*args):
        if self.winfo_exists():
            selected=str(self.variable.get())==str(self.value)
            self.configure(fg_color=BLUE if selected else 'white',text_color='white' if selected else NAVY,
                border_color=BLUE if selected else BORDER,hover_color='#3337D1' if selected else '#EEEDFF')
    def destroy(self):
        if self._trace:
            self.variable.trace_remove('write',self._trace);self._trace=None
        super().destroy()


def RadioButton(parent,**kwargs):
    if kwargs.get('indicatoron',True) is False:return SizeChoice(parent,**kwargs)
    font=kwargs.pop('font',('Noto Sans Thai',10));bg=kwargs.pop('bg','white');fg=kwargs.pop('fg',NAVY)
    wrap=kwargs.pop('wraplength',0)
    for key in ('anchor','justify','selectcolor','padx','pady','bd','relief'):kwargs.pop(key,None)
    widget=ctk.CTkRadioButton(parent,bg_color=bg,text_color=fg,font=pixel_font(font),
        fg_color=BLUE,hover_color=BLUE,border_color='#A5B1C6',radiobutton_width=19,radiobutton_height=19,
        height=30,**kwargs)
    if wrap and widget._text_label:widget._text_label.configure(wraplength=wrap,justify='left')
    return widget


def option_menu(parent,variable,values,width=220,command=None):
    return ctk.CTkOptionMenu(parent,variable=variable,values=list(values),width=width,height=40,
        corner_radius=10,fg_color='#EEF0F7',button_color='#E0E4EF',button_hover_color='#D1D7E7',
        text_color=NAVY,font=('Noto Sans Thai',14),dropdown_font=('Noto Sans Thai',14),
        dropdown_fg_color='white',dropdown_text_color=NAVY,dropdown_hover_color='#EEEDFF',command=command)
