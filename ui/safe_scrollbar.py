"""Coalesce Canvas notifications; never redraw a CTk scrollbar inside its own idle pass."""
import tkinter as tk


def connect_scrollbar(canvas, scrollbar):
    state={'job':None,'latest':None,'shown':None,'closed':False}
    def flush():
        state['job']=None
        if state['closed']:return
        values=state['latest']
        if values==state['shown']:return
        state['shown']=values
        try:scrollbar.set(*values)
        except tk.TclError:pass
    def notify(first,last):
        values=(round(float(first),7),round(float(last),7))
        state['latest']=values
        if not state['closed'] and values!=state['shown'] and state['job'] is None:
            state['job']=canvas.after(16,flush)
    def close(event):
        if event.widget!=canvas:return
        state['closed']=True
        if state['job'] is not None:
            try:canvas.after_cancel(state['job'])
            except tk.TclError:pass
            state['job']=None
    canvas.configure(yscrollcommand=notify)
    canvas.bind('<Destroy>',close,add='+')
    return notify
