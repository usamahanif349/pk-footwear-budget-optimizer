#!/usr/bin/env python3
# REDUCE: input arrives sorted by key; add up the 5 sums per key.
import sys
cur, acc = None, [0, 0, 0, 0, 0]
for line in sys.stdin:
    key, vals = line.rstrip("\n").split("\t")
    v = [int(x) for x in vals.split(",")]
    if key != cur:
        if cur is not None:
            sys.stdout.write(cur + "\t" + ",".join(map(str, acc)) + "\n")
        cur, acc = key, [0, 0, 0, 0, 0]
    acc = [a + b for a, b in zip(acc, v)]
if cur is not None:
    sys.stdout.write(cur + "\t" + ",".join(map(str, acc)) + "\n")
