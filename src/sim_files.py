#!/usr/bin/env python3
"""3GPP standard SIM file definitions.
Extracted from pySim (ts_31_102, ts_31_103, ts_102_221)."""

# AT+CRSM file_id must be passed as decimal
# FID hex → decimal conversion needed

# Fields: path, name, fid(hex), type(DF/EF), structure(transparent/linear_fixed/cyclic/ber_tlv)
# path is for display; AT+CRSM uses FID-based access

SIM_FILES = [
    # ── MF (3F00) ──
    {'path': 'MF/EF.ICCID', 'name': 'EF.ICCID', 'fid': '2FE2', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'MF/EF.DIR', 'name': 'EF.DIR', 'fid': '2F00', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'MF/EF.PL', 'name': 'EF.PL', 'fid': '2F05', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'MF/EF.ARR', 'name': 'EF.ARR', 'fid': '2F06', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'MF/EF.UMPC', 'name': 'EF.UMPC', 'fid': '2F08', 'type': 'EF', 'structure': 'transparent'},

    # ── ADF.USIM ──
    {'path': 'ADF.USIM/EF.IMSI', 'name': 'EF.IMSI', 'fid': '6F07', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.LI', 'name': 'EF.LI', 'fid': '6F05', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.Keys', 'name': 'EF.Keys', 'fid': '6F08', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.KeysPS', 'name': 'EF.KeysPS', 'fid': '6F09', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PLMNwAcT', 'name': 'EF.PLMNwAcT', 'fid': '6F60', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.HPPLMN', 'name': 'EF.HPPLMN', 'fid': '6F31', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ACMmax', 'name': 'EF.ACMmax', 'fid': '6F37', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.UST', 'name': 'EF.UST', 'fid': '6F38', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ACM', 'name': 'EF.ACM', 'fid': '6F39', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.GID1', 'name': 'EF.GID1', 'fid': '6F3E', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.GID2', 'name': 'EF.GID2', 'fid': '6F3F', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.SPN', 'name': 'EF.SPN', 'fid': '6F46', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PUCT', 'name': 'EF.PUCT', 'fid': '6F41', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.CBMI', 'name': 'EF.CBMI', 'fid': '6F45', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ACC', 'name': 'EF.ACC', 'fid': '6F78', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.FPLMN', 'name': 'EF.FPLMN', 'fid': '6F7B', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.LOCI', 'name': 'EF.LOCI', 'fid': '6F7E', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.AD', 'name': 'EF.AD', 'fid': '6FAD', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.CBMID', 'name': 'EF.CBMID', 'fid': '6F48', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ECC', 'name': 'EF.ECC', 'fid': '6FB7', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.CBMIR', 'name': 'EF.CBMIR', 'fid': '6F50', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PSLOCI', 'name': 'EF.PSLOCI', 'fid': '6F73', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.FDN', 'name': 'EF.FDN', 'fid': '6F3B', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SMS', 'name': 'EF.SMS', 'fid': '6F3C', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MSISDN', 'name': 'EF.MSISDN', 'fid': '6F40', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SMSP', 'name': 'EF.SMSP', 'fid': '6F42', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SMSS', 'name': 'EF.SMSS', 'fid': '6F43', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.SDN', 'name': 'EF.SDN', 'fid': '6F49', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT2', 'name': 'EF.EXT2', 'fid': '6F4B', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT3', 'name': 'EF.EXT3', 'fid': '6F4C', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SMSR', 'name': 'EF.SMSR', 'fid': '6F47', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.ICI', 'name': 'EF.ICI', 'fid': '6F80', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.OCI', 'name': 'EF.OCI', 'fid': '6F81', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.ICT', 'name': 'EF.ICT', 'fid': '6F82', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.OCT', 'name': 'EF.OCT', 'fid': '6F83', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT5', 'name': 'EF.EXT5', 'fid': '6F4E', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.CCP2', 'name': 'EF.CCP2', 'fid': '6F4F', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.eMLPP', 'name': 'EF.eMLPP', 'fid': '6FB5', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.AAeM', 'name': 'EF.AAeM', 'fid': '6FB6', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.BDN', 'name': 'EF.BDN', 'fid': '6F4D', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT4', 'name': 'EF.EXT4', 'fid': '6F55', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.CMI', 'name': 'EF.CMI', 'fid': '6F58', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EST', 'name': 'EF.EST', 'fid': '6F56', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ACL', 'name': 'EF.ACL', 'fid': '6F57', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.DCK', 'name': 'EF.DCK', 'fid': '6F2C', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.CNL', 'name': 'EF.CNL', 'fid': '6F32', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.START-HFN', 'name': 'EF.START-HFN', 'fid': '6F5B', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.THRESHOLD', 'name': 'EF.THRESHOLD', 'fid': '6F5C', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.OPLMNwAcT', 'name': 'EF.OPLMNwAcT', 'fid': '6F61', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.HPLMNwAcT', 'name': 'EF.HPLMNwAcT', 'fid': '6F62', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ARR', 'name': 'EF.ARR', 'fid': '6F06', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.RPLMNAcTD', 'name': 'EF.RPLMNAcTD', 'fid': '6F65', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.NETPAR', 'name': 'EF.NETPAR', 'fid': '6FC4', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PNN', 'name': 'EF.PNN', 'fid': '6FC5', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.OPL', 'name': 'EF.OPL', 'fid': '6FC6', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MBDN', 'name': 'EF.MBDN', 'fid': '6FC7', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT6', 'name': 'EF.EXT6', 'fid': '6FC8', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MBI', 'name': 'EF.MBI', 'fid': '6FC9', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MWIS', 'name': 'EF.MWIS', 'fid': '6FCA', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.CFIS', 'name': 'EF.CFIS', 'fid': '6FCB', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT7', 'name': 'EF.EXT7', 'fid': '6FCC', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SPDI', 'name': 'EF.SPDI', 'fid': '6FCD', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.MMSN', 'name': 'EF.MMSN', 'fid': '6FCE', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EXT8', 'name': 'EF.EXT8', 'fid': '6FCF', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MMSICP', 'name': 'EF.MMSICP', 'fid': '6FD0', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.MMSUP', 'name': 'EF.MMSUP', 'fid': '6FD1', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.MMSUCP', 'name': 'EF.MMSUCP', 'fid': '6FD2', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.NIA', 'name': 'EF.NIA', 'fid': '6FD3', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EHPLMN', 'name': 'EF.EHPLMN', 'fid': '6FD9', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.EHPLMNPI', 'name': 'EF.EHPLMNPI', 'fid': '6FDB', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.NAFKCA', 'name': 'EF.NAFKCA', 'fid': '6FDD', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.SPNI', 'name': 'EF.SPNI', 'fid': '6FDE', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PNNI', 'name': 'EF.PNNI', 'fid': '6FDF', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.EPSLOCI', 'name': 'EF.EPSLOCI', 'fid': '6FE3', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.EPSNSC', 'name': 'EF.EPSNSC', 'fid': '6FE4', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.UFC', 'name': 'EF.UFC', 'fid': '6FE6', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.NASCONFIG', 'name': 'EF.NASCONFIG', 'fid': '6FE8', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.PWS', 'name': 'EF.PWS', 'fid': '6FEC', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.IPS', 'name': 'EF.IPS', 'fid': '6FF1', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/EF.ePDGId', 'name': 'EF.ePDGId', 'fid': '6FF3', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.ePDGSelection', 'name': 'EF.ePDGSelection', 'fid': '6FF4', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.FromPreferred', 'name': 'EF.FromPreferred', 'fid': '6FF7', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.IMSConfigData', 'name': 'EF.IMSConfigData', 'fid': '6FF8', 'type': 'EF', 'structure': 'ber_tlv'},
    {'path': 'ADF.USIM/EF.EARFCNList', 'name': 'EF.EARFCNList', 'fid': '6FFD', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/EF.eAKA', 'name': 'EF.eAKA', 'fid': '6F01', 'type': 'EF', 'structure': 'transparent'},

    # ── ADF.USIM / DF.GSM-ACCESS (5F3B) ──
    {'path': 'ADF.USIM/DF.GSM-ACCESS', 'name': 'DF.GSM-ACCESS', 'fid': '5F3B', 'type': 'DF', 'structure': ''},
    {'path': 'ADF.USIM/DF.GSM-ACCESS/EF.Kc', 'name': 'EF.Kc', 'fid': '4F20', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.GSM-ACCESS/EF.KcGPRS', 'name': 'EF.KcGPRS', 'fid': '4F52', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.GSM-ACCESS/EF.CPBCCH', 'name': 'EF.CPBCCH', 'fid': '4F63', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.GSM-ACCESS/EF.InvScan', 'name': 'EF.InvScan', 'fid': '4F64', 'type': 'EF', 'structure': 'transparent'},

    # ── ADF.USIM / DF.HNB (5F50) ──
    {'path': 'ADF.USIM/DF.HNB', 'name': 'DF.HNB', 'fid': '5F50', 'type': 'DF', 'structure': ''},
    {'path': 'ADF.USIM/DF.HNB/EF.ACSGL', 'name': 'EF.ACSGL', 'fid': '4F81', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.HNB/EF.CSGT', 'name': 'EF.CSGT', 'fid': '4F82', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.HNB/EF.HNBN', 'name': 'EF.HNBN', 'fid': '4F83', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.HNB/EF.OCSGL', 'name': 'EF.OCSGL', 'fid': '4F84', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.HNB/EF.OCSGT', 'name': 'EF.OCSGT', 'fid': '4F85', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.HNB/EF.OHNBN', 'name': 'EF.OHNBN', 'fid': '4F86', 'type': 'EF', 'structure': 'linear_fixed'},

    # ── ADF.USIM / DF.5GS (5FC0) ──
    {'path': 'ADF.USIM/DF.5GS', 'name': 'DF.5GS', 'fid': '5FC0', 'type': 'DF', 'structure': ''},
    {'path': 'ADF.USIM/DF.5GS/EF.5GS3GPPLOCI', 'name': 'EF.5GS3GPPLOCI', 'fid': '4F01', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GSN3GPPLOCI', 'name': 'EF.5GSN3GPPLOCI', 'fid': '4F02', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GS3GPPNSC', 'name': 'EF.5GS3GPPNSC', 'fid': '4F03', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GSN3GPPNSC', 'name': 'EF.5GSN3GPPNSC', 'fid': '4F04', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GAUTHKEYS', 'name': 'EF.5GAUTHKEYS', 'fid': '4F05', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.UAC_AIC', 'name': 'EF.UAC_AIC', 'fid': '4F06', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.SUCI_Calc_Info', 'name': 'EF.SUCI_Calc_Info', 'fid': '4F07', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.OPL5G', 'name': 'EF.OPL5G', 'fid': '4F08', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.5GS/EF.SUPI_NAI', 'name': 'EF.SUPI_NAI', 'fid': '4F09', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.Routing_Indicator', 'name': 'EF.Routing_Indicator', 'fid': '4F0A', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.URSP', 'name': 'EF.URSP', 'fid': '4F0B', 'type': 'EF', 'structure': 'ber_tlv'},
    {'path': 'ADF.USIM/DF.5GS/EF.TN3GPPSNN', 'name': 'EF.TN3GPPSNN', 'fid': '4F0C', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.CAG', 'name': 'EF.CAG', 'fid': '4F0D', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.SOR-CMCI', 'name': 'EF.SOR-CMCI', 'fid': '4F0E', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.DRI', 'name': 'EF.DRI', 'fid': '4F0F', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GSEDRX', 'name': 'EF.5GSEDRX', 'fid': '4F10', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.5GNSWO_CONF', 'name': 'EF.5GNSWO_CONF', 'fid': '4F11', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.MCHPPLMN', 'name': 'EF.MCHPPLMN', 'fid': '4F15', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.5GS/EF.KAUSF_DERIVATION', 'name': 'EF.KAUSF_DERIVATION', 'fid': '4F16', 'type': 'EF', 'structure': 'transparent'},

    # ── ADF.USIM / DF.PHONEBOOK (5F3A) ──
    {'path': 'ADF.USIM/DF.PHONEBOOK', 'name': 'DF.PHONEBOOK', 'fid': '5F3A', 'type': 'DF', 'structure': ''},
    {'path': 'ADF.USIM/DF.PHONEBOOK/EF.PBR', 'name': 'EF.PBR', 'fid': '4F30', 'type': 'EF', 'structure': 'linear_fixed'},
    {'path': 'ADF.USIM/DF.PHONEBOOK/EF.PSC', 'name': 'EF.PSC', 'fid': '4F22', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.PHONEBOOK/EF.CC', 'name': 'EF.CC', 'fid': '4F23', 'type': 'EF', 'structure': 'transparent'},
    {'path': 'ADF.USIM/DF.PHONEBOOK/EF.PUID', 'name': 'EF.PUID', 'fid': '4F24', 'type': 'EF', 'structure': 'transparent'},

    # ── ADF.ISIM — NOT accessible via AT+CRSM (FIDs overlap with USIM) ──
    # {'path': 'ADF.ISIM/EF.IMPI', 'name': 'EF.IMPI', 'fid': '6F02', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.DOMAIN', 'name': 'EF.DOMAIN', 'fid': '6F03', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.IMPU', 'name': 'EF.IMPU', 'fid': '6F04', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.AD', 'name': 'EF.AD', 'fid': '6FAD', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.ARR', 'name': 'EF.ARR', 'fid': '6F06', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.IST', 'name': 'EF.IST', 'fid': '6F07', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.P-CSCF', 'name': 'EF.P-CSCF', 'fid': '6F09', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.GBABP', 'name': 'EF.GBABP', 'fid': '6FD5', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.GBANL', 'name': 'EF.GBANL', 'fid': '6FD7', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.NAFKCA', 'name': 'EF.NAFKCA', 'fid': '6FDD', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.SMS', 'name': 'EF.SMS', 'fid': '6F3C', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.SMSS', 'name': 'EF.SMSS', 'fid': '6F43', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.SMSR', 'name': 'EF.SMSR', 'fid': '6F47', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.SMSP', 'name': 'EF.SMSP', 'fid': '6F42', 'type': 'EF', 'structure': 'linear_fixed'},
    # {'path': 'ADF.ISIM/EF.FromPreferred', 'name': 'EF.FromPreferred', 'fid': '6FF7', 'type': 'EF', 'structure': 'transparent'},
    # {'path': 'ADF.ISIM/EF.IMSConfigData', 'name': 'EF.IMSConfigData', 'fid': '6FF8', 'type': 'EF', 'structure': 'ber_tlv'},
    # {'path': 'ADF.ISIM/EF.UICCIARI', 'name': 'EF.UICCIARI', 'fid': '6FE7', 'type': 'EF', 'structure': 'linear_fixed'},
]


def build_file_tree() -> list[dict]:
    """Convert SIM_FILES into a flat tree structure.
    Each node: {name, fid, type, structure, path}"""
    tree = []
    # Group by top-level
    groups = {}  # 'MF', 'ADF.USIM'
    for f in SIM_FILES:
        parts = f['path'].split('/')
        group = parts[0]
        if group not in groups:
            groups[group] = []
        groups[group].append(f)

    for group_name in ['MF', 'ADF.USIM']:
        if group_name not in groups:
            continue
        files = groups[group_name]
        for f in files:
            tree.append({
                'path': f['path'],
                'name': f['name'],
                'fid': f['fid'],
                'type': f['type'],
                'structure': f['structure'],
            })
    return tree


def get_file_by_path(path: str) -> dict | None:
    """Look up file info by path."""
    for f in SIM_FILES:
        if f['path'] == path:
            return f
    return None


def get_file_by_fid(fid: str) -> list[dict]:
    """FID로 파일 정보 조회 (동일 FID 여러 개 가능)."""
    fid_upper = fid.upper()
    return [f for f in SIM_FILES if f['fid'].upper() == fid_upper]
