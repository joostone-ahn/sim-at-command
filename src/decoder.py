#!/usr/bin/env python3
"""SIM file decoder using pySim EF classes.
Provides decode_ef() to convert raw hex into decoded JSON."""

import sys
import logging
from pathlib import Path

# Add pySim to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pysim"))

logger = logging.getLogger(__name__)

# Lazy-loaded EF instance cache: {path: ef_instance}
_ef_cache: dict = {}
_initialized = False


def _init():
    """Build EF instance cache from pySim definitions."""
    global _initialized, _ef_cache
    if _initialized:
        return
    try:
        from pySim.ts_102_221 import CardProfileUICC
        from pySim.ts_31_102 import ADF_USIM
        from pySim.ts_31_103 import ADF_ISIM
        from pySim.filesystem import CardEF, CardDF, LinFixedEF, TransparentEF, BerTlvEF

        def walk(node, prefix=''):
            """Recursively collect EF instances."""
            name = getattr(node, 'name', '') or ''
            current = f"{prefix}/{name}" if prefix else name
            if isinstance(node, CardEF):
                _ef_cache[current] = node
            if isinstance(node, CardDF):
                for child_name, child in node.children.items():
                    walk(child, current)

        # MF-level files
        profile = CardProfileUICC()
        for f in profile.files_in_mf:
            if isinstance(f, CardEF):
                path = f"MF/{f.name}"
                _ef_cache[path] = f

        # ADF.USIM
        usim = ADF_USIM()
        for child_name, child in usim.children.items():
            walk(child, 'ADF.USIM')

        # ADF.ISIM
        isim = ADF_ISIM()
        for child_name, child in isim.children.items():
            walk(child, 'ADF.ISIM')

        _initialized = True
        logger.info("[decoder] Loaded %d EF decoders", len(_ef_cache))
    except Exception as e:
        logger.error("[decoder] Failed to initialize: %s", e)
        _initialized = True  # Don't retry


def _find_ef(path: str):
    """Find EF instance by path. Tries exact match then name-based fallback."""
    _init()
    # Exact match
    if path in _ef_cache:
        return _ef_cache[path]
    # Try matching by EF name (last component)
    ef_name = path.split('/')[-1] if '/' in path else path
    for cached_path, ef in _ef_cache.items():
        if cached_path.endswith('/' + ef_name):
            return ef
    return None


def _json_safe(obj):
    """Convert decoded result to JSON-serializable format."""
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, bytearray):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _decode_ber_tlv(path: str, hex_data: str) -> dict | None:
    """Decode BER-TLV data by parsing tag+length+value and calling EF's decode_tag_data."""
    if not hex_data:
        return None
    try:
        tag_hex = hex_data[:2].upper()
        value_hex = _strip_tlv(hex_data)

        # Try EF-specific decode_tag_data (e.g. EF_URSP)
        ef = _find_ef(path)
        if ef and hasattr(ef, 'decode_tag_data'):
            result = ef.decode_tag_data(tag_hex, value_hex)
            return _json_safe(result)

        return {'raw': value_hex}
    except Exception as e:
        logger.warning("[decoder] BER-TLV decode error for %s: %s", path, e)
        return None


def _strip_tlv(hex_data: str) -> str:
    """Strip tag + BER length from TLV hex, return value portion."""
    if not hex_data or len(hex_data) < 4:
        return hex_data
    data = hex_data.upper()
    i = 0
    tag_byte = int(data[i:i+2], 16)
    i += 2
    if (tag_byte & 0x1F) == 0x1F:
        i += 2
    len_byte = int(data[i:i+2], 16)
    i += 2
    if len_byte == 0x81:
        i += 2
    elif len_byte == 0x82:
        i += 4
    return data[i:]


def decode_ef(path: str, hex_data: str, structure: str = 'transparent') -> dict | None:
    """Decode raw hex data for a given EF path."""
    if not hex_data:
        return None

    # BER-TLV: parse tag+length+value, decode via EF class
    if structure == 'ber_tlv':
        return _decode_ber_tlv(path, hex_data)

    ef = _find_ef(path)
    if not ef:
        return None

    try:
        if structure in ('linear_fixed', 'cyclic'):
            if hasattr(ef, 'decode_record_hex'):
                return _json_safe(ef.decode_record_hex(hex_data))
        else:
            if hasattr(ef, 'decode_hex'):
                return _json_safe(ef.decode_hex(hex_data))
    except Exception as e:
        logger.warning("[decoder] %s decode error: %s", path, e)
        return {'_decode_error': str(e)}

    return None


def decode_ef_records(path: str, hex_records: list[str]) -> list:
    """Decode all records of a linear fixed / cyclic EF.

    Args:
        path: File path
        hex_records: List of hex strings, one per record

    Returns:
        List of decoded dicts (None for failed records)
    """
    ef = _find_ef(path)
    if not ef or not hasattr(ef, 'decode_record_hex'):
        return [None] * len(hex_records)

    results = []
    for i, rec_hex in enumerate(hex_records):
        if not rec_hex:
            results.append(None)
            continue
        try:
            decoded = ef.decode_record_hex(rec_hex, record_nr=i+1)
            results.append(_json_safe(decoded))
        except Exception as e:
            logger.warning("[decoder] %s rec#%d decode error: %s", path, i+1, e)
            results.append({'_decode_error': str(e)})
    return results
