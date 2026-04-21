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
        """Verify AT basic operation + CRSM support."""
        try:
            # Basic AT check
            resp = self._send('AT')
            if 'OK' not in resp:
                return {'success': False, 'error': 'No AT response'}
            # CRSM support check — try reading EF.ICCID(2FE2)
            resp2 = self._send('AT+CRSM=176,12258,0,0,10')
            if '+CRSM:' in resp2:
                m = re.search(r'\+CRSM:\s*(\d+),\s*(\d+)', resp2)
                if m:
                    sw1, sw2 = int(m.group(1)), int(m.group(2))
                    if sw1 == 144:
                        return {'success': True, 'crsm': True}
                    else:
                        return {'success': True, 'crsm': True,
                                'warning': f'SW={sw1},{sw2}'}
                return {'success': True, 'crsm': True}
            else:
                return {'success': True, 'crsm': False,
                        'warning': 'AT+CRSM not supported'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def crsm_read_binary(self, file_id: int, length: int = 0) -> dict:
        """AT+CRSM READ BINARY (INS=176). Auto-splits for large files."""
        if length <= 255 or length == 0:
            cmd = f'AT+CRSM=176,{file_id},0,0,{length}'
            resp = self._send(cmd)
            return self._parse_crsm(resp)
        # Split into chunks of 255 bytes
        data = ''
        offset = 0
        while offset < length:
            chunk_len = min(255, length - offset)
            p1 = (offset >> 8) & 0xFF
            p2 = offset & 0xFF
            cmd = f'AT+CRSM=176,{file_id},{p1},{p2},{chunk_len}'
            resp = self._send(cmd)
            r = self._parse_crsm(resp)
            if not r['success']:
                if data:
                    # Return what we got so far
                    return {'success': True, 'sw1': 144, 'sw2': 0, 'data': data}
                return r
            data += r['data']
            offset += chunk_len
        return {'success': True, 'sw1': 144, 'sw2': 0, 'data': data}

    def crsm_read_record(self, file_id: int, record: int, length: int) -> dict:
        """AT+CRSM READ RECORD (INS=178)."""
        cmd = f'AT+CRSM=178,{file_id},{record},4,{length}'
        resp = self._send(cmd)
        return self._parse_crsm(resp)

    def crsm_get_response(self, file_id: int) -> dict:
        """AT+CRSM GET RESPONSE (INS=192) — file metadata."""
        cmd = f'AT+CRSM=192,{file_id},0,0,0'
        resp = self._send(cmd)
        return self._parse_crsm(resp)

    def crsm_update_binary(self, file_id: int, data: str) -> dict:
        """AT+CRSM UPDATE BINARY (INS=214)."""
        length = len(data) // 2
        cmd = f'AT+CRSM=214,{file_id},0,0,{length},"{data}"'
        resp = self._send(cmd)
        return self._parse_crsm(resp)

    def crsm_update_record(self, file_id: int, record: int,
                           length: int, data: str) -> dict:
        """AT+CRSM UPDATE RECORD (INS=220)."""
        cmd = f'AT+CRSM=220,{file_id},{record},4,{length},"{data}"'
        resp = self._send(cmd)
        return self._parse_crsm(resp)

    def csim_send(self, apdu_hex: str) -> dict:
        """AT+CSIM — send raw APDU."""
        length = len(apdu_hex)
        cmd = f'AT+CSIM={length},"{apdu_hex}"'
        resp = self._send(cmd)
        return self._parse_csim(resp)

    def verify_adm(self, adm_hex: str, key_ref: str = '0A') -> dict:
        """ADM verification — VERIFY PIN via AT+CSIM."""
        # VERIFY: 00 20 00 <key_ref> 08 <adm_8bytes>
        adm_padded = adm_hex.ljust(16, 'F')[:16]
        apdu = f'002000{key_ref}08{adm_padded}'
        return self.csim_send(apdu)

    def _parse_crsm(self, resp: str) -> dict:
        """Parse AT+CRSM response."""
        m = re.search(r'\+CRSM:\s*(\d+),\s*(\d+)(?:,\s*"([^"]*)")?', resp)
        if not m:
            if 'ERROR' in resp:
                return {'success': False, 'sw1': 0, 'sw2': 0, 'data': '',
                        'error': resp.strip()}
            return {'success': False, 'sw1': 0, 'sw2': 0, 'data': '',
                    'error': f'Parse failed: {resp.strip()}'}
        sw1, sw2 = int(m.group(1)), int(m.group(2))
        data = m.group(3) or ''
        success = sw1 == 144 and sw2 == 0
        result = {'success': success, 'sw1': sw1, 'sw2': sw2, 'data': data}
        if not success:
            result['error'] = f'SW={sw1},{sw2} ({sw1:02X}{sw2:02X})'
        return result

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
        success = sw == '9000'
        result = {'success': success, 'sw': sw, 'data': payload}
        if not success:
            result['error'] = f'SW={sw}'
        return result

    @staticmethod
    def list_ports() -> list[dict]:
        """List available serial ports (USB/modem devices only, excludes Bluetooth/debug)."""
        EXCLUDE = ('bluetooth', 'debug', 'wlan')
        ports = []
        for p in serial.tools.list_ports.comports():
            dev_lower = p.device.lower()
            # Skip known non-modem ports
            if any(x in dev_lower for x in EXCLUDE):
                continue
            # Include if USB VID present OR device name contains 'usbmodem'
            if p.vid is None and 'usbmodem' not in dev_lower:
                continue
            ports.append({
                'device': p.device,
                'description': p.description,
                'hwid': p.hwid,
                'manufacturer': p.manufacturer or '',
                'serial_number': p.serial_number or '',
            })
        return ports


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
