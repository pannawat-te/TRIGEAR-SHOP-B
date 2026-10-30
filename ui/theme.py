# ไฟล์นี้: ตั้งค่าธีมและรูปแบบวิดเจ็ตของโปรแกรม
"""Shared visual tokens and Tk/ttk defaults for TRI GEAR."""
import tkinter as tk
from tkinter import ttk

NAVY = '#14253D'
BLUE = '#4145F1'
BG = '#F3F5FA'
WHITE = '#FFFFFF'
MUTED = '#64748B'
BORDER = '#DCE5F0'


# def apply_theme: กำหนดรูปแบบพื้นฐานให้วิดเจ็ต Tkinter/ttk ของโปรแกรม
def apply_theme(root):
    from ui.app_fonts import register_fonts, configure_named_fonts
    register_fonts()
    configure_named_fonts(root)
    import customtkinter as ctk
    ctk.set_appearance_mode("light")
    for settings in ctk.ThemeManager.theme.get("CTkFont", {}).values():
        if isinstance(settings, dict):
            settings["family"] = "Noto Sans Thai"
    root.configure(bg=BG)
    root.option_add('*Font', '{Noto Sans Thai} 10')
    root.option_add('*Background', BG)
    root.option_add('*Foreground', NAVY)
    root.option_add('*Button.Background', BLUE)
    root.option_add('*Button.Foreground', WHITE)
    root.option_add('*Button.activeBackground', '#1D4ED8')
    root.option_add('*Button.activeForeground', WHITE)
    root.option_add('*Button.relief', 'flat')
    root.option_add('*Button.padX', 14)
    root.option_add('*Button.padY', 8)
    root.option_add('*Entry.Background', WHITE)
    root.option_add('*Entry.relief', 'solid')
    root.option_add('*Entry.borderWidth', 1)
    root.option_add('*Text.Background', WHITE)
    root.option_add('*Listbox.Background', WHITE)
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    style.configure('.', font=('Noto Sans Thai', 10), background=BG, foreground=NAVY)
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=NAVY)
    style.configure('TButton', padding=(14, 9), background=BLUE, foreground=WHITE, borderwidth=0)
    style.map('TButton', background=[('active', '#1D4ED8'), ('disabled', '#CBD5E1')])
    style.configure('TEntry', padding=7, fieldbackground=WHITE)
    style.configure('Treeview', rowheight=36, background=WHITE, fieldbackground=WHITE, foreground=NAVY, borderwidth=0)
    style.map('Treeview', background=[('selected', '#DBEAFE')], foreground=[('selected', NAVY)])
    style.configure('Treeview.Heading', font=('Noto Sans Thai', 10, 'bold'), padding=9, background='#E9EFF7', foreground=NAVY)
    style.configure('TLabelframe', background=BG, bordercolor=BORDER)
    style.configure('TLabelframe.Label', font=('Noto Sans Thai', 11, 'bold'), background=BG, foreground=NAVY)
