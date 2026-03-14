#!/usr/bin/env python3
import zstandard as z

data = open('test-original-case.exfat', 'rb').read()
compressed = z.ZstdCompressor(level=22).compress(data)
open('test-original-case.exfat.zst', 'wb').write(compressed)

print(f'Original: {len(data)} bytes')
print(f'Compressed: {len(compressed)} bytes')
print(f'Ratio: {100*len(compressed)/len(data):.1f}%')
