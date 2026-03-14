import struct

with open('PPSA17221-fixed.exfat', 'rb') as f:
    boot = f.read(512)

with open('PPSA17221-official.exfat', 'rb') as f:
    off_boot = f.read(512)

fields = [
    ('FAT Length', 84, 88),
    ('Heap Offset', 88, 92),
    ('Cluster Count', 92, 96),
    ('Root Cluster', 96, 100),
]

print('Geometry Comparison:')
print('=' * 60)
all_match = True
for name, start, end in fields:
    py_val = struct.unpack('<I', boot[start:end])[0]
    off_val = struct.unpack('<I', off_boot[start:end])[0]
    match = py_val == off_val
    all_match = all_match and match
    status = 'OK' if match else 'DIFF'
    print(f'{name:20} | Py:{py_val:<8} | Off:{off_val:<8} | {status}')

print('=' * 60)
if all_match:
    print('SUCCESS: ALL FIELDS MATCH!')
else:
    print('GEOMETRY STILL DIFFERS')
