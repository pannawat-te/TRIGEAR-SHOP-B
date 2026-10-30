"""One mouse-wheel dispatcher per Tk root, with bounded, cancellable pixel animation."""
import time
import tkinter as tk


def wheel_units(event):
    """Legacy public helper, retained for other pages."""
    if getattr(event,'num',None)==4:return -3
    if getattr(event,'num',None)==5:return 3
    delta=getattr(event,'delta',0)
    return 0 if not delta else -max(1,int(abs(delta)/120))*3 if delta>0 else max(1,int(abs(delta)/120))*3


def wheel_pixels(event,system='win32'):
    if getattr(event,'num',None)==4:return -90.0
    if getattr(event,'num',None)==5:return 90.0
    delta=float(getattr(event,'delta',0) or 0)
    if system=='aqua':return max(-240.0,min(240.0,-delta*8.0))
    return max(-360.0,min(360.0,-delta/120.0*90.0))


class SmoothScroll:
    DURATION=.16
    def __init__(self,canvas,clock=time.perf_counter):
        self.canvas=canvas;self.clock=clock;self.job=None;self.target=0.;self.origin=0.;self.started=0.;self.last=None
        canvas.bind('<Destroy>',self._destroy,add='+')
        canvas.bind('<ButtonPress-1>',lambda e:self.stop(),add='+')
    def limits(self):
        values=self.canvas.tk.splitlist(self.canvas.cget('scrollregion'))
        if len(values)!=4:return 0.,0.
        top,bottom=float(values[1]),float(values[3]);total=max(0.,bottom-top)
        viewport=max(1,self.canvas.winfo_height()-2*int(float(self.canvas.cget('highlightthickness'))))
        return total,max(0.,total-viewport)
    def position(self,total):return self.canvas.yview()[0]*total
    def stop(self):
        if self.job is not None:
            try:self.canvas.after_cancel(self.job)
            except tk.TclError:pass
        self.job=None;self.last=None
    def _destroy(self,event):
        if event.widget==self.canvas:self.stop()
    def scroll(self,pixels):
        total,maximum=self.limits()
        if maximum<=0 or not pixels:return False
        current=self.position(total)
        base=self.target if self.job is not None else current
        if (base-current)*pixels<0:base=current
        target=min(maximum,max(0.,base+pixels))
        if abs(target-current)<.25 and self.job is None:return False
        self.target=target;self.origin=current;self.started=self.clock();self.last=current
        if self.job is None:self.job=self.canvas.after(0,self._tick)
        return True
    def _tick(self):
        self.job=None
        try:
            if not self.canvas.winfo_exists():return
            total,maximum=self.limits()
            if total<=0:return
            current=self.position(total)
            # A scrollbar drag or external yview command wins over an old animation.
            if self.last is not None and abs(current-self.last)>3:
                self.last=None;return
            self.target=min(maximum,max(0.,self.target))
            progress=min(1.,max(0.,(self.clock()-self.started)/self.DURATION))
            eased=1-(1-progress)**3
            position=self.origin+(self.target-self.origin)*eased
            self.canvas.yview_moveto(min(maximum,max(0.,position))/total)
            self.last=self.position(total)
            if progress<1 and abs(self.last-self.target)>.5:self.job=self.canvas.after(16,self._tick)
            else:self.canvas.yview_moveto(self.target/total);self.last=None
        except tk.TclError:self.job=None;self.last=None


def enable_mouse_scroll(canvas,content):
    content._scroll_canvas=canvas;canvas._scroll_canvas=canvas
    if not hasattr(canvas,'_smooth_scroll'):canvas._smooth_scroll=SmoothScroll(canvas)
    root=canvas._root()
    if getattr(root,'_wheel_installed',False):return
    root._wheel_installed=True
    system=str(root.tk.call('tk','windowingsystem'))
    def dispatch(event):
        try:
            widget=root.winfo_containing(event.x_root,event.y_root)
            if widget is None:return
            if widget.winfo_class() in ('Text','Listbox','Treeview','TCombobox','Spinbox','TSpinbox','Menu'):return
            pixels=wheel_pixels(event,system)
            while widget is not None:
                target=getattr(widget,'_scroll_canvas',None)
                if target is not None and target.winfo_exists() and target._smooth_scroll.scroll(pixels):return 'break'
                widget=getattr(widget,'master',None)
        except tk.TclError:return
    for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):root.bind_all(sequence,dispatch,add='+')
