"""Run SMTP outside Tk's UI thread; poll results only from the UI thread."""
import queue
import threading

def run_task(widget, buttons, action, success, failure):
    for button in buttons: button.configure(state='disabled')
    result = queue.Queue()
    def work():
        try: result.put((True,action()))
        except Exception as exc: result.put((False,exc))
    threading.Thread(target=work,daemon=True).start()
    def poll():
        if not widget.winfo_exists(): return
        try: ok,value = result.get_nowait()
        except queue.Empty:
            widget.after(100,poll);return
        for button in buttons:
            if button.winfo_exists(): button.configure(state='normal')
        if ok: success(value)
        else: failure(value)
    widget.after(100,poll)
