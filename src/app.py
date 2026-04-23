#!/usr/bin/env python3
"""SIM AT Command Tool — Flask Web Application."""

import json
import sys
import logging
import platform
from pathlib import Path
from flask import Flask, render_template, request, jsonify

sys.path.insert(0, str(Path(__file__).parent))
from at_modem import ATModem, parse_fcp, _cla_for_lchan
from sim_files import build_file_tree, get_file_by_path
from decoder import decode_ef, decode_ef_records

app = Flask(__name__)
app.json.sort_keys = False
logger = logging.getLogger(__name__)

modem = ATModem()
usim_aid = ''
isim_aid = ''
usim_lchan = 0    # Logical channel for USIM (from STATUS scan)
isim_lchan = -1   # Logical channel for ISIM (-1 = not available via scan)
isim_ccho = False  # True if ISIM uses AT+CCHO/CGLA fallback


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ports', methods=['GET'])
def list_ports():
    """List available serial ports with ADB device model info."""
    ports = ATModem.list_ports()
    adb_models = _get_adb_models()
    return jsonify({'ports': ports, 'adb_models': adb_models})


def _get_adb_models() -> dict:
    """Get connected Android device models via adb. Returns {serial: model_name}."""
    import subprocess
    models = {}
    try:
        r = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, timeout=5)
        for line in r.stdout.strip().split('\n')[1:]:
            if 'model:' not in line:
                continue
            serial = line.split()[0]
            for part in line.split():
                if part.startswith('model:'):
                    models[serial] = part.split(':', 1)[1].replace('_', ' ')
    except Exception:
        pass
    return models


@app.route('/connect', methods=['POST'])
def connect():
    """Connect to serial port."""
    port = request.json.get('port', '')
    if not port:
        return jsonify({'success': False, 'error': 'Please select a port'})
    result = modem.connect(port)
    return jsonify(result)


