# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SIM AT Command Tool — single-file exe build.

Usage (from installer/ directory):
    python -m PyInstaller --clean --noconfirm sim-at-command.spec
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
PYSIM_DIR = os.path.join(PROJECT_ROOT, 'pysim')

# ---------------------------------------------------------------------------
# Hidden imports — pySim uses many lazy / dynamic imports
# ---------------------------------------------------------------------------
hidden = []
hidden += collect_submodules('pySim')
hidden += collect_submodules('construct')
hidden += collect_submodules('pyosmocom')
hidden += [
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'flask',
    'jinja2',
    'markupsafe',
    'cmd2',
    'jsonpath_ng',
    'bidict',
    'yaml',
    'termcolor',
    'colorlog',
    'Cryptodome',
    'pytlv',
    'packaging',
    'asn1tools',
]

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------
datas = [
    # Flask templates
    (os.path.join(SRC_DIR, 'templates'), os.path.join('src', 'templates')),
    # pySim ASN.1 definitions (needed at runtime)
    (os.path.join(PYSIM_DIR, 'pySim', 'esim', 'asn1'), os.path.join('pysim', 'pySim', 'esim', 'asn1')),
]

# Collect pySim package data (asn files etc.) via hook
pysim_data = collect_data_files('pySim')
datas += pysim_data

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [os.path.join(SPECPATH, 'launcher.py')],
    pathex=[SRC_DIR, PYSIM_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages not needed at runtime
        'tkinter', '_tkinter', 'matplotlib', 'numpy', 'scipy',
        'PIL', 'IPython', 'notebook', 'pytest',
        'twisted', 'klein', 'psycopg2',
        'pyscard',          # PC/SC smart card — not used (AT modem only)
        'smartcard',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SIM-AT-Command',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,           # Keep console window for AT log output
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,              # Add .ico path here if desired
)
