"""Regression: notifications raised while CTk draws must never re-enter .set()."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ui.safe_scrollbar import connect_scrollbar

class Canvas:
    def __init__(self):self.jobs={};self.counter=0
    def configure(self,**kwargs):self.notify=kwargs['yscrollcommand']
    def bind(self,event,callback,**kwargs):self.close=callback
    def after(self,delay,callback):self.counter+=1;self.jobs[self.counter]=callback;return self.counter
    def after_cancel(self,key):self.jobs.pop(key,None)
    def flush(self):
        jobs=list(self.jobs.values());self.jobs.clear()
        for job in jobs:job()

class Scrollbar:
    def __init__(self,canvas):self.canvas=canvas;self.calls=[];self.drawing=False
    def set(self,*values):
        assert not self.drawing,'recursive scrollbar redraw'
        self.drawing=True;self.calls.append(values)
        self.canvas.notify(*values)
        self.drawing=False

class Tests(unittest.TestCase):
    def test_coalesces_notifications_without_recursion(self):
        c=Canvas();s=Scrollbar(c);connect_scrollbar(c,s)
        for n in range(100):c.notify(n/200,.9)
        self.assertEqual(len(c.jobs),1);self.assertEqual(s.calls,[])
        c.flush();self.assertEqual(s.calls,[(.495,.9)]);self.assertEqual(c.jobs,{})
    def test_unchanged_position_does_not_redraw(self):
        c=Canvas();s=Scrollbar(c);connect_scrollbar(c,s);c.notify('0','1');c.flush();c.notify('0','1')
        self.assertEqual(len(s.calls),1);self.assertEqual(c.jobs,{})
    def test_destroy_cancels_pending_draw(self):
        from types import SimpleNamespace
        c=Canvas();s=Scrollbar(c);connect_scrollbar(c,s);c.notify('0','.5');c.close(SimpleNamespace(widget=c))
        c.flush();self.assertEqual(s.calls,[])

if __name__=='__main__':unittest.main()