@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from modem."""
    global usim_aid, isim_aid, usim_lchan, isim_lchan, isim_ccho
    modem.disconnect()
    usim_aid = ''
    isim_aid = ''
    usim_lchan = 0
    isim_lchan = -1
    isim_ccho = False
    return jsonify({'success': True})


@app.route('/at_check', methods=['POST'])
def at_check():
    """Verify AT functionality, discover AIDs, and scan logical channels."""
    global usim_aid, isim_aid, usim_lchan, isim_lchan, isim_ccho
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})
    result = modem.at_check()
    usim_aid = ''
    isim_aid = ''
    usim_lchan = 0
    isim_lchan = -1
    isim_ccho = False
    for aid in result.get('aids', []):
        aid_upper = aid.upper()
        if aid_upper.startswith('A0000000871002'):
            usim_aid = aid_upper
        elif aid_upper.startswith('A0000000871004'):
            isim_aid = aid_upper
    channels = result.get('channels', {})
    if 'usim' in channels:
        usim_lchan = channels['usim']['lchan']
        if channels['usim']['aid']:
            usim_aid = channels['usim']['aid']
    if 'isim' in channels:
        isim_lchan = channels['isim']['lchan']
        isim_aid = channels['isim']['aid']
    # If ISIM not found via scan but AID exists in EF.DIR, try AT+CCHO fallback
    if isim_lchan < 0 and isim_aid:
        session = modem.ccho_open(isim_aid)
        if session is not None:
            isim_ccho = True
            isim_lchan = session  # Store session ID (used differently from lchan)
            logger.info("[AID] ISIM via AT+CCHO session %d", session)
            modem.ccho_close(session)  # Close for now, will reopen per-read
    logger.info("[AID] USIM=%s (ch%d), ISIM=%s (ch%d)",
                usim_aid or '(none)', usim_lchan,
                isim_aid or '(none)', isim_lchan)
    result['usim_aid'] = usim_aid
    result['isim_aid'] = isim_aid
    result['usim_lchan'] = usim_lchan
    result['isim_lchan'] = isim_lchan
    return jsonify(result)


@app.route('/read_info', methods=['POST'])
def read_info():
    """Read ICCID, IMSI and MSISDN for header display."""
    if not modem.is_connected:
        return jsonify({'iccid': '', 'imsi': '', 'msisdn': ''})
    iccid = ''
    imsi = ''
    msisdn = ''
    iccid_hex = ''
    imsi_hex = ''
    msisdn_hex = ''
    iccid_meta = {}
    imsi_meta = {}
    msisdn_meta = {}
    msisdn_reclen = 0
    lchan = usim_lchan
    try:
        # Read ICCID (MF/2FE2, transparent)
        sel = _select_file_chain('MF/EF.ICCID', lchan=lchan)
        if sel.get('success'):
            fcp = sel.get('fcp', '')
            iccid_meta = parse_fcp(fcp) if fcp else {}
            fs = iccid_meta.get('file_size', 10)
            r = modem.csim_read_binary(fs, lchan=lchan)
            if r.get('sw', '').startswith('90') and r.get('data'):
                iccid_hex = r['data']
                iccid = _decode_iccid(iccid_hex)
    except Exception:
        pass
    try:
        sel = _select_file_chain('ADF.USIM/EF.IMSI', lchan=lchan)
        if sel.get('success'):
            fcp = sel.get('fcp', '')
            imsi_meta = parse_fcp(fcp) if fcp else {}
            fs = imsi_meta.get('file_size', 9)
            r = modem.csim_read_binary(fs, lchan=lchan)
            if r.get('sw', '').startswith('90') and r.get('data'):
                imsi_hex = r['data']
                imsi = _decode_imsi(imsi_hex)
    except Exception:
        pass
    try:
        sel = _select_file_chain('ADF.USIM/EF.MSISDN', lchan=lchan)
        if sel.get('success'):
            fcp = sel.get('fcp', '')
            msisdn_meta = parse_fcp(fcp) if fcp else {}
            msisdn_reclen = msisdn_meta.get('record_len', 0)
            if msisdn_reclen:
                r = modem.csim_read_record(1, msisdn_reclen, lchan=lchan)
                if r.get('sw', '').startswith('90') and r.get('data'):
                    msisdn_hex = r['data']
                    msisdn = _decode_msisdn(msisdn_hex)
    except Exception:
        pass
    return jsonify({
        'iccid': iccid, 'imsi': imsi, 'msisdn': msisdn,
        '_iccid_hex': iccid_hex, '_iccid_meta': iccid_meta,
        '_imsi_hex': imsi_hex, '_imsi_meta': imsi_meta,
        '_msisdn_hex': msisdn_hex, '_msisdn_meta': msisdn_meta,
        '_msisdn_reclen': msisdn_reclen,
    })


def _decode_iccid(hex_data: str) -> str:
    """Decode ICCID from EF.ICCID hex (swap nibbles)."""
    if not hex_data or len(hex_data) < 4:
        return ''
    digits = ''
    for i in range(0, len(hex_data), 2):
        lo = hex_data[i+1] if i+1 < len(hex_data) else 'F'
        hi = hex_data[i]
        if lo != 'F' and lo != 'f':
            digits += lo
        if hi != 'F' and hi != 'f':
            digits += hi
    return digits


def _decode_imsi(hex_data: str) -> str:
    """Decode IMSI from EF.IMSI hex."""
    if not hex_data or len(hex_data) < 4:
        return ''
    b = bytes.fromhex(hex_data)
    length = b[0]
    if length < 1 or length > 8:
        return ''
    digits = str((b[1] >> 4) & 0x0F)
    for i in range(2, 1 + length):
        if i >= len(b):
            break
        lo = b[i] & 0x0F
        hi = (b[i] >> 4) & 0x0F
        if lo <= 9:
            digits += str(lo)
        if hi <= 9:
            digits += str(hi)
    return digits


def _decode_msisdn(hex_data: str) -> str:
    """Decode phone number from EF.MSISDN record."""
    if not hex_data or len(hex_data) < 28:
        return ''
    b = bytes.fromhex(hex_data)
    bcd_offset = len(b) - 14
    bcd_len = b[bcd_offset]
    if bcd_len < 2 or bcd_len > 12 or bcd_len == 0xFF:
        return ''
    ton_npi = b[bcd_offset + 1]
    prefix = '+' if (ton_npi & 0x70) == 0x10 else ''
    digits = ''
    for i in range(bcd_offset + 2, bcd_offset + 1 + bcd_len):
        if i >= len(b):
            break
        lo = b[i] & 0x0F
        hi = (b[i] >> 4) & 0x0F
        if lo <= 9:
            digits += str(lo)
        if hi <= 9:
            digits += str(hi)
    return prefix + digits



@app.route('/files', methods=['GET'])
def get_files():
    """Return 3GPP standard SIM file tree."""
    tree = build_file_tree()
    return jsonify({'files': tree, 'usim_aid': usim_aid, 'isim_aid': isim_aid})


@app.route('/read', methods=['POST'])
def read_file():
    """Read EF file via AT+CSIM — SELECT by AID + FID chain, then READ."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    path = request.json.get('path', '')
    fid_hex = request.json.get('fid', '')
    structure = request.json.get('structure', 'transparent')

    if not fid_hex:
        return jsonify({'success': False, 'error': 'Missing FID'})

    return _read_file_csim(path, fid_hex, structure)


