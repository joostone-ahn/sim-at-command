# 📡 SIM AT Command Tool

A web-based tool for reading, writing, and decoding SIM/USIM card files via AT commands (`AT+CRSM`, `AT+CSIM`) over USB modem port.

---

## Requirements

- [**Python 3.10+**](https://www.python.org/downloads/) — other dependencies are installed automatically on first run
- [**Samsung USB Driver**](https://developer.samsung.com/android-usb-driver) — required for Samsung devices on Windows
- **USB modem port** enabled on the device
  - Samsung: Dial `*#0808#` → USB settings → **DM + MODEM + ADB**
  - Samsung: Developer options → enable **3GPP AT**

---

## Getting Started

### macOS / Linux
```bash
chmod +x run.command
./run.command
```

### Windows
Double-click `run.bat`.

Browser opens automatically at `http://127.0.0.1:8083`.

---

## How to Use

### 1. Connect
Select the serial port and click **Connect**. Only modem ports are shown (Serial Port, Diagnostics, Bluetooth, etc. are filtered out).

> **Note:** If ADB is available, the connected device model name is shown next to the port name.

### 2. Browse & Read
The **SIM Files** panel shows 123 EFs from 3GPP TS 31.102 (USIM) and TS 102.221 (MF). Click any EF to read. Use **Search** to filter by FID or name.

> **Note:** ADF.ISIM files are currently excluded — AT+CRSM cannot distinguish ISIM FIDs from USIM.

### 3. View File Contents
**Decode / Raw** toggle switches between decoded and raw hex view. **Copy** copies to clipboard (tables as TSV for Excel).

| File Type | Decode View |
|---|---|
| PLMN (PLMNwAcT, OPLMNwAcT, etc.) | MCC / MNC / AcT table |
| Service tables (UST, IST, EST) | Service name + ON/OFF |
| ACC | Access control class + ON/OFF |
| ARR | Read/Update/Write/Activate/Deactivate conditions |
| URSP | Tree-formatted view |
| Other EFs | JSON (pySim-based decoding) |

### 4. Verify ADM
Click **VERIFY ADM** to verify ADM1–ADM4 independently. Status dots show verification state (gray/green). EF.ARR is read on connect — the **Write** button is automatically enabled/disabled based on ARR conditions, with a tooltip showing which ADM key is needed.

### 5. Write
Click **Write** to open the editor popup:

- **Hex editor** — Direct hex input
- **PLMN editor** — MCC/MNC/AcT table with Table/Hex toggle
- **Service table editor** — ON/OFF toggles with Table/Hex toggle
- **ACC editor** — Class ON/OFF toggles
- **BER-TLV editor** — Tag-based write with TLV validation (URSP etc.)

---

## Project Structure

```
run.command / run.bat    # One-click launchers
requirements.txt         # Python dependencies
src/
  app.py                 # Flask web server + API
  at_modem.py            # AT command serial communication
  sim_files.py           # 3GPP SIM file definitions
  decoder.py             # pySim-based hex decoder
  templates/
    index.html           # Web GUI (single page)
pysim/                   # pySim (Osmocom, modified)
```

---

## pySim Modifications

- `ts_102_221.py` — SecurityAttribReferenced: 6-byte long format (SEID) ARR record fix
- `ts_24_526.py` — URSP decoder (3GPP TS 24.526)
- `ts_31_102.py` — EF.URSP as BerTlvEF with `decode_tag_data`
- `commands.py` — APDU logging
- `setup.py` — Removed `smpp.twisted3` dependency (Windows fix)

---

## License

### This Project
© 2026 JUSEOK AHN <ajs3013@lguplus.co.kr>. All rights reserved.

### pySim (Third-party, modified)
The `pysim/` directory contains a modified version of [pySim by Osmocom](https://osmocom.org/projects/pysim/wiki) ([source](https://gitea.osmocom.org/sim-card/pysim)), licensed under **GPLv2**. See `pysim/COPYING`.
