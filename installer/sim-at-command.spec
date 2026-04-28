# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for SIM AT Command Tool

import os
import sys

block_cipher = None

# Project root (one level up from installer/)
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(SPECPATH, 'launcher.py')],
    pathex=[
        os.path.join(PROJECT_ROOT, 'src'),
        os.path.join(PROJECT_ROOT, 'pysim'),
    ],
    binaries=[],
    datas=[
        # Flask templates
        (os.path.join(PROJECT_ROOT, 'src', 'templates'), os.path.join('src', 'templates')),
        # Source modules (imported at runtime)
        (os.path.join(PROJECT_ROOT, 'src', 'app.py'), os.path.join('src', '.')),
        (os.path.join(PROJECT_ROOT, 'src', 'at_modem.py'), os.path.join('src', '.')),
        (os.path.join(PROJECT_ROOT, 'src', 'decoder.py'), os.path.join('src', '.')),
        (os.path.join(PROJECT_ROOT, 'src', 'sim_files.py'), os.path.join('src', '.')),
        # pySim package
        (os.path.join(PROJECT_ROOT, 'pysim', 'pySim'), 'pySim'),
    ],
    hiddenimports=[
        'flask',
        'jinja2',
        'markupsafe',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'construct',
        'bidict',
        'osmocom',
        'osmocom.utils',
        'osmocom.tlv',
        'osmocom.construct',
        'yaml',
        'colorlog',
        'jsonpath_ng',
        'Cryptodome',
        'asn1tools',
        'packaging',
        'cmd2',
        'pytlv',
        'termcolor',
        'pySim',
        'pySim.filesystem',
        'pySim.ts_102_221',
        'pySim.ts_31_102',
        'pySim.ts_31_103',
        'pySim.ts_31_102_telecom',
        'pySim.ts_31_103_shared',
        'pySim.legacy',
        'pySim.legacy.cards',
        'pySim.cat',
        'pySim.ota',
        'pySim.euicc',
        'pySim.ara_m',
        'pySim.cdma_ruim',
        'pySim.sysmocom_sja2',
        'pySim.gsm_r',
        'pySim.ts_51_011',
        'pySim.ts_102_222',
        'pySim.ts_31_104',
        'pySim.ts_24_526',
        'pySim.esim',
        'pySim.esim.saip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy.testing',
        'PIL',
        'cv2',
        'twisted',
        'klein',
        'psycopg2',
        'pyscard',
        'smartcard',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SIM-AT-Command',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