@app.route('/write', methods=['POST'])
def write_file():
    """Write to EF file via AT+CSIM or AT+CCHO/CGLA for ISIM fallback."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    path = request.json.get('path', '')
    fid_hex = request.json.get('fid', '')
    structure = request.json.get('structure', 'transparent')
    hex_data = request.json.get('data', '').strip().replace(' ', '')
    record_nr = request.json.get('record_nr', 0)
    record_len = request.json.get('record_len', 0)

    if not fid_hex or not hex_data:
        return jsonify({'success': False, 'error': 'Missing FID or data'})

    is_isim = path.startswith('ADF.ISIM') if path else False

    # ISIM via CCHO fallback
    if is_isim and isim_ccho:
        return _write_file_ccho(path, fid_hex, structure, hex_data, record_nr, record_len)

    lchan = isim_lchan if is_isim else usim_lchan

    # SELECT the file first
    if path:
        modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
        sel = _select_file_chain(path, lchan=lchan)
        if not sel['success']:
            sel['log'] = [{'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()}]
            return jsonify(sel)

    # UPDATE via CSIM on correct logical channel
    cla = _cla_for_lchan(lchan)
    data_len = len(hex_data) // 2
    log_lines = []
    if structure in ('linear_fixed', 'cyclic') and record_nr > 0:
        rl = record_len or data_len
        modem._log_apdu('msg', f'UPDATE RECORD #{record_nr} ({rl} bytes)')
        apdu = f'{cla:02X}DC{record_nr:02X}04{rl:02X}{hex_data}'
        r = modem.csim_send(apdu)
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
    else:
        modem._log_apdu('msg', f'UPDATE BINARY ({data_len} bytes)')
        # Split into 255-byte chunks
        offset = 0
        r = {'success': True, 'sw': '9000'}
        while offset < data_len:
            chunk_len = min(255, data_len - offset)
            p1 = (offset >> 8) & 0xFF
            p2 = offset & 0xFF
            chunk_hex = hex_data[offset*2:(offset+chunk_len)*2]
            apdu = f'{cla:02X}D6{p1:02X}{p2:02X}{chunk_len:02X}{chunk_hex}'
            r = modem.csim_send(apdu)
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            if not r.get('sw', '').startswith('90'):
                break
            offset += chunk_len
    sw = r.get('sw', '')
    success = sw.startswith('90')
    result = {'success': success, 'sw': sw, 'log': log_lines}
    if not success:
        result['error'] = f'SW={sw}'
    return jsonify(result)


@app.route('/verify_adm', methods=['POST'])
def verify_adm():
    """ADM verification — supports ADM1~4."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    adm_hex = request.json.get('adm', '').strip().replace(' ', '')
    adm_type = request.json.get('adm_type', 'ADM1')

    if len(adm_hex) != 16:
        return jsonify({'success': False, 'error': 'ADM must be 16 hex digits'})

    # Map ADM type to key reference
    key_ref_map = {'ADM1': '0A', 'ADM2': '0B', 'ADM3': '0C', 'ADM4': '0D'}
    key_ref = key_ref_map.get(adm_type, '0A')

    r = modem.verify_adm(adm_hex, key_ref)
    r['log'] = [{'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()}]
    return jsonify(r)


@app.route('/service_map', methods=['POST'])
def service_map():
    """Return service table map for EF.UST, EF.IST, or EF.EST."""
    try:
        ef_name = request.json.get('ef', '')
        if 'UST' in ef_name:
            from pySim.ts_31_102 import EF_UST_map
            return jsonify({'success': True, 'map': {str(k): v for k, v in EF_UST_map.items()}})
        elif 'IST' in ef_name:
            from pySim.ts_31_103 import EF_IST_map
            return jsonify({'success': True, 'map': {str(k): v for k, v in EF_IST_map.items()}})
        elif 'EST' in ef_name:
            from pySim.ts_31_102 import EF_EST_map
            return jsonify({'success': True, 'map': {str(k): v for k, v in EF_EST_map.items()}})
        else:
            return jsonify({'success': False, 'error': 'Unknown service table'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/read_arr', methods=['POST'])
def read_arr():
    """Read EF.ARR files via AT+CSIM and decode records for access rule display.
    Reads MF, USIM, and ISIM ARR separately (each ADF may have different rules)."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    results = {}
    # MF and USIM ARR — channel 0
    for af in [{'path': 'MF/EF.ARR'}, {'path': 'ADF.USIM/EF.ARR'}]:
        sel = _select_file_chain(af['path'])
        if not sel['success']:
            continue
        fcp_data = sel.get('fcp', '')
        if not fcp_data:
            continue
        meta = parse_fcp(fcp_data)
        record_len = meta.get('record_len', 0)
        num_records = meta.get('num_records', 0)
        if not record_len or not num_records:
            continue
        records = []
        for i in range(1, num_records + 1):
            r = modem.csim_read_record(i, record_len, lchan=0)
            if r.get('sw', '').startswith('90'):
                records.append(r.get('data', ''))
            else:
                records.append(None)
        decoded = decode_ef_records(af['path'], records)
        results[af['path']] = {
            'records_hex': records, 'decoded': decoded, 'num_records': num_records,
            'meta': meta,
        }

    # ISIM ARR — use scanned ISIM channel or CCHO fallback
    if isim_aid and isim_lchan >= 0:
        try:
            if isim_ccho:
                # Use CCHO/CGLA for ISIM ARR
                session = modem.ccho_open(isim_aid)
                if session:
                    try:
                        sel = modem.cgla_send(session, '00A40804047FFF6F06')
                        sw = sel.get('sw', '')
                        fcp_data = sel.get('data', '')
                        if not fcp_data and sw.startswith('61'):
                            gr = modem.cgla_send(session, f'00C00000{sw[2:4]}')
                            fcp_data = gr.get('data', '')
                        if fcp_data and (sw.startswith('90') or sw.startswith('61')):
                            meta = parse_fcp(fcp_data)
                            record_len = meta.get('record_len', 0)
                            num_records = meta.get('num_records', 0)
                            if record_len and num_records:
                                records = []
                                for i in range(1, num_records + 1):
                                    r = modem.cgla_send(session, f'00B2{i:02X}04{record_len:02X}')
                                    if r.get('sw', '').startswith('90'):
                                        records.append(r.get('data', ''))
                                    else:
                                        records.append(None)
                                decoded = decode_ef_records('ADF.ISIM/EF.ARR', records)
                                results['ADF.ISIM/EF.ARR'] = {
                                    'records_hex': records, 'decoded': decoded,
                                    'num_records': num_records, 'meta': meta,
                                }
                    finally:
                        modem.ccho_close(session)
            else:
                # Use scanned ISIM channel
                sel = _select_file_chain('ADF.ISIM/EF.ARR', lchan=isim_lchan)
                if sel.get('success'):
                    fcp_data = sel.get('fcp', '')
                    if fcp_data:
                        meta = parse_fcp(fcp_data)
                        record_len = meta.get('record_len', 0)
                        num_records = meta.get('num_records', 0)
                        if record_len and num_records:
                            records = []
                            for i in range(1, num_records + 1):
                                r = modem.csim_read_record(i, record_len, lchan=isim_lchan)
                                if r.get('sw', '').startswith('90'):
                                    records.append(r.get('data', ''))
                                else:
                                    records.append(None)
                            decoded = decode_ef_records('ADF.ISIM/EF.ARR', records)
                            results['ADF.ISIM/EF.ARR'] = {
                                'records_hex': records, 'decoded': decoded,
                                'num_records': num_records, 'meta': meta,
                            }
        except Exception as e:
            logger.warning("[ARR] ISIM ARR read failed: %s", e)

    return jsonify({'success': True, 'arr': results})


@app.route('/write_tlv', methods=['POST'])
def write_tlv():
    """BER-TLV write: SELECT chain + DELETE DATA + SET DATA via AT+CSIM or CCHO."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    path = request.json.get('path', '')
    tag = request.json.get('tag', '')
    data = request.json.get('data', '').strip().replace(' ', '')

    if not path or not tag:
        return jsonify({'success': False, 'error': 'Missing path or tag'})

    tag_hex = tag.replace('0x', '').replace('0X', '')

    is_isim = path.startswith('ADF.ISIM')

    # ISIM via CCHO fallback
    if is_isim and isim_ccho:
        return _write_tlv_ccho(path, tag_hex, data)

    lchan = isim_lchan if is_isim else usim_lchan

    modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
    select_results = _select_file_chain(path, lchan=lchan)
    if not select_results['success']:
        return jsonify(select_results)

    cla = _cla_for_lchan(lchan, proprietary=True)
    modem._log_apdu('msg', 'DELETE DATA (tag=0x' + tag_hex + ')')
    del_apdu = f'{cla:02X}DB0080{len(tag_hex)//2:02X}{tag_hex}'
    modem.csim_send(del_apdu)

    if data:
        modem._log_apdu('msg', 'SET DATA (tag=0x' + tag_hex + ')')
        val_len = len(data) // 2
        if val_len <= 0x7F:
            ber_len = f'{val_len:02X}'
        elif val_len <= 0xFF:
            ber_len = f'81{val_len:02X}'
        else:
            ber_len = f'82{val_len:04X}'
        tlv = tag_hex + ber_len + data
        lc = len(tlv) // 2
        set_apdu = f'{cla:02X}DB0080{lc:02X}{tlv}'
        r = modem.csim_send(set_apdu)
        if not r['success']:
            return jsonify({'success': False, 'error': f'SET DATA failed: {r.get("error", r.get("sw", ""))}'})

    return jsonify({'success': True})


def _read_file_csim(path: str, fid_hex: str, structure: str) -> 'Response':
    """Read EF via AT+CSIM: path SELECT + READ on scanned logical channel.
    For ISIM with CCHO fallback: uses AT+CCHO/CGLA instead of AT+CSIM."""
    log_lines = []
    is_isim = path.startswith('ADF.ISIM')

    if is_isim and isim_lchan < 0:
        return jsonify({
            'success': False,
            'error': 'ISIM channel not available on this modem',
            'log': log_lines,
        })

    # ISIM via CCHO/CGLA fallback
    if is_isim and isim_ccho:
        return _read_file_ccho(path, fid_hex, structure)

    lchan = isim_lchan if is_isim else usim_lchan

    # Step 1: SELECT file chain
    modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
    select_result = _select_file_chain(path, lchan=lchan)
    if not select_result['success']:
        return jsonify({
            'success': False,
            'error': select_result.get('error', 'SELECT failed'),
            'sw': select_result.get('sw', ''),
            'log': log_lines,
        })

    # Step 2: Parse FCP from SELECT response
    meta = {}
    fcp_data = select_result.get('fcp', '')
    if fcp_data:
        meta = parse_fcp(fcp_data)

    actual_structure = meta.get('structure', structure)
    file_size = meta.get('file_size', 0)
    record_len = meta.get('record_len', 0)
    num_records = meta.get('num_records', 0)

    # Step 3: Read based on structure
    if actual_structure == 'ber_tlv':
        modem._log_apdu('msg', 'RETRIEVE DATA (tag=0x80)')
        cla = _cla_for_lchan(lchan, proprietary=True)
        retrieve_apdu = f'{cla:02X}CB0080018000'
        r = modem.csim_send(retrieve_apdu)
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
        all_data = r.get('data', '')
        sw = r.get('sw', '')
        while sw.startswith('62'):
            r2 = modem.csim_send(f'{cla:02X}CB000000')
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            all_data += r2.get('data', '')
            sw = r2.get('sw', '')
        if not all_data and not sw.startswith('90'):
            return jsonify({
                'success': False, 'error': f'RETRIEVE DATA failed: SW={sw}',
                'sw': sw, 'meta': meta, 'log': log_lines,
            })
        return jsonify({
            'success': True, 'structure': 'ber_tlv', 'data': all_data,
            'meta': meta, 'file_size': file_size,
            'decoded': decode_ef(path, all_data, 'ber_tlv') if all_data else None,
            'log': log_lines,
        })

    elif actual_structure in ('linear_fixed', 'cyclic'):
        if not record_len:
            return jsonify({
                'success': False,
                'error': f'No record length info (meta: {json.dumps(meta)})',
                'meta': meta, 'log': log_lines,
            })
        records = []
        for i in range(1, (num_records or 1) + 1):
            modem._log_apdu('msg', f'READ RECORD #{i} ({record_len} bytes)')
            r = modem.csim_read_record(i, record_len, lchan=lchan)
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            sw = r.get('sw', '')
            if sw.startswith('90'):
                records.append(r.get('data', ''))
            else:
                if sw == '6A83':
                    break
                records.append(None)
        return jsonify({
            'success': True, 'structure': actual_structure, 'data': records,
            'meta': meta, 'record_len': record_len, 'num_records': len(records),
            'decoded': decode_ef_records(path, records),
            'log': log_lines,
        })

    else:  # transparent
        read_len = file_size if file_size > 0 else 0
        modem._log_apdu('msg', f'READ BINARY ({read_len} bytes)')
        r = modem.csim_read_binary(read_len, lchan=lchan)
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
        sw = r.get('sw', '')
        data = r.get('data', '')
        if not sw.startswith('90') and not data:
            return jsonify({
                'success': False, 'error': f'READ BINARY failed: SW={sw}',
                'sw': sw, 'meta': meta, 'log': log_lines,
            })
        return jsonify({
            'success': True, 'structure': 'transparent', 'data': data,
            'meta': meta, 'file_size': file_size,
            'decoded': decode_ef(path, data, 'transparent'),
            'log': log_lines,
        })


def _read_file_ccho(path: str, fid_hex: str, structure: str) -> 'Response':
    """Read ISIM EF via AT+CCHO/CGLA (fallback for modems without lchan support)."""
    from sim_files import get_file_by_path
    log_lines = []
    session = modem.ccho_open(isim_aid)
    if session is None:
        return jsonify({
            'success': False, 'error': 'AT+CCHO failed to open ISIM session',
            'log': log_lines,
        })
    try:
        # Build FID path: 7FFF + sub FIDs
        parts = path.split('/')
        fid_path = '7FFF'
        for i, part in enumerate(parts[1:]):
            sub_path = '/'.join(parts[:i+2])
            fi = get_file_by_path(sub_path)
            if fi:
                fid_path += fi['fid'].upper()
            else:
                fid = _name_to_fid(part)
                if fid:
                    fid_path += fid
                else:
                    return jsonify({'success': False, 'error': f'Unknown file: {part}'})

        # SELECT by path via CGLA
        modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
        lc = len(fid_path) // 2
        sel = modem.cgla_send(session, f'00A40804{lc:02X}{fid_path}')
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
        sw = sel.get('sw', '')
        if not (sw.startswith('90') or sw.startswith('61')):
            return jsonify({
                'success': False, 'error': f'SELECT failed: SW={sw}',
                'sw': sw, 'log': log_lines,
            })

        # Parse FCP
        meta = {}
        fcp_data = sel.get('data', '')
        if not fcp_data and sw.startswith('61'):
            le = sw[2:4]
            gr = modem.cgla_send(session, f'00C00000{le}')
            fcp_data = gr.get('data', '')
        if fcp_data:
            meta = parse_fcp(fcp_data)

        actual_structure = meta.get('structure', structure)
        file_size = meta.get('file_size', 0)
        record_len = meta.get('record_len', 0)
        num_records = meta.get('num_records', 0)

        # Read based on structure
        if actual_structure == 'ber_tlv':
            modem._log_apdu('msg', 'RETRIEVE DATA (tag=0x80)')
            r = modem.cgla_send(session, '80CB0080018000')
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            all_data = r.get('data', '')
            sw = r.get('sw', '')
            while sw.startswith('62'):
                r2 = modem.cgla_send(session, '80CB000000')
                log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
                all_data += r2.get('data', '')
                sw = r2.get('sw', '')
            if not all_data and not sw.startswith('90'):
                return jsonify({
                    'success': False, 'error': f'RETRIEVE DATA failed: SW={sw}',
                    'sw': sw, 'meta': meta, 'log': log_lines,
                })
            return jsonify({
                'success': True, 'structure': 'ber_tlv', 'data': all_data,
                'meta': meta, 'file_size': file_size,
                'decoded': decode_ef(path, all_data, 'ber_tlv') if all_data else None,
                'log': log_lines,
            })

        elif actual_structure in ('linear_fixed', 'cyclic'):
            if not record_len:
                return jsonify({
                    'success': False,
                    'error': f'No record length info (meta: {json.dumps(meta)})',
                    'meta': meta, 'log': log_lines,
                })
            records = []
            for i in range(1, (num_records or 1) + 1):
                modem._log_apdu('msg', f'READ RECORD #{i} ({record_len} bytes)')
                r = modem.cgla_send(session, f'00B2{i:02X}04{record_len:02X}')
                log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
                sw = r.get('sw', '')
                if sw.startswith('90'):
                    records.append(r.get('data', ''))
                else:
                    if sw == '6A83':
                        break
                    records.append(None)
            return jsonify({
                'success': True, 'structure': actual_structure, 'data': records,
                'meta': meta, 'record_len': record_len, 'num_records': len(records),
                'decoded': decode_ef_records(path, records),
                'log': log_lines,
            })

        else:  # transparent
            read_len = file_size if file_size > 0 else 0
            modem._log_apdu('msg', f'READ BINARY ({read_len} bytes)')
            if read_len <= 255:
                r = modem.cgla_send(session, f'00B00000{read_len:02X}')
            else:
                data = ''
                offset = 0
                while offset < read_len:
                    chunk = min(255, read_len - offset)
                    p1 = (offset >> 8) & 0xFF
                    p2 = offset & 0xFF
                    r = modem.cgla_send(session, f'00B0{p1:02X}{p2:02X}{chunk:02X}')
                    if r.get('sw', '').startswith('90'):
                        data += r.get('data', '')
                        offset += chunk
                    else:
                        break
                r = {'success': True, 'data': data, 'sw': '9000'}
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            sw = r.get('sw', '')
            data = r.get('data', '')
            if not sw.startswith('90') and not data:
                return jsonify({
                    'success': False, 'error': f'READ BINARY failed: SW={sw}',
                    'sw': sw, 'meta': meta, 'log': log_lines,
                })
            return jsonify({
                'success': True, 'structure': 'transparent', 'data': data,
                'meta': meta, 'file_size': file_size,
                'decoded': decode_ef(path, data, 'transparent'),
                'log': log_lines,
            })
    finally:
        modem.ccho_close(session)


def _write_file_ccho(path: str, fid_hex: str, structure: str,
                     hex_data: str, record_nr: int, record_len: int) -> 'Response':
    """Write ISIM EF via AT+CCHO/CGLA fallback."""
    from sim_files import get_file_by_path
    session = modem.ccho_open(isim_aid)
    if session is None:
        return jsonify({'success': False, 'error': 'AT+CCHO failed to open ISIM session'})
    try:
        # Build FID path
        parts = path.split('/')
        fid_path = '7FFF'
        for i, part in enumerate(parts[1:]):
            sub_path = '/'.join(parts[:i+2])
            fi = get_file_by_path(sub_path)
            if fi:
                fid_path += fi['fid'].upper()
            else:
                fid = _name_to_fid(part)
                if fid:
                    fid_path += fid
        lc = len(fid_path) // 2
        modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
        sel = modem.cgla_send(session, f'00A40804{lc:02X}{fid_path}')
        sw = sel.get('sw', '')
        if not (sw.startswith('90') or sw.startswith('61')):
            return jsonify({'success': False, 'error': f'SELECT failed: SW={sw}', 'sw': sw})
        # UPDATE
        data_len = len(hex_data) // 2
        if structure in ('linear_fixed', 'cyclic') and record_nr > 0:
            rl = record_len or data_len
            modem._log_apdu('msg', f'UPDATE RECORD #{record_nr} ({rl} bytes)')
            r = modem.cgla_send(session, f'00DC{record_nr:02X}04{rl:02X}{hex_data}')
        else:
            modem._log_apdu('msg', f'UPDATE BINARY ({data_len} bytes)')
            offset = 0
            r = {'success': True, 'sw': '9000'}
            while offset < data_len:
                chunk_len = min(255, data_len - offset)
                p1 = (offset >> 8) & 0xFF
                p2 = offset & 0xFF
                chunk_hex = hex_data[offset*2:(offset+chunk_len)*2]
                r = modem.cgla_send(session, f'00D6{p1:02X}{p2:02X}{chunk_len:02X}{chunk_hex}')
                if not r.get('sw', '').startswith('90'):
                    break
                offset += chunk_len
        sw = r.get('sw', '')
        success = sw.startswith('90')
        result = {'success': success, 'sw': sw}
        if not success:
            result['error'] = f'SW={sw}'
        return jsonify(result)
    finally:
        modem.ccho_close(session)


def _write_tlv_ccho(path: str, tag_hex: str, data: str) -> 'Response':
    """BER-TLV write ISIM EF via AT+CCHO/CGLA fallback."""
    from sim_files import get_file_by_path
    session = modem.ccho_open(isim_aid)
    if session is None:
        return jsonify({'success': False, 'error': 'AT+CCHO failed to open ISIM session'})
    try:
        parts = path.split('/')
        fid_path = '7FFF'
        for i, part in enumerate(parts[1:]):
            sub_path = '/'.join(parts[:i+2])
            fi = get_file_by_path(sub_path)
            if fi:
                fid_path += fi['fid'].upper()
            else:
                fid = _name_to_fid(part)
                if fid:
                    fid_path += fid
        lc = len(fid_path) // 2
        modem._log_apdu('msg', 'SELECT ' + path.split('/')[-1] + ' (' + (get_file_by_path(path) or {}).get('fid','') + ')')
        sel = modem.cgla_send(session, f'00A40804{lc:02X}{fid_path}')
        sw = sel.get('sw', '')
        if not (sw.startswith('90') or sw.startswith('61')):
            return jsonify({'success': False, 'error': f'SELECT failed: SW={sw}', 'sw': sw})
        # DELETE existing tag
        modem._log_apdu('msg', 'DELETE DATA (tag=0x' + tag_hex + ')')
        del_apdu = f'80DB0080{len(tag_hex)//2:02X}{tag_hex}'
        modem.cgla_send(session, del_apdu)
        # SET DATA
        if data:
            modem._log_apdu('msg', 'SET DATA (tag=0x' + tag_hex + ')')
            val_len = len(data) // 2
            if val_len <= 0x7F:
                ber_len = f'{val_len:02X}'
            elif val_len <= 0xFF:
                ber_len = f'81{val_len:02X}'
            else:
                ber_len = f'82{val_len:04X}'
            tlv = tag_hex + ber_len + data
            tlv_lc = len(tlv) // 2
            set_apdu = f'80DB0080{tlv_lc:02X}{tlv}'
            r = modem.cgla_send(session, set_apdu)
            if not r.get('success'):
                return jsonify({'success': False, 'error': f'SET DATA failed: {r.get("error", r.get("sw", ""))}'})
        return jsonify({'success': True})
    finally:
        modem.ccho_close(session)


def _select_file_chain(path: str, lchan: int = 0) -> dict:
    """Select file via AT+CSIM: AID SELECT + path SELECT in one APDU.
    For ADF: SELECT AID, then SELECT remaining DFs/EF by path (00A40804).
    For MF: SELECT by path from 3F00.
    lchan: logical channel number for ISIM access."""
    from sim_files import get_file_by_path
    parts = path.split('/')

    adf_part = parts[0] if parts else ''
    if adf_part in ('ADF.USIM', 'ADF.ISIM'):
        is_isim = (adf_part == 'ADF.ISIM')

        if is_isim:
            if isim_lchan < 0:
                return {'success': False, 'error': 'ISIM channel not available'}
            lchan = isim_lchan
        else:
            lchan = usim_lchan

        cla = _cla_for_lchan(lchan)

        # SELECT sub-DFs and EF by path using 7FFF (P1=08, P2=04)
        sub_parts = parts[1:]
        if not sub_parts:
            return {'success': True, 'fcp': '', 'sw': ''}

        fid_path = '7FFF'
        for i, part in enumerate(sub_parts):
            sub_path = '/'.join(parts[:i+2])
            fi = get_file_by_path(sub_path)
            if fi:
                fid_path += fi['fid'].upper()
            else:
                fid = _name_to_fid(part)
                if not fid:
                    return {'success': False, 'error': f'Unknown file: {part} in {path}'}
                fid_path += fid

        lc = len(fid_path) // 2
        apdu = f'{cla:02X}A40804{lc:02X}{fid_path}'
        r = modem.csim_send(apdu)
        sw = r.get('sw', '')
        if sw.startswith('90') or sw.startswith('61') or sw.startswith('9F'):
            return {'success': True, 'fcp': r.get('data', ''), 'sw': sw}
        return {'success': False, 'error': f'SELECT path {fid_path} failed: SW={sw}', 'sw': sw}

    elif adf_part == 'MF':
        # MF files: SELECT by path (P1=08, P2=04) — without 3F00 prefix
        cla = _cla_for_lchan(usim_lchan)
        fid_path = ''
        for i, part in enumerate(parts):
            if part == 'MF':
                continue
            sub_path = '/'.join(parts[:i+1])
            fi = get_file_by_path(sub_path)
            if fi:
                fid_path += fi['fid'].upper()
            else:
                fid = _name_to_fid(part)
                if not fid:
                    return {'success': False, 'error': f'Unknown file: {part} in {path}'}
                fid_path += fid

        if not fid_path:
            return {'success': False, 'error': f'Empty FID path for {path}'}
        lc = len(fid_path) // 2
        apdu = f'{cla:02X}A40804{lc:02X}{fid_path}'
        r = modem.csim_send(apdu)
        sw = r.get('sw', '')
        if sw.startswith('90') or sw.startswith('61') or sw.startswith('9F'):
            return {'success': True, 'fcp': r.get('data', ''), 'sw': sw}
        return {'success': False, 'error': f'SELECT path {fid_path} failed: SW={sw}', 'sw': sw}

    return {'success': False, 'error': f'Unknown path prefix: {adf_part}'}


def _name_to_fid(name: str) -> str:
    """Fallback: map common DF/EF names to FIDs."""
    known = {
        'DF.5GS': '5FC0', 'DF.GSM-ACCESS': '5F3B', 'DF.HNB': '5F50',
        'DF.PHONEBOOK': '5F3A', 'DF.WLAN': '5F40', 'DF.ProSe': '5F90',
        'DF.SNPN': '5FE0', 'DF.5G_ProSe': '5FF0', 'DF.SAIP': '5FD0',
        'DF.5MBSUECONFIG': '5FF1',
    }
    return known.get(name, '')


@app.route('/at_raw', methods=['POST'])
def at_raw():
    """Send raw AT command."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})
    cmd = request.json.get('cmd', '').strip()
    if not cmd:
        return jsonify({'success': False, 'error': 'No command'})
    resp = modem._send(cmd)
    return jsonify({'success': True, 'response': resp})


@app.route('/apdu_log', methods=['GET'])
def apdu_log():
    """Return APDU log entries since given index."""
    since = int(request.args.get('since', 0))
    entries = modem.apdu_log[since:]
    return jsonify({'entries': entries, 'total': len(modem.apdu_log)})


# Suppress apdu_log polling from Flask request log
import logging as _logging
_logging.getLogger('werkzeug').addFilter(
    type('', (_logging.Filter,), {'filter': lambda self, r: '/apdu_log' not in r.getMessage()})()
)


@app.route('/apdu_log_clear', methods=['POST'])
def apdu_log_clear():
    """Clear APDU log buffer."""
    modem.apdu_log.clear()
    return jsonify({'success': True})


@app.route('/apdu_send', methods=['POST'])
def apdu_send():
    """Send raw APDU hex via AT+CSIM and return result."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})
    apdu = request.json.get('apdu', '').strip().replace(' ', '').upper()
    if not apdu or len(apdu) < 8:
        return jsonify({'success': False, 'error': 'Invalid APDU (min 4 bytes)'})
    r = modem.csim_send(apdu)
    return jsonify(r)


def _kill_existing_process(port: int):
    """Kill any existing process on the given port (cross-platform)."""
    import subprocess
    try:
        if platform.system() == 'Windows':
            # Windows: netstat + taskkill
            result = subprocess.run(
                ['netstat', '-ano'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    if pid.isdigit():
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True, timeout=5)
                        print(f"[init] Killed existing process on port {port} (PID {pid})")
        else:
            # macOS / Linux: lsof
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'], capture_output=True, text=True, timeout=5)
            for pid in result.stdout.strip().split('\n'):
                if pid:
                    subprocess.run(['kill', '-9', pid], capture_output=True, timeout=5)
                    print(f"[init] Killed existing process on port {port} (PID {pid})")
    except Exception:
        pass


if __name__ == '__main__':
    PORT = 8083
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    _kill_existing_process(PORT)
    print(f"🚀 SIM AT Command Tool")
    print(f"   http://127.0.0.1:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
