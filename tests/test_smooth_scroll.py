import sys,unittest,types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ui.mouse_scroll import SmoothScroll,wheel_pixels
class Canvas:
 def __init__(self,total=3000,viewport=600):self.total=total;self.viewport=viewport;self.pos=0.;self.now=0.;self.jobs={};self.next=0;self.tk=types.SimpleNamespace(splitlist=lambda x:x.split())
 def bind(self,*a,**k):pass
 def cget(self,key):return f'0 0 400 {self.total}' if key=='scrollregion' else '0'
 def winfo_height(self):return self.viewport
 def yview(self):return self.pos/self.total,min(1,(self.pos+self.viewport)/self.total)
 def yview_moveto(self,first):self.pos=max(0,min(self.total-self.viewport,first*self.total))
 def after(self,ms,callback):self.next+=1;self.jobs[self.next]=(self.now+ms/1000,callback);return self.next
 def after_cancel(self,key):self.jobs.pop(key,None)
 def winfo_exists(self):return True
 def pump(self):
  while self.jobs:
   key=min(self.jobs,key=lambda k:self.jobs[k][0]);self.now,callback=self.jobs.pop(key);callback()
class Tests(unittest.TestCase):
 def make(self):
  c=Canvas();return c,SmoothScroll(c,clock=lambda:c.now)
 def test_fractional_wheel(self):
  self.assertEqual(wheel_pixels(types.SimpleNamespace(delta=30), 'win32'),-22.5)
  self.assertEqual(wheel_pixels(types.SimpleNamespace(num=5)),90)
 def test_burst_one_job_and_bounds(self):
  c,s=self.make()
  for _ in range(50):s.scroll(90);self.assertEqual(len(c.jobs),1)
  c.pump();self.assertAlmostEqual(c.pos,2400);self.assertIsNone(s.job);self.assertFalse(s.scroll(90))
 def test_reverse(self):
  c,s=self.make();c.pos=600;s.scroll(360);s.scroll(-90);c.pump();self.assertAlmostEqual(c.pos,510)
 def test_cancel(self):
  c,s=self.make();s.scroll(90);s._destroy(types.SimpleNamespace(widget=c));self.assertEqual(c.jobs,{})
 def test_external_scrollbar_wins(self):
  c,s=self.make();s.scroll(360);c.pos=1000;c.pump();self.assertEqual(c.pos,1000)
 def test_no_scroll_for_short_content(self):
  c=Canvas(total=300,viewport=600);s=SmoothScroll(c);self.assertFalse(s.scroll(90))
if __name__ == '__main__':unittest.main()
