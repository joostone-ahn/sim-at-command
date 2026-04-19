#!/usr/bin/env python3
"""SIM AT Command Tool — Flask Web Application."""

import json
import sys
import logging
import platform
from pathlib import Path
from flask import Flask, render_template, request, jsonify

sys.path.insert(0, str(Path(__file__).parent))
from at_modem import ATModem, parse_fcp
from sim_files import SIM_FILES, build_file_tree
from decoder import decode_ef, decode_ef_records

app = Flask(__name__)
app.json.sort_keys = False
logger = logging.getLogger(__name__)

modem = ATModem()
usim_aid = ''
isim_aid = ''


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ports', methods=['GET'])
def list_ports():
    """List available serial ports."""
    ports = ATModem.list_ports()
    return jsonify({'ports': ports})


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
    modem.disconnect()
    return jsonify({'success': True})


@app.route('/at_check', methods=['POST'])
def at_check():
    """Verify AT + CRSM functionality."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})
    result = modem.at_check()
    return jsonify(result)



@app.route('/files', methods=['GET'])
def get_files():
    """Return 3GPP standard SIM file tree."""
    tree = build_file_tree()
    return jsonify({'files': tree})


@app.route('/read', methods=['POST'])
def read_file():
    """Read EF file via GET RESPONSE + READ BINARY/RECORD."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    path = request.json.get('path', '')
    fid_hex = request.json.get('fid', '')
    structure = request.json.get('structure', 'transparent')

    if not fid_hex:
        return jsonify({'success': False, 'error': 'Missing FID'})

    fid = int(fid_hex, 16)

    # 1) GET RESPONSE for file metadata
    meta_resp = modem.crsm_get_response(fid)
    log_lines = [{'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()}]
    meta = {}
    if meta_resp['success'] and meta_resp['data']:
        meta = parse_fcp(meta_resp['data'])

    # Use metadata structure if available
    actual_structure = meta.get('structure', structure)
    file_size = meta.get('file_size', 0)
    record_len = meta.get('record_len', 0)
    num_records = meta.get('num_records', 0)

    # 2) Read based on structure
    if actual_structure == 'ber_tlv':
        # BER-TLV: use RETRIEVE DATA via AT+CSIM
        # First SELECT the file
        select_result = _select_file_chain(path)
        if not select_result['success']:
            return jsonify({
                'success': False,
                'error': select_result.get('error', 'SELECT failed'),
                'meta': meta,
                'log': log_lines,
            })
        # RETRIEVE DATA: 80CB0080 01 80 00 (tag 0x80, Le=00)
        retrieve_apdu = '80CB0080018000'
        r = modem.csim_send(retrieve_apdu)
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
        all_data = r.get('data', '')
        sw = r.get('sw', '')
        # Handle continuation: 62F1/62F2 means more data
        while sw.startswith('62'):
            cont_apdu = '80CB000000'
            r2 = modem.csim_send(cont_apdu)
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            all_data += r2.get('data', '')
            sw = r2.get('sw', '')
        if not all_data and not sw.startswith('90'):
            return jsonify({
                'success': False,
                'error': f'RETRIEVE DATA failed: SW={sw}',
                'sw': sw,
                'meta': meta,
                'log': log_lines,
            })
        return jsonify({
            'success': True,
            'structure': 'ber_tlv',
            'data': all_data,
            'meta': meta,
            'file_size': file_size,
            'decoded': decode_ef(path, all_data, 'ber_tlv') if all_data else None,
            'log': log_lines,
        })
    elif actual_structure in ('linear_fixed', 'cyclic'):
        if not record_len:
            return jsonify({
                'success': False,
                'error': f'No record length info (meta: {json.dumps(meta)})',
                'meta': meta
            })
        records = []
        for i in range(1, (num_records or 1) + 1):
            r = modem.crsm_read_record(fid, i, record_len)
            log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
            if r['success']:
                records.append(r['data'])
            else:
                if r.get('sw1') == 106 and r.get('sw2') == 131:
                    break
                records.append(None)
        return jsonify({
            'success': True,
            'structure': actual_structure,
            'data': records,
            'meta': meta,
            'record_len': record_len,
            'num_records': len(records),
            'decoded': decode_ef_records(path, records),
            'log': log_lines,
        })
    else:
        read_len = file_size if file_size > 0 else 0
        r = modem.crsm_read_binary(fid, read_len)
        log_lines.append({'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()})
        if not r['success']:
            sw_hex = f"{r.get('sw1',0):02X}{r.get('sw2',0):02X}"
            return jsonify({
                'success': False,
                'error': r.get('error', 'Read failed'),
                'sw': sw_hex,
                'meta': meta,
                'log': log_lines,
            })
        return jsonify({
            'success': True,
            'structure': 'transparent',
            'data': r['data'],
            'meta': meta,
            'file_size': file_size,
            'decoded': decode_ef(path, r['data'], 'transparent'),
            'log': log_lines,
        })


@app.route('/write', methods=['POST'])
def write_file():
    """Write to EF file."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    fid_hex = request.json.get('fid', '')
    structure = request.json.get('structure', 'transparent')
    hex_data = request.json.get('data', '').strip().replace(' ', '')
    record_nr = request.json.get('record_nr', 0)
    record_len = request.json.get('record_len', 0)

    if not fid_hex or not hex_data:
        return jsonify({'success': False, 'error': 'Missing FID or data'})

    fid = int(fid_hex, 16)

    if structure in ('linear_fixed', 'cyclic') and record_nr > 0:
        r = modem.crsm_update_record(fid, record_nr, record_len or len(hex_data) // 2, hex_data)
    else:
        r = modem.crsm_update_binary(fid, hex_data)

    r['log'] = [{'cmd': modem.last_cmd, 'resp': modem.last_resp.strip()}]
    return jsonify(r)


@app.route('/verify_adm', methods=['POST'])
def verify_adm():
    """ADM verification."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    adm_hex = request.json.get('adm', '').strip().replace(' ', '')
    key_ref = request.json.get('key_ref', '0A')

    if len(adm_hex) != 16:
        return jsonify({'success': False, 'error': 'ADM must be 16 hex digits'})

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


@app.route('/write_tlv', methods=['POST'])
def write_tlv():
    """BER-TLV write: SELECT chain + DELETE DATA + SET DATA via AT+CSIM."""
    if not modem.is_connected:
        return jsonify({'success': False, 'error': 'Modem not connected'})

    path = request.json.get('path', '')
    tag = request.json.get('tag', '')  # e.g. '0x80' or '80'
    data = request.json.get('data', '').strip().replace(' ', '')

    if not path or not tag:
        return jsonify({'success': False, 'error': 'Missing path or tag'})

    tag_hex = tag.replace('0x', '').replace('0X', '')
    tag_int = int(tag_hex, 16)
    p1 = (tag_int >> 8) & 0xFF
    p2 = tag_int & 0xFF
    p1_hex = f'{p1:02X}'
    p2_hex = f'{p2:02X}'

    # Build SELECT chain from path
    # e.g. 'ADF.USIM/DF.5GS/EF.URSP' → SELECT ADF.USIM, SELECT DF.5GS, SELECT EF.URSP
    select_results = _select_file_chain(path)
    if not select_results['success']:
        return jsonify(select_results)

    # DELETE existing tag: CLA=80, INS=DB, P1=80(first block), P2=00, Data=<tag byte>=delete
    del_apdu = f'80DB0080{len(tag_hex)//2:02X}{tag_hex}'
    modem.csim_send(del_apdu)  # ignore errors — tag may not exist

    # SET DATA: build TLV from tag + data(value), then send
    # data = value only (without tag+length), we prepend tag + BER length
    if data:
        val_len = len(data) // 2
        if val_len <= 0x7F:
            ber_len = f'{val_len:02X}'
        elif val_len <= 0xFF:
            ber_len = f'81{val_len:02X}'
        else:
            ber_len = f'82{val_len:04X}'
        tlv = tag_hex + ber_len + data
        lc = len(tlv) // 2
        set_apdu = f'80DB0080{lc:02X}{tlv}'
        r = modem.csim_send(set_apdu)
        if not r['success']:
            return jsonify({'success': False, 'error': f'SET DATA failed: {r.get("error", r.get("sw", ""))}'})

    return jsonify({'success': True})


def _select_file_chain(path: str) -> dict:
    """Select file via AT+CSIM SELECT by path from MF."""
    from sim_files import get_file_by_path
    parts = path.split('/')
    ADF_FID = {'ADF.USIM': '7FFF', 'ADF.ISIM': '7FFF'}

    fid_path = ''
    for i, part in enumerate(parts):
        if part == 'MF':
            continue
        elif part in ADF_FID:
            fid_path += ADF_FID[part]
        else:
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
    apdu = f'00A40804{lc:02X}{fid_path}'
    r = modem.csim_send(apdu)
    sw = r.get('sw', '')
    if sw.startswith('90') or sw.startswith('61') or sw.startswith('9F'):
        return {'success': True}
    return {'success': False, 'error': f'SELECT path {fid_path} failed: SW={sw}'}


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
