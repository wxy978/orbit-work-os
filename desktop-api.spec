# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for package in ["uvicorn", "fastapi", "pydantic", "langchain_text_splitters", "tiktoken", "docx", "pypdf"]:
    d, b, h = collect_all(package)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(["backend/desktop_entry.py"], pathex=["backend"], binaries=binaries, datas=datas, hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="orbit-api", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
