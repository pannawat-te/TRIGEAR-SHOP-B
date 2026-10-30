"""Calendar with explicit foreground/background colors, independent of app Button defaults."""
import calendar
from datetime import date
import tkinter as tk

BG='#F3F5FA';WHITE='#FFFFFF';NAVY='#14253D';BLUE='#4145F1';MUTED='#64748B'
MONTHS=('มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม')


def pick_date(parent,variable):
    try:current=date.fromisoformat(variable.get())
    except (ValueError,TypeError):current=date.today()
    win=tk.Toplevel(parent);win.title('เลือกวันที่');win.transient(parent);win.resizable(False,False)
    win.configure(bg=WHITE)
    year,month=current.year,current.month
    heading=tk.StringVar()
    nav=tk.Frame(win,bg=WHITE);nav.pack(fill='x',padx=18,pady=(18,12))
    nav.columnconfigure(1,weight=1)
    body=tk.Frame(win,bg=WHITE);body.pack(padx=18,pady=(0,12))
    for col in range(7):body.columnconfigure(col,weight=1,uniform='days')
    def close():
        try:win.grab_release()
        except tk.TclError:pass
        win.destroy()
    def choose(day):
        variable.set(date(year,month,day).isoformat());close()
    def make_button(container,title,command,selected=False):
        return tk.Button(container,text=title,command=command,font=('Noto Sans Thai',12,'bold'),
            bg=BLUE if selected else WHITE,fg=WHITE if selected else NAVY,
            activebackground=BLUE,activeforeground=WHITE,disabledforeground=MUTED,
            relief='flat',bd=0,highlightthickness=1,highlightbackground=BLUE if selected else '#E4E8F1',
            highlightcolor=BLUE,padx=0,pady=5,width=4,cursor='hand2',takefocus=True)
    def render():
        heading.set(f'{MONTHS[month-1]} {year}')
        for w in body.winfo_children():w.destroy()
        for col,name in enumerate(['จ','อ','พ','พฤ','ศ','ส','อา']):
            tk.Label(body,text=name,font=('Noto Sans Thai',11,'bold'),bg=WHITE,fg=MUTED,padx=4,pady=8).grid(row=0,column=col,sticky='ew')
        for row,week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(year,month),1):
            for col,day in enumerate(week):
                if day:
                    chosen=date(year,month,day)==current
                    b=make_button(body,str(day),lambda d=day:choose(d),chosen)
                    b.grid(row=row,column=col,sticky='nsew',padx=3,pady=3)
                else:tk.Label(body,text='',bg=WHITE,width=4).grid(row=row,column=col)
    def move(step):
        nonlocal year,month
        index=year*12+month-1+step;new_year,zero=divmod(index,12)
        if not 1<=new_year<=9999:return
        year,month=new_year,zero+1;render()
    make_button(nav,'‹',lambda:move(-1)).grid(row=0,column=0)
    tk.Label(nav,textvariable=heading,font=('Noto Sans Thai',15,'bold'),bg=WHITE,fg=NAVY,width=21).grid(row=0,column=1,padx=8)
    make_button(nav,'›',lambda:move(1)).grid(row=0,column=2)
    foot=tk.Frame(win,bg=WHITE);foot.pack(fill='x',padx=18,pady=(0,16))
    def today():
        variable.set(date.today().isoformat());close()
    make_button(foot,'วันนี้',today).pack(side='left')
    cancel=make_button(foot,'ยกเลิก',close);cancel.configure(width=7);cancel.pack(side='right')
    tk.Label(foot,text='ปี ค.ศ. · บันทึก YYYY-MM-DD',bg=WHITE,fg=MUTED,font=('Noto Sans Thai',9)).pack(side='left',padx=12)
    win.protocol('WM_DELETE_WINDOW',close);win.bind('<Escape>',lambda event:close())
    render();win.update_idletasks()
    x=parent.winfo_rootx()+(parent.winfo_width()-win.winfo_reqwidth())//2
    y=parent.winfo_rooty()+(parent.winfo_height()-win.winfo_reqheight())//2
    x=max(0,min(x,win.winfo_screenwidth()-win.winfo_reqwidth()))
    y=max(0,min(y,win.winfo_screenheight()-win.winfo_reqheight()))
    win.geometry(f'+{x}+{y}');win.grab_set();win.focus_set();win.wait_window()
