"""Bundled UI fonts, registered for this process without administrator access."""
from pathlib import Path
import ctypes
import sys

FAMILY = 'Noto Sans Thai'
_registered = False
_handles = []


def register_fonts():
    global _registered
    if _registered:
        return
    paths = sorted((Path(__file__).resolve().parents[1] / 'assets' / 'fonts').glob('NotoSansThai-*.ttf'))
    if not paths:
        raise RuntimeError('Missing assets/fonts/NotoSansThai font files; extract the complete font patch.')
    if sys.platform == 'win32':
        add = ctypes.windll.gdi32.AddFontResourceExW
        add.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        add.restype = ctypes.c_int
        for path in paths:
            if not add(str(path), 0x10, None):
                raise RuntimeError(f'Cannot load bundled font: {path.name}')
    elif sys.platform == 'darwin':
        from ctypes.util import find_library
        cf = ctypes.CDLL(find_library('CoreFoundation'))
        ct = ctypes.CDLL(find_library('CoreText'))
        cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
        cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
        ct.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        for path in paths:
            raw = str(path).encode()
            url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
            try:
                ct.CTFontManagerRegisterFontsForURL(url, 1, None)
            finally:
                cf.CFRelease(url)
        _handles.extend([cf, ct])
    else:
        from ctypes.util import find_library
        fc = ctypes.CDLL(find_library('fontconfig'))
        fc.FcConfigGetCurrent.restype = ctypes.c_void_p
        fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        fc.FcConfigAppFontAddFile.restype = ctypes.c_int
        config = fc.FcConfigGetCurrent()
        for path in paths:
            if not fc.FcConfigAppFontAddFile(config, str(path).encode()):
                raise RuntimeError(f'Cannot load bundled font: {path.name}')
        _handles.append(fc)
    _registered = True


def configure_named_fonts(root):
    from tkinter import font
    for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont', 'TkCaptionFont', 'TkSmallCaptionFont', 'TkIconFont', 'TkTooltipFont'):
        font.nametofont(name, root=root).configure(family=FAMILY)
