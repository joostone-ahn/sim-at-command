#!/usr/bin/env python3
"""AT Command based SIM communication module."""

import serial
import serial.tools.list_ports
import time
import re
import logging

logger = logging.getLogger(__name__)


class ATModem:
    """AT command communication via serial port."""

    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None
        self.last_cmd = ''
        self.last_resp = ''
        self.apdu_log: list[dict] = []  # [{dir:'tx'/'rx', data:'hex', sw:'', ts:float}]
        self.apdu_log_max = 500

    def connect(self, port: str = None) -> dict:
        """Connect to serial port and verify AT response."""
        if port:
            self.port = port
        if not self.port:
            raise ValueError("No port specified")
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(0.3)
            self.ser.reset_input_buffer()
            # Verify basic AT response
            resp = self._send('AT')
            if 'OK' not in resp:
                raise RuntimeError(f"No AT response: {resp}")
            return {'success': True}
        except serial.SerialException as e:
            return {'success': False, 'error': f"Port connection failed: {e}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    @property
    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def _log_apdu(self, direction: str, apdu: str, sw: str = ''):
        """Add APDU to log buffer. direction: 'tx', 'rx', or 'msg'."""
        self.apdu_log.append({
            'dir': direction, 'data': apdu.upper() if direction != 'msg' else apdu, 'sw': sw.upper() if sw else '',
            'ts': time.time()
        })
        if len(self.apdu_log) > self.apdu_log_max:
            self.apdu_log = self.apdu_log[-self.apdu_log_max:]

    def _send(self, cmd: str, timeout: float = None) -> str:
        """Send AT command and receive response."""
        if not self.is_connected:
            raise RuntimeError("Modem not connected")
        t = timeout or self.timeout
        self.ser.reset_input_buffer()
        self.ser.write((cmd + '\r\n').encode())
        self.last_cmd = cmd
        time.sleep(0.1)
        deadline = time.time() + t
        buf = b''
        while time.time() < deadline:
            chunk = self.ser.read(self.ser.in_waiting or 1)
            if chunk:
                buf += chunk
                text = buf.decode(errors='replace')
                if 'OK' in text or 'ERROR' in text or '+CME ERROR' in text:
                    break
            else:
                time.sleep(0.05)
        resp = buf.decode(errors='replace')
        self.last_resp = resp
        logger.info("[AT] -> %s", cmd)
        for line in resp.strip().split('\n'):
            line = line.strip()
            if line and line != cmd:
                logger.info("[AT] <- %s", line)
        return resp

    def at_check(self) -> dict:
        """Verify AT, read EF.DIR for AIDs, scan channels, CCHO fallback."""
        try:
            resp = self._send('AT')
            if 'OK' not in resp:
                return {'success': False, 'error': 'No AT response'}
            # 1. Read EF.DIR first to get full AIDs
            aids = self.read_ef_dir()
            # 2. Scan channels to find USIM/ISIM
            channels = self.scan_channels(aids)
            return {'success': True, 'csim': True, 'aids': aids, 'channels': channels}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def csim_send(self, apdu_hex: str) -> dict:
        """AT+CSIM — send raw APDU. Auto-handles SW 61xx (GET RESPONSE).
        Skips GET RESPONSE for SELECT (INS=A4) to preserve card context."""
        length = len(apdu_hex)
        cmd = f'AT+CSIM={length},"{apdu_hex}"'
        self._log_apdu('tx', apdu_hex)
        resp = self._send(cmd)
        result = self._parse_csim(resp)
        sw = result.get('sw', '')
        # Auto GET RESPONSE for SW 61xx — but NOT for SELECT commands
        ins = apdu_hex[2:4].upper() if len(apdu_hex) >= 4 else ''
        if sw.startswith('61') and ins != 'A4':
            le = sw[2:4]
            orig_cla = int(apdu_hex[:2], 16)
            if orig_cla & 0x40:
                get_resp_cla = 0x40 | (orig_cla & 0x0F)
            else:
                get_resp_cla = 0x00 | (orig_cla & 0x03)
            get_resp = f'{get_resp_cla:02X}C00000{le}'
            resp2 = self._send(f'AT+CSIM={len(get_resp)},"{get_resp}"')
            result2 = self._parse_csim(resp2)
            result2['data'] = result.get('data', '') + result2.get('data', '')
            self._log_apdu('rx', result2.get('data', ''), result2.get('sw', ''))
            return result2
        # Treat 61xx as success for SELECT (FCP available but not fetched)
        if sw.startswith('61') and ins == 'A4':
            result['success'] = True
        self._log_apdu('rx', result.get('data', ''), sw)
        return result
        # Treat 61xx as success for SELECT (FCP available but not fetched)
        if sw.startswith('61') and ins == 'A4':
            result['success'] = True
        return result

    def scan_channels(self, aids: list[str]) -> dict:
        """Scan logical channels 0~19 with STATUS command to find USIM/ISIM.
        Channels 0~3: basic (CLA = 0x00|ch), Channels 4~19: extended (CLA = 0x40|(ch-4))
        Returns {'usim': {'lchan': N, 'aid': '...'}, 'isim': {'lchan': N, 'aid': '...'}}"""
        result = {}
        usim_prefix = 'A0000000871002'
        isim_prefix = 'A0000000871004'
        fail_count = 0
        for ch in range(20):
            cla = _cla_for_lchan(ch, proprietary=True)
            r = self.csim_send(f'{cla:02X}F2000000')
            sw = r.get('sw', '')
            data = r.get('data', '')
            if not (sw.startswith('90') or sw.startswith('61')) or not data:
                fail_count += 1
                # 6E00 = class not supported → extended channels not available
                if ch > 3 and (fail_count >= 2 or sw == '6E00'):
                    break
                continue
            fail_count = 0
            aid = _extract_aid_from_fcp(data)
            if aid:
                aid_upper = aid.upper()
                if aid_upper.startswith(usim_prefix) and 'usim' not in result:
                    result['usim'] = {'lchan': ch, 'aid': aid_upper}
                    logger.info("[SCAN] Channel %d: USIM (%s)", ch, aid_upper)
                elif aid_upper.startswith(isim_prefix) and 'isim' not in result:
                    result['isim'] = {'lchan': ch, 'aid': aid_upper}
                    logger.info("[SCAN] Channel %d: ISIM (%s)", ch, aid_upper)
            else:
                # Channel responds but no AID (e.g. MF selected) — assume USIM on channel 0
                if ch == 0 and 'usim' not in result:
                    result['usim'] = {'lchan': 0, 'aid': ''}
                    logger.info("[SCAN] Channel 0: USIM (no AID, assumed)")
            if 'usim' in result and 'isim' in result:
                break
        # Fallback: if no USIM found, default to channel 0
        if 'usim' not in result:
            result['usim'] = {'lchan': 0, 'aid': ''}
            logger.info("[SCAN] Defaulting USIM to channel 0")
        return result

    def csim_read_binary(self, length: int, lchan: int = 0) -> dict:
        """READ BINARY via AT+CSIM on given logical channel."""
        cla = _cla_for_lchan(lchan)
        if length <= 255:
            apdu = f'{cla:02X}B00000{length:02X}'
            r = self.csim_send(apdu)
            # Trim response to requested length (some modems return more)
            data = r.get('data', '')
            if len(data) > length * 2:
                r['data'] = data[:length * 2]
                # Update last log entry with trimmed data
                if self.apdu_log and self.apdu_log[-1]['dir'] == 'rx':
                    self.apdu_log[-1]['data'] = r['data']
            return r
        # Split into chunks
        data = ''
        offset = 0
        sw = ''
        while offset < length:
            chunk_len = min(255, length - offset)
            p1 = (offset >> 8) & 0xFF
            p2 = offset & 0xFF
            apdu = f'{cla:02X}B0{p1:02X}{p2:02X}{chunk_len:02X}'
            r = self.csim_send(apdu)
            sw = r.get('sw', '')
            if sw.startswith('90'):
                chunk_data = r.get('data', '')
                if len(chunk_data) > chunk_len * 2:
                    chunk_data = chunk_data[:chunk_len * 2]
                data += chunk_data
                offset += chunk_len
            else:
                break
        return {'success': sw.startswith('90'), 'data': data, 'sw': sw}

    def csim_read_record(self, rec_no: int, rec_len: int, lchan: int = 0) -> dict:
        """READ RECORD via AT+CSIM on given logical channel."""
        cla = _cla_for_lchan(lchan)
        apdu = f'{cla:02X}B2{rec_no:02X}04{rec_len:02X}'
        r = self.csim_send(apdu)
        data = r.get('data', '')
        if len(data) > rec_len * 2:
            r['data'] = data[:rec_len * 2]
            if self.apdu_log and self.apdu_log[-1]['dir'] == 'rx':
                self.apdu_log[-1]['data'] = r['data']
        return r

    def _get_response(self, sw: str, lchan: int = 0) -> dict:
        """Send GET RESPONSE for 61xx SW. Returns parsed result with FCP data."""
        le = sw[2:4]
        cla = f'{_cla_for_lchan(lchan):02X}'
        return self.csim_send(f'{cla}C00000{le}')

    # ── AT+CCHO/CGLA session-based access (fallback for modems without lchan support) ──

    def ccho_open(self, aid_hex: str) -> int | None:
        """Open logical channel by AID via AT+CCHO. Returns session ID or None."""
        cmd = f'AT+CCHO="{aid_hex.upper()}"'
        resp = self._send(cmd)
        if 'ERROR' in resp:
            return None
        for line in resp.strip().split('\n'):
            line = line.strip()
            if line.isdigit():
                return int(line)
        return None

    def ccho_close(self, session_id: int) -> bool:
        """Close logical channel via AT+CCHC."""
        resp = self._send(f'AT+CCHC={session_id}')
        return 'OK' in resp

    def cgla_send(self, session_id: int, apdu_hex: str) -> dict:
        """Send APDU via AT+CGLA on a CCHO session. Returns same format as csim_send."""
        length = len(apdu_hex)
        cmd = f'AT+CGLA={session_id},{length},"{apdu_hex}"'
        self._log_apdu('tx', apdu_hex)
        resp = self._send(cmd)
        result = self._parse_cgla(resp)
        self._log_apdu('rx', result.get('data', ''), result.get('sw', ''))
        return result

    def _parse_cgla(self, resp: str) -> dict:
        """Parse AT+CGLA response (same format as +CSIM)."""
        m = re.search(r'\+CGLA:\s*\d+,\s*"([^"]*)"', resp)
        if not m:
            if 'ERROR' in resp:
                return {'success': False, 'data': '', 'error': resp.strip()}
            return {'success': False, 'data': '',
                    'error': f'Parse failed: {resp.strip()}'}
        data = m.group(1).upper()
        sw = data[-4:] if len(data) >= 4 else ''
        payload = data[:-4] if len(data) > 4 else ''
        success = sw == '9000' or sw.startswith('61') or sw.startswith('9F')
        result = {'success': success, 'sw': sw, 'data': payload}
        if not success:
            result['error'] = f'SW={sw}'
        return result

    def read_ef_dir(self) -> list[str]:
        """Read EF.DIR (2F00) via AT+CSIM and extract AIDs from all records.
        Returns list of AID hex strings."""
        aids = []
        # SELECT MF
        r = self.csim_send('00A40004023F00')
        sw = r.get('sw', '')
        if not (sw.startswith('90') or sw.startswith('61')):
            return aids
        # SELECT EF.DIR (2F00)
        r = self.csim_send('00A40004022F00')
        sw = r.get('sw', '')
        if not (sw.startswith('90') or sw.startswith('61')):
            return aids
        # GET RESPONSE for FCP if 61xx
        fcp_data = r.get('data', '')
        if sw.startswith('61') and not fcp_data:
            r2 = self._get_response(sw)
            fcp_data = r2.get('data', '')
        if not fcp_data:
            return aids
        meta = parse_fcp(fcp_data)
        record_len = meta.get('record_len', 0)
        num_records = meta.get('num_records', 0)
        if not record_len or not num_records:
            return aids
        for i in range(1, num_records + 1):
            rr = self.csim_send(f'00B2{i:02X}04{record_len:02X}')
            if not rr.get('sw', '').startswith('90') or not rr.get('data'):
                continue
            aid = _parse_dir_record(rr['data'])
            if aid and aid not in aids:
                aids.append(aid)
        return aids

    def verify_adm(self, adm_hex: str, key_ref: str = '0A') -> dict:
        """ADM verification — VERIFY PIN via AT+CSIM."""
        # VERIFY: 00 20 00 <key_ref> 08 <adm_8bytes>
        adm_padded = adm_hex.ljust(16, 'F')[:16]
        apdu = f'002000{key_ref}08{adm_padded}'
        return self.csim_send(apdu)

    def _parse_csim(self, resp: str) -> dict:
        """Parse AT+CSIM response."""
        m = re.search(r'\+CSIM:\s*\d+,\s*"([^"]*)"', resp)
        if not m:
            if 'ERROR' in resp:
                return {'success': False, 'data': '', 'error': resp.strip()}
            return {'success': False, 'data': '',
                    'error': f'Parse failed: {resp.strip()}'}
        data = m.group(1).upper()
        sw = data[-4:] if len(data) >= 4 else ''
        payload = data[:-4] if len(data) > 4 else ''
        success = sw == '9000' or sw.startswith('61') or sw.startswith('9F')
        result = {'success': success, 'sw': sw, 'data': payload}
        if not success:
            result['error'] = f'SW={sw}'
        return result

    @staticmethod
    def list_ports() -> list[dict]:
        """List available serial ports (modem ports only)."""
        EXCLUDE = ('bluetooth', 'debug', 'wlan')
        ports = []
        for p in serial.tools.list_ports.comports():
            dev_lower = p.device.lower()
            desc_lower = (p.description or '').lower()
            # Skip known non-modem ports
            if any(x in dev_lower for x in EXCLUDE):
                continue
            # Include if USB VID present OR device name contains 'usbmodem'
            if p.vid is None and 'usbmodem' not in dev_lower:
                continue
            # On Windows: only show modem ports (filter out Serial Port, Diagnostics, etc.)
            if p.vid and 'modem' not in desc_lower and 'usbmodem' not in dev_lower:
                continue
            ports.append({
                'device': p.device,
                'description': p.description,
                'hwid': p.hwid,
                'manufacturer': p.manufacturer or '',
                'serial_number': p.serial_number or '',
            })
        return ports


def _cla_for_lchan(lchan: int, proprietary: bool = False) -> int:
    """Build CLA byte for a given logical channel number.
    Channels 0~3: basic (0x00|ch or 0x80|ch for proprietary)
    Channels 4~19: extended (0x40|(ch-4) or 0xC0|(ch-4) for proprietary)"""
    if lchan <= 3:
        return (0x80 if proprietary else 0x00) | (lchan & 0x03)
    else:
        return (0xC0 if proprietary else 0x40) | ((lchan - 4) & 0x0F)


def _extract_aid_from_fcp(hex_data: str) -> str | None:
    """Extract AID (tag 84) from FCP TLV data."""
    if not hex_data or len(hex_data) < 4:
        return None
    try:
        b = bytes.fromhex(hex_data)
        # Skip FCP template tag (62) + length
        if b[0] != 0x62:
            return None
        i = 2
        if b[1] > 0x80:
            i = 3
        end = len(b)
        while i < end - 1:
            tag = b[i]
            i += 1
            length = b[i]
            i += 1
            if tag == 0x84:  # AID
                return b[i:i+length].hex().upper()
            i += length
    except (ValueError, IndexError):
        pass
    return None


def _parse_dir_record(hex_data: str) -> str | None:
    """Parse a single EF.DIR record and extract AID.
    Record TLV: 61(app template) containing 4F(AID)."""
    if not hex_data or len(hex_data) < 8:
        return None
    data = hex_data.upper().replace(' ', '')
    # Must start with tag 61
    if not data.startswith('61'):
        return None
    try:
        i = 2
        tpl_len = int(data[i:i+2], 16)
        i += 2
        end = i + tpl_len * 2
        while i < end and i < len(data) - 2:
            tag = data[i:i+2]
            i += 2
            length = int(data[i:i+2], 16)
            i += 2
            value = data[i:i+length*2]
            i += length * 2
            if tag == '4F':
                return value
    except (ValueError, IndexError):
        pass
    return None


def parse_fcp(hex_data: str) -> dict:
    """Parse GET RESPONSE(192) result into file metadata.
    Supports 3GPP TS 51.011 / TS 102.221 formats."""
    if not hex_data or len(hex_data) < 4:
        return {}
    b = bytes.fromhex(hex_data)
    result = {}
    # TS 51.011 format (length >= 14)
    if len(b) >= 14 and b[6] in (0x01, 0x02, 0x04):
        result['file_size'] = (b[2] << 8) | b[3]
        file_type_byte = b[6]
        if file_type_byte == 0x04:
            result['file_type'] = 'DF'
        elif file_type_byte == 0x01:
            result['file_type'] = 'transparent'
        elif file_type_byte == 0x02:
            result['file_type'] = 'linear_fixed'
        if file_type_byte in (0x01, 0x02) and len(b) >= 15:
            structure = b[13]
            if structure == 0x00:
                result['structure'] = 'transparent'
            elif structure == 0x01:
                result['structure'] = 'linear_fixed'
                if len(b) >= 16:
                    result['record_len'] = b[14]
                    if result['record_len'] > 0:
                        result['num_records'] = result['file_size'] // result['record_len']
            elif structure == 0x03:
                result['structure'] = 'cyclic'
                if len(b) >= 16:
                    result['record_len'] = b[14]
                    if result['record_len'] > 0:
                        result['num_records'] = result['file_size'] // result['record_len']
    # TLV format (TS 102.221) — 62 xx ...
    elif b[0] == 0x62:
        result = _parse_fcp_tlv(b[2:2+b[1]] if len(b) > 2 else b[2:])
    return result


def _parse_fcp_tlv(data: bytes) -> dict:
    """Parse FCP TLV (TS 102.221)."""
    result = {}
    i = 0
    while i < len(data) - 1:
        tag = data[i]
        i += 1
        if i >= len(data):
            break
        length = data[i]
        i += 1
        value = data[i:i+length]
        i += length
        if tag == 0x80:  # File size
            result['file_size'] = int.from_bytes(value, 'big')
        elif tag == 0x82:  # File descriptor
            if len(value) >= 2:
                fd_byte = value[0]
                if fd_byte & 0x38 == 0x38:
                    result['structure'] = 'ber_tlv'
                    result['file_type'] = 'EF'
                elif fd_byte & 0x07 == 0x01:
                    result['structure'] = 'transparent'
                    result['file_type'] = 'EF'
                elif fd_byte & 0x07 == 0x02:
                    result['structure'] = 'linear_fixed'
                    result['file_type'] = 'EF'
                    if len(value) >= 5:
                        result['record_len'] = (value[2] << 8) | value[3]
                        result['num_records'] = value[4]
                elif fd_byte & 0x07 == 0x06:
                    result['structure'] = 'cyclic'
                    result['file_type'] = 'EF'
                    if len(value) >= 5:
                        result['record_len'] = (value[2] << 8) | value[3]
                        result['num_records'] = value[4]
                elif fd_byte & 0x07 == 0x00 and fd_byte & 0x38 == 0x00:
                    result['file_type'] = 'DF'
        elif tag == 0x83:  # File ID
            result['file_id'] = value.hex()
        elif tag == 0x8A:  # Life cycle status
            lcsi_byte = value[0] if value else 0
            result['lcsi'] = lcsi_byte
            if lcsi_byte == 0x00:
                result['lifecycle'] = 'No info'
            elif lcsi_byte == 0x01:
                result['lifecycle'] = 'Creation'
            elif lcsi_byte == 0x03:
                result['lifecycle'] = 'Initialization'
            elif lcsi_byte in (0x05, 0x07):
                result['lifecycle'] = 'Activated'
            elif lcsi_byte in (0x04, 0x06):
                result['lifecycle'] = 'Deactivated'
            elif lcsi_byte in (0x0C, 0x0D, 0x0E, 0x0F):
                result['lifecycle'] = 'Terminated'
            else:
                result['lifecycle'] = f'Unknown (0x{lcsi_byte:02X})'
        elif tag == 0x8B:  # Security attrib referenced
            # Short format (3 bytes): EF_ARR_FID(2) + record_nr(1)
            # Long format (6 bytes): EF_ARR_FID(2) + SEID(1) + record_nr(1) + SEID_rec(1) + pad(1)
            if len(value) >= 6:
                arr_fid = f'{value[0]:02X}{value[1]:02X}'
                arr_rec = value[3]
                result['security'] = f'EF.ARR:{arr_fid} rec#{arr_rec}'
                result['security_raw'] = value.hex()
                result['arr_record_nr'] = arr_rec
            elif len(value) >= 3:
                arr_fid = f'{value[0]:02X}{value[1]:02X}'
                arr_rec = value[2]
                result['security'] = f'EF.ARR:{arr_fid} rec#{arr_rec}'
                result['security_raw'] = value.hex()
                result['arr_record_nr'] = arr_rec
            else:
                result['security'] = value.hex()
                result['security_raw'] = value.hex()
        elif tag == 0x8C:  # Security attrib compact
            result['security'] = _parse_compact_security(value)
            result['security_raw'] = value.hex()
        elif tag == 0xAB:  # Security attrib expanded
            result['security'] = value.hex()
            result['security_raw'] = value.hex()
    return result


def _parse_compact_security(value: bytes) -> str:
    """Parse compact security attribute (tag 8C)."""
    if not value:
        return ''
    am = value[0]  # access mode byte
    conditions = []
    labels = []
    if am & 0x80:
        labels.append('DELETE')
    if am & 0x40:
        labels.append('TERMINATE')
    if am & 0x20:
        labels.append('ACTIVATE')
    if am & 0x10:
        labels.append('DEACTIVATE')
    if am & 0x08:
        labels.append('WRITE/UPDATE')
    if am & 0x04:
        labels.append('READ')
    if am & 0x02:
        labels.append('INCREASE')

    sc_names = {0x00: 'Always', 0x01: 'PIN1', 0x02: 'PIN2',
                0x0A: 'ADM1', 0x0B: 'ADM2', 0xFF: 'Never'}
    idx = 1
    for label in labels:
        if idx < len(value):
            sc = value[idx]
            sc_str = sc_names.get(sc, f'0x{sc:02X}')
            conditions.append(f'{label}={sc_str}')
            idx += 1

    return ', '.join(conditions) if conditions else value.hex()
