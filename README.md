# 📡 SIM AT Command Tool

A web-based tool for reading, writing, and decoding SIM/USIM card files via AT commands over USB modem port.

Unlike traditional SIM card readers that require PC/SC hardware, this tool communicates directly with the SIM card through an Android device's modem port using `AT+CRSM` and `AT+CSIM` commands.

---

## Requirements

- **Python 3.10+**
- Device with USB modem port (Android DM+MODEM mode, or any device exposing AT modem via USB)
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

---

## How to Use

### 1. Connect
Select the serial port and click **Connect**.

> **Note:** If an Android device is connected via ADB, the device model name is shown next to the port name. Non-modem ports (Bluetooth, debug, etc.) are automatically filtered out.

### 2. Browse SIM Files
The **SIM Files** panel shows a 3GPP standard file tree (MF, ADF.USIM) with **123 EFs** from 3GPP TS 31.102 and TS 102.221. Click any EF to read and display its contents. Use the **Search** field in the panel header to filter by FID or file name.

- Supports **AT+CRSM** (transparent, linear fixed, cyclic) and **AT+CSIM** (BER-TLV RETRIEVE DATA / SET DATA)
- Sequential read protection prevents serial port command collision when switching files rapidly

> **Note:** ADF.ISIM files are currently excluded. AT+CRSM cannot distinguish ISIM FIDs from USIM (they overlap), and AT+CSIM SELECT by AID is not supported on some modems.

### 3. View File Contents
Select a file to view its contents in the **File Contents** panel.

- **Decode / Raw** toggle — Switch between decoded view and raw hex data
- **Copy** — Copy current view content to clipboard (tables are copied as TSV for Excel paste)
- **Write** — Modify file contents via popup editor (disabled until required ADM is verified)

Special decode views for specific file types:

| File Type | Decode View |
|---|---|
| PLMN files (PLMNwAcT, OPLMNwAcT, etc.) | Table with MCC, MNC, AcT |
| Service tables (UST, IST, EST) | Table with service name and ON/OFF status |
| ACC | Table with access control class and ON/OFF status |
| ARR | Table with Read/Update/Write/Activate/Deactivate conditions per record |
| URSP | Tree-formatted decode view |
| Other EFs | JSON decode view (pySim-based decoding) |

### 4. Verify ADM
Click **VERIFY ADM** to open the verification popup. ADM1 through ADM4 can be verified independently via AT+CSIM VERIFY PIN. Status dots next to the button show each ADM key's verification state (gray = not verified, green = verified).

- EF.ARR files (MF and ADF.USIM) are read automatically on connect
- **Write** button is enabled/disabled based on decoded ARR access conditions
- If a file requires ADM verification, a tooltip on the disabled Write button indicates which key is needed

### 5. Write
Click **Write** to modify an EF's contents. The write popup provides specialized editors depending on file type:

- **Hex editor** — Direct hex input for any writable EF
- **Table editor** — PLMN list with MCC/MNC/AcT fields, Table/Hex mode toggle
- **Service table editor** — True/False toggles per service, Table/Hex mode toggle
- **ACC editor** — True/False toggles per access class
- **BER-TLV editor** — Tag-based write with TLV validation (URSP etc.)

---

## Project Structure

```
run.command          # macOS/Linux launcher (with banner)
run.bat              # Windows launcher (with banner)
requirements.txt     # Python dependencies (flask, pyserial)
src/
  app.py             # Flask web server + AT command API
  at_modem.py        # Serial port AT command communication
  sim_files.py       # 3GPP standard SIM file definitions
  decoder.py         # pySim-based hex decoder
  templates/
    index.html       # Web GUI (single page)
pysim/               # pySim (Osmocom, modified)
```

---

## pySim Modifications

The `pysim/` directory contains a modified version of pySim with the following custom changes:

- `pySim/ts_102_221.py` — SecurityAttribReferenced: `_from_bytes` override for correct ARR record number extraction from 6-byte long format (SEID)
- `pySim/ts_24_526.py` — URSP decoder (3GPP TS 24.526)
- `pySim/ts_31_102.py` — EF.URSP changed to BerTlvEF with `decode_tag_data`
- `pySim/commands.py` — APDU logging for all commands
- `setup.py` — Removed `smpp.twisted3` dependency (Windows build fix)

---

## License

### This Project
© 2026 JUSEOK AHN <ajs3013@lguplus.co.kr>. All rights reserved.

### pySim (Third-party, modified)
The `pysim/` directory contains a modified version of pySim, an open source project by Osmocom.
- Original project: [pySim - Osmocom](https://osmocom.org/projects/pysim/wiki)
- Original source: https://gitea.osmocom.org/sim-card/pysim
- License: **GNU General Public License v2.0 (GPLv2)**

See `pysim/COPYING` for the full license text.
