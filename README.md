# 📡 SIM AT Command Tool

A web-based tool for reading, writing, and decoding SIM/USIM/ISIM card files via `AT+CSIM` (raw APDU) over USB modem port.

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
Select the serial port and click **Connect**. Only modem ports are shown.

On connect, the tool automatically:
- Reads **EF.DIR** to discover USIM/ISIM AIDs
- Scans **logical channels 0–19** (basic + extended) via STATUS command to detect USIM/ISIM channel assignments
- Falls back to **AT+CCHO/CGLA** for ISIM access on modems that don't support logical channel separation (e.g. MediaTek)
- Reads **EF.ARR** (MF, USIM, ISIM) for access rule display
- Reads **ICCID, IMSI, MSISDN** and displays them in the header bar

> If ADB is available, the connected device model name is shown next to the port name.

### 2. Browse & Read
The **SIM Files** panel shows EFs from 3GPP TS 31.102 (USIM), TS 31.103 (ISIM), and TS 102.221 (MF). Click any EF to read. Use **Search** to filter by FID or name.

File access uses `SELECT by path` (`00A40804 7FFF + FID chain`). Previously read files are cached (green dot) and shown instantly on re-click.

### 3. APDU Log
The **APDU Log** panel shows all APDU communication in real-time:
- **▶** (blue) = sent APDU with CLA/INS color coding
- **◀** (red) = received data + SW (green=9000, orange=61xx, red=error)
- Hex formatted 16 bytes per line with aligned indentation
- Step-by-step text labels: SELECT, READ BINARY, READ RECORD, RETRIEVE DATA, UPDATE BINARY, UPDATE RECORD, DELETE DATA, SET DATA, VERIFY ADM, RE-READ, etc.

### 4. View File Contents
**Decode / Raw** toggle switches between decoded and raw hex view. **Copy** copies to clipboard (tables as TSV for Excel).

| File Type | Decode View |
|---|---|
| PLMN (PLMNwAcT, OPLMNwAcT, etc.) | MCC / MNC / AcT table |
| Service tables (UST, IST, EST) | Service name + ON/OFF |
| ACC | Access control class + ON/OFF |
| ARR | Read/Update/Write/Activate/Deactivate conditions |
| URSP | Tree-formatted view |
| Other EFs | JSON (pySim-based decoding) |

### 5. Verify ADM
Click **VERIFY ADM** to verify ADM1–ADM4 independently. Status dots show verification state (gray/green). The **Write** button is automatically enabled/disabled based on ARR conditions, with a tooltip showing which ADM key is needed. If no update rule exists in ARR, write is treated as NEVER.

### 6. Write
Click **Write** to open the editor popup:

- **Hex editor** — Direct hex input
- **PLMN editor** — MCC/MNC/AcT table with Table/Hex toggle
- **Service table editor** — ON/OFF toggles with Table/Hex toggle
- **ACC editor** — Class ON/OFF toggles
- **BER-TLV editor** — Tag-based write with DELETE DATA + SET DATA (URSP etc.)

---

## Modem Compatibility

| Feature | Qualcomm | Samsung LSI | MediaTek |
|---|---|---|---|
| AT+CSIM | ✅ | ✅ | ✅ |
| Logical channel scan | ✅ | ✅ (NOTE1) | ❌ |
| AID SELECT | ✅ | ✅ | ❌ |
| AT+CCHO/CGLA | ✅ | ✅ | ✅ |
| Extended channels (4–19) | ✅ | ❌ | ❌ |
| ISIM access | Channel scan | Channel scan | AT+CCHO/CGLA fallback (NOTE2) |

> **NOTE1:** Samsung LSI STATUS (INS=F2) responds only to proprietary class (CLA bit8=1, e.g. 80/81) per ISO 7816-4 Section 5.4.1. Standard interindustry class (CLA bit8=0, e.g. 00/01) returns 6E00 (class not supported). This does not affect functionality since the tool uses proprietary CLA for channel scanning.

> **NOTE2:** AT+CSIM (3GPP TS 27.007 Section 8.17) sends a raw APDU directly to the UICC — the app must manage logical channels via the CLA byte. AT+CCHO (Section 8.45) opens a logical channel by AID and returns a session ID, then AT+CGLA (Section 8.46) sends APDUs on that session — the modem manages channel assignment internally. This tool uses AT+CSIM with channel scan as the primary method, and falls back to AT+CCHO/CGLA only for ISIM access on modems (e.g. MediaTek) where logical channel scan is not supported.

---

## Project Structure

```
run.command / run.bat    # One-click launchers
requirements.txt         # Python dependencies
src/
  app.py                 # Flask web server + API
  at_modem.py            # AT+CSIM serial communication
  sim_files.py           # 3GPP SIM file definitions (MF/USIM/ISIM)
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
