#!/usr/bin/env python3
"""Pack out/desktop/icon-*.png into app.ico (Windows, PNG entries) and app.icns (macOS, PNG entries)."""
import os, struct
here = os.path.dirname(os.path.abspath(__file__))
png = lambda s: open(f'{here}/out/desktop/icon-{s}.png', 'rb').read()

ico_sizes = [16, 32, 48, 64, 128, 256]
blobs = [png(s) for s in ico_sizes]
out = struct.pack('<HHH', 0, 1, len(blobs))
off = 6 + 16 * len(blobs)
for s, d in zip(ico_sizes, blobs):
    out += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(d), off)
    off += len(d)
open(f'{here}/out/desktop/app.ico', 'wb').write(out + b''.join(blobs))

# icp4 16, icp5 32, icp6 64, ic07 128, ic08 256, ic09 512, ic10 1024 (retina 512@2x)
icns = [(b'icp4', 16), (b'icp5', 32), (b'icp6', 64), (b'ic07', 128), (b'ic08', 256), (b'ic09', 512), (b'ic10', 1024)]
body = b''.join(t + struct.pack('>I', 8 + len(png(s))) + png(s) for t, s in icns)
open(f'{here}/out/desktop/app.icns', 'wb').write(b'icns' + struct.pack('>I', 8 + len(body)) + body)
print('packed app.ico and app.icns')
