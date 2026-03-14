#!/usr/bin/env python3
import struct

def _dir_checksum(dentries: bytes) -> int:
    """Compute checksum for directory entries (skips bytes 2-3 of primary)."""
    csum = 0
    for i, b in enumerate(dentries):
        if i in (2, 3):
            continue
        csum = ((csum << 31) | (csum >> 1)) & 0xFFFFFFFF
        csum = (csum + b) & 0xFFFFFFFF
    return csum & 0xFFFF

# Extract from generated image (all 3 entries)
# File entry: 85021742200000001225785b1225785b1225785b000000000000000000000000
# Stream ext: c003000a9ad900006f0d00000000000000000000c9d100006f0d000000000000
# Name entry: c10070006100720061006d002e006a0073006f006e0000000000000000000000

gen_file_entry = bytes.fromhex('85021742200000001225785b1225785b1225785b000000000000000000000000')
gen_stream_ext = bytes.fromhex('c003000a9ad900006f0d00000000000000000000c9d100006f0d000000000000')
gen_name_entry = bytes.fromhex('c10070006100720061006d002e006a0073006f006e0000000000000000000000')

# Extract from official image
off_file_entry = bytes.fromhex('8502d0662000000034bc6c5c122d785b6b726d5cbb00f0f0f000000000000000')
off_stream_ext = bytes.fromhex('c003000aaaaf00006f0d00000000000000000000c6d100006f0d000000000000')
off_name_entry = bytes.fromhex('c10070006100720061006d002e006a0073006f006e0000000000000000000000')

# Compute checksums (should match bytes 2-3 of file entry)
gen_all = gen_file_entry + gen_stream_ext + gen_name_entry
gen_csum = _dir_checksum(gen_all)
gen_stored = struct.unpack('<H', gen_file_entry[2:4])[0]

off_all = off_file_entry + off_stream_ext + off_name_entry
off_csum = _dir_checksum(off_all)
off_stored = struct.unpack('<H', off_file_entry[2:4])[0]

print("=== GENERATED ===")
print(f"Computed checksum: {hex(gen_csum)}")
print(f"Expected (stored): {hex(gen_stored)}")
print(f"Match: {gen_csum == gen_stored}")

print("\n=== OFFICIAL ===")
print(f"Computed checksum: {hex(off_csum)}")
print(f"Expected (stored): {hex(off_stored)}")
print(f"Match: {off_csum == off_stored}")

print("\n=== ANALYSIS ===")
if gen_csum == gen_stored:
    print("Generated checksum is VALID")
else:
    print(f"Generated checksum is INVALID (computed {hex(gen_csum)}, stored {hex(gen_stored)})")

if off_csum == off_stored:
    print("Official checksum is VALID")
else:
    print(f"Official checksum is INVALID (computed {hex(off_csum)}, stored {hex(off_stored)})")
