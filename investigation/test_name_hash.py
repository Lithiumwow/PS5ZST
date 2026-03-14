#!/usr/bin/env python3
import struct

def _name_hash(enc_name_upper: bytes) -> int:
    """exFAT name hash (spec §6.3.5.1)"""
    h = 0
    for i in range(0, len(enc_name_upper), 2):
        char = struct.unpack('<H', enc_name_upper[i:i+2])[0]
        h = ((h << 15) | (h >> 1)) & 0xFFFF
        h = (h + char) & 0xFFFF
    return h

def _encode_name(name: str) -> bytes:
    return name.encode('utf-16-le')

# Test both cases
name = "param.json"

# Hash using original name
hash_original = _name_hash(_encode_name(name))
print(f"Hash('param.json'): {hex(hash_original)}")

# Hash using uppercase
hash_upper = _name_hash(_encode_name(name.upper()))
print(f"Hash('PARAM.JSON'): {hex(hash_upper)}")

# What we found in images:
# Generated: 0xd99a
# Official:  0xafaa

print(f"\nGenerated image has: 0xd99a")
print(f"Official image has:  0xafaa")
print(f"\nMatch original? Generated={hash_original==0xd99a}, Official={hash_original==0xafaa}")
print(f"Match uppercase? Generated={hash_upper==0xd99a}, Official={hash_upper==0xafaa}")
