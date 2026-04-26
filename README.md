# 📡 SIM AT Command Tool

A web-based tool for reading, writing, and decoding SIM/USIM/ISIM card files via `AT+CSIM` (raw APDU) over USB modem port.

---

## Modem Compatibility

| Platform | Chipset | AT+CSIM | Logical<br>channel<br>scan (NOTE1) | AID SELECT | AT+CCHO<br>/CGLA | ISIM<br>access | RETRIEVE<br>DATA |
|---|---|---|---|---|---|---|---|
| Android | **Qualcomm** | ✅ | ✅ | ✅ | ✅ | Scanned<br>channel (NOTE3) | ⚠️ (NOTE5) |
| Android | **Samsung LSI** | ✅ | ✅<br>(NOTE2) | ✅ | ✅ | Scanned<br>channel (NOTE3) | ✅ |
| Android | **MediaTek** | ✅ | ❌ | ❌ | ✅ | AT+CCHO<br>/CGLA (NOTE4) | ✅ |
| iOS | **Qualcomm** | ✅ | ✅ | ✅ | ✅ | Scanned<br>channel (NOTE3) | ⚠️ (NOTE5) |

> **NOTE1:** The tool sends STATUS (INS=F2) with proprietary CLA on each logical channel (0–19) via AT+CSIM and extracts the AID (tag 84) from the FCP response. If the AID starts with the USIM AID prefix (A0000000871002) or ISIM AID prefix (A0000000871004), that channel number is recorded and used for all subsequent file access on that application.

> **NOTE2:** Samsung LSI STATUS responds only to proprietary class (CLA bit8=1, e.g. 80/81) per ISO 7816-4 Section 5.4.1. Standard interindustry class (CLA bit8=0, e.g. 00/01) returns 6E00.

> **NOTE3:** ISIM files are accessed by setting the CLA byte to the scanned ISIM logical channel number (e.g. CLA=01 for channel 1) in AT+CSIM APDUs. No separate session management is needed.

> **NOTE4:** When logical channel scan is not supported, the tool falls back to AT+CCHO (3GPP TS 27.007 Section 8.45) to open a session by ISIM AID, then sends APDUs via AT+CGLA (Section 8.46) on that session. The modem manages channel assignment internally.

> **NOTE5:** Qualcomm modem processes AT+CSIM through MMGSDI/CRSM internally, which may block RETRIEVE DATA (INS=CB) with SW=6981 (command incompatible with file structure). The tool performs an AT+CFUN power cycle on every connect to reset the modem internal state, which has been verified to resolve the issue.

---

## Device Setup

### Android (Samsung)

1. **USB Driver** (Windows only): Install [Samsung Android USB Driver](https://developer.samsung.com/android-usb-driver)
2. **Developer mode**: Settings → About phone → Software information → tap **Build number** 5 times
3. **Developer options**:
   - Enable **USB debugging** → connect USB → allow RSA key
   - Enable **3GPP AT commands** (required for AT+CSIM)
4. **USB mode**: Dial `*#0808#` → select **DM + MODEM + ADB**

### iOS (iPhone)

- Carrier Settings → Baseband Manager → Logging Settings → Mode: **Passive, External Hardware (QXDM)**

> iPhone must be upgraded to a carrier software version to enable modem port access. Also, AT+CSIM is available on Windows only — Qualcomm USB driver is not available for macOS.

---

## Getting Started

**Requirements:** [Python 3.10+](https://www.python.org/downloads/) — other dependencies are installed automatically on first run.

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

> If ADB is available, the connected device model name is shown next to the port name.

On connect, the tool automatically:
- Performs **AT+CFUN power cycle** to reset modem internal state
- Scans logical channels to identify which channel is assigned to USIM and ISIM
- If ISIM is not found via channel scan (e.g. MediaTek), opens ISIM via AT+CCHO/CGLA
- Reads **EF.ARR** (MF, USIM, ISIM) to display access rules for each EF — shows which ADM key must be verified before writing
- Reads **ICCID, IMSI, MSISDN** and displays them in the header bar

### 2. Browse & Read
The **SIM Files** panel shows EFs from 3GPP TS 31.102 (USIM), TS 31.103 (ISIM), and TS 102.221 (MF).

- Click any EF to read
- Use **Search** to filter by FID or name
- Each file has a status dot indicating read state:
  - 🟢 green = read successfully (re-click shows cached value)
  - 🔴 red = read failed (re-click retries)

### 3. APDU Log
The **APDU Log** panel shows all APDU communication in real-time:
- **>>** (blue) = sent APDU with CLA/INS color coding
- **<<** (red) = received data + SW (green=9000, red=error)
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
Click **VERIFY ADM** to verify ADM1–ADM4 independently.

- Status dots show verification state (gray = not verified, green = verified)
- **Write** button is automatically enabled/disabled based on ARR conditions
- Tooltip shows which ADM key is needed for update

### 6. Write
Click **Write** to open the editor popup:

- **Hex editor** — Direct hex input
- **PLMN editor** — MCC/MNC/AcT table with Table/Hex toggle
- **Service table editor** — ON/OFF toggles with Table/Hex toggle
- **ACC editor** — Class ON/OFF toggles
- **BER-TLV editor** — Tag-based write with DELETE DATA + SET DATA (URSP etc.)

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
