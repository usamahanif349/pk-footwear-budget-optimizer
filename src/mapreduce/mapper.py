#!/usr/bin/env python3
# MAP: read CSV lines, emit key=platform|campaign, value=5 sums.
# Uses the "in-mapper combining" pattern: sums inside each mapper first,
# so far less data goes through the shuffle.
import sys
acc = {}
for line in sys.stdin:
    f = line.rstrip("\n").split(",")
    if f[0] == "date":          # skip header
        continue
    key = f[2] + "|" + f[1]     # platform|campaign
    v = acc.get(key)
    if v is None:
        v = acc[key] = [0, 0, 0, 0, 0]
    v[0] += int(f[3]); v[1] += int(f[4]); v[2] += int(f[5])
    v[3] += int(f[6]); v[4] += int(f[7])
for key, v in acc.items():
    sys.stdout.write(key + "\t" + ",".join(map(str, v)) + "\n")
