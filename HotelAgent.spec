# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\alfre\\desktop\\hotelagent\\gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('config/settings.yaml', 'config'), ('config/system_prompt.txt', 'config'), ('KNOWLEDGE.md', '.'), ('PRICES.md', '.'), ('config/pricing_rules.md', 'config'), ('data/conversations', 'data/conversations'), ('data/uploads', 'data/uploads'), ('data/logs', 'data/logs'), ('data/automations', 'data/automations')],
    hiddenimports=['customtkinter', 'typer', 'rich', 'openai', 'yaml', 'dotenv', 'loguru', 'scripts.config_manager', 'scripts.llm', 'scripts.gmail', 'scripts.email_provider', 'scripts.email_processor', 'scripts.memory', 'scripts.documents', 'scripts.voice', 'scripts.web_scraper', 'scripts.price_manager', 'scripts.agent_manager', 'scripts.automation_manager', 'scripts.scheduler', 'agents.base_agent', 'agents.hotel_agent'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HotelAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HotelAgent',
)
