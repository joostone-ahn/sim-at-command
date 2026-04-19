# 📡 SIM AT Command Tool

A web-based tool for reading, writing, and decoding SIM/USIM/ISIM card files via AT commands over USB modem port.

Unlike traditional SIM card readers that require PC/SC hardware, this tool communicates directly with the SIM card through an Android device's modem port using `AT+CRSM` and `AT+CSIM` commands.

---

## Requirements

- **Python 3.10+**
- Android device with **DM + MODEM + ADB** USB port mode enabled
- USB cable

> All dependencies (Flask, pyserial, etc.) are installed automatically on first run.

---

## Getting Started

### macOS / Linux

```bash
chmod +x run.command
./run.command
```

Or double-click `run.command`.

### Windows

Double-click `run.bat`.

### After Launch

Browser opens automatically at `http://127.0.0.1:8083`.

1. **Select serial port** — modem port is auto-detected (Samsung/Android)
2. **Connect** — establishes serial connection and verifies AT+CRSM support
3. **Browse SIM files** — 3GPP standard file tree (MF, ADF.USIM, ADF.ISIM)
4. **Click any file** — reads and displays raw hex + decoded data
5. **ADM Verify** — enter ADM1 key to enable write operations
6. **Write** — modify file contents via popup editor

---

## Features

- **AT+CRSM** based SIM file read/write (transparent, linear fixed, cyclic)
- **AT+CSIM** based BER-TLV operations (URSP read/write via RETRIEVE DATA / SET DATA)
- **Auto-detection** of serial modem port
- **3GPP standard file list** — 123 EFs from TS 31.102, TS 102.221
- **Decoded data display** — pySim-based decoders for IMSI, ICCID, SPN, PLMN, UST, and more
- **PLMN table view** — MCC/MNC/AcT decoded table for PLMNwAcT, OPLMNwAcT, HPLMNwAcT, FPLMN, EHPLMN
- **Service table view** — UST/IST/EST with service name and True/False status
- **ACC table view** — Access Control Class bit-level display
- **URSP tree view** — 3GPP TS 24.526 based URSP rule decoding with tree structure
- **Write popup** — hex editor with structure-aware UI (service table toggles, PLMN editor, BER-TLV tag editor)
- **ADM1 verification** — ADM1 key authentication via AT+CSIM for write access

> **Note:** ADF.ISIM files are currently excluded. AT+CRSM cannot distinguish ISIM FIDs from USIM (they overlap), and AT+CSIM SELECT by AID is not supported on some modems. ISIM support may be added in a future update.

---

## Project Structure

```
run.command          # macOS/Linux launcher
run.bat              # Windows launcher
requirements.txt     # Python dependencies (flask, pyserial)
src/
  app.py             # Flask web server + AT command API
  at_modem.py        # Serial port AT command communication
  sim_files.py       # 3GPP standard SIM file definitions
  decoder.py         # pySim-based hex decoder
  templates/
    index.html       # Web GUI (single page)
pysim/               # pySim (Osmocom, modified for URSP support)
```

---

## License

### This Project
© 2026 JUSEOK AHN <ajs3013@lguplus.co.kr>. All rights reserved.

### pySim (Third-party, modified)
The `pysim/` directory contains a modified version of pySim by Osmocom.
- Original: [pySim - Osmocom](https://osmocom.org/projects/pysim/wiki)
- License: **GNU General Public License v2.0 (GPLv2)**
