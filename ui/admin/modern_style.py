"""Shared Admin navigation and real CTk components; no application-wide widget patches."""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ui.storefront_style import panel,button,label,scroll_area,BG,WHITE,NAVY,BLUE,MUTED,BORDER


def chrome(owner,title,subtitle,active):
    owner.frame.configure(bg=BG)
    sidebar=ctk.CTkFrame(owner.frame,width=210,fg_color=WHITE,corner_radius=0)
    sidebar.pack(side='left',fill='y');sidebar.pack_propagate(False)
    try:
        from ui.brand import logo
        image=logo((135,64));brand=tk.Label(sidebar,image=image,bg=WHITE);brand.image=image;brand.pack(pady=(22,5))
    except (OSError,ValueError):label(sidebar,'TRIGEAR',25,True).pack(pady=20)
    label(sidebar,'ADMIN PANEL',12,color=MUTED).pack(pady=(0,20))
    ctx=getattr(owner.root,'_admin_context',{})
    def go(key):
        if key==active:return
        owner.frame.destroy()
        root=owner.root;back=lambda:open_dashboard(root)
        if key=='home':open_dashboard(root)
        elif key=='products':
            from ui.admin.products import AdminProductsPage
            AdminProductsPage(root,back)
        elif key=='orders':
            from ui.admin.orders import AdminOrdersPage
            AdminOrdersPage(root,back)
        elif key=='members':
            from ui.admin.members import AdminMembersPage
            AdminMembersPage(root,ctx.get('id'),back)
        elif key=='resets':
            from ui.admin.password_resets import AdminPasswordResetsPage
            AdminPasswordResetsPage(root,ctx.get('id'),back)
    for text,key in [('ภาพรวม','home'),('จัดการสินค้า','products'),('คำสั่งซื้อ','orders'),('จัดการสมาชิก','members'),('คำขอรีเซ็ตรหัสผ่าน','resets')]:
        button(sidebar,text,lambda k=key:go(k),'muted' if key==active else 'secondary',width=184).pack(fill='x',padx=12,pady=5)
    def email():
        from ui.email_settings import show_email_settings
        show_email_settings(owner.root,ctx.get('id'))
    button(sidebar,'ตั้งค่าอีเมล OTP',email,'secondary',width=184).pack(fill='x',padx=12,pady=5)
    button(sidebar,'ออกจากระบบ',ctx.get('logout') or getattr(owner.root,'_logout_callback',getattr(owner,'back_callback',lambda:None)),'danger',width=184).pack(side='bottom',fill='x',padx=12,pady=22)
    main=tk.Frame(owner.frame,bg=BG);main.pack(side='left',fill='both',expand=True)
    head=tk.Frame(main,bg=BG);head.pack(fill='x',padx=24,pady=(22,14))
    label(head,title,27,True,anchor='w').pack(anchor='w')
    label(head,subtitle,14,color=MUTED,anchor='w').pack(anchor='w',pady=(4,0))
    owner.admin_header=head
    return main


def open_dashboard(root):
    from ui.admin.dashboard import AdminDashboard
    ctx=getattr(root,'_admin_context',{})
    AdminDashboard(root,ctx.get('logout') or getattr(root,'_logout_callback',lambda:None),ctx.get('id'))


def entry(parent,variable=None,width=220,placeholder=''):
    return ctk.CTkEntry(parent,textvariable=variable,width=width,height=42,corner_radius=10,border_color=BORDER,fg_color=WHITE,text_color=NAVY,font=('Noto Sans Thai',15),placeholder_text=placeholder)


def menu(parent,variable,values,command=None,width=180):
    return ctk.CTkOptionMenu(parent,variable=variable,values=list(values),command=command,width=width,height=42,corner_radius=10,fg_color='#ECEFF7',button_color='#DDE3F0',text_color=NAVY,font=('Noto Sans Thai',14),dropdown_font=('Noto Sans Thai',14))


def metrics(parent,items):
    row=tk.Frame(parent,bg=BG);row.pack(fill='x',pady=(0,16));values=[]
    for i,(title,value) in enumerate(items):
        row.columnconfigure(i,weight=1,uniform='metric')
        c=panel(row);c.grid(row=0,column=i,sticky='nsew',padx=(0,8))
        label(c,title,14,color=MUTED,anchor='w').pack(fill='x',padx=16,pady=(14,4))
        v=label(c,str(value),26,True,anchor='w');v.pack(fill='x',padx=16,pady=(0,16));values.append(v)
    state={'columns':None}
    def reflow(event):
        columns=len(items) if event.width>=950 else min(2,len(items))
        if state['columns']==columns:return
        state['columns']=columns
        cards=row.winfo_children()
        for col in range(len(items)):row.columnconfigure(col,weight=1 if col<columns else 0,uniform='metric' if col<columns else '')
        for i,c in enumerate(cards):c.grid_configure(row=i//columns,column=i%columns,padx=(0,8),pady=(0,8))
    row.bind('<Configure>',reflow,add='+')
    return values


def table(parent,columns,height=9):
    box=tk.Frame(parent,bg=WHITE)
    style=ttk.Style(parent)
    style.configure('Admin.Treeview',rowheight=42,borderwidth=0,relief='flat',font=('Noto Sans Thai',10))
    style.configure('Admin.Treeview.Heading',background='#F0F3F9',foreground=NAVY,font=('Noto Sans Thai',10,'bold'),relief='flat')
    tree=ttk.Treeview(box,style='Admin.Treeview',columns=[x[0] for x in columns],show='headings',height=height,selectmode='browse')
    for key,title,width in columns:
        tree.heading(key,text=title);tree.column(key,width=width,minwidth=65,anchor='w',stretch=key in ('name','user','order'))
    y=ttk.Scrollbar(box,command=tree.yview);y.pack(side='right',fill='y')
    x=ttk.Scrollbar(box,orient='horizontal',command=tree.xview);x.pack(side='bottom',fill='x')
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);tree.pack(fill='both',expand=True)
    for tag,bg,fg in [('low','#FFF4DE','#965600'),('empty','#FFE8EB','#AF2437'),('ok','#EDFAF3','#176943')]:tree.tag_configure(tag,background=bg,foreground=fg)
    return box,tree
