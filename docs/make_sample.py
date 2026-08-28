# -*- coding: utf-8 -*-
"""Seeded random sample. Not head() - the file is state-sorted, so head is all Alabama."""
import csv, random, sys

csv.field_size_limit(10_000_000)
random.seed(20260828)

N = 300
with open("nh_full.csv", newline="", encoding="utf-8", errors="replace") as f:
    r = csv.reader(f)
    header = next(r)
    # reservoir sample
    res = []
    for i, row in enumerate(r):
        if len(res) < N:
            res.append(row)
        else:
            j = random.randint(0, i)
            if j < N:
                res[j] = row

with open("sample_300.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(res)

# facts about THIS sample, for scoring later
states = {row[header.index("State")] for row in res}
ccns = {row[header.index("CMS Certification Number (CCN)")] for row in res}
names = {row[header.index("Provider Name")] for row in res}
corrected = {row[header.index("Deficiency Corrected")] for row in res}
sd_i = header.index("Survey Date")
cd_i = header.index("Correction Date")
anom = [row for row in res if row[cd_i] and row[sd_i] and row[cd_i] < row[sd_i]]

print("sample rows:", len(res))
print("distinct states:", len(states))
print("distinct CCN:", len(ccns))
print("distinct provider names:", len(names))
print("distinct 'Deficiency Corrected':", len(corrected))
print("  values:", sorted(corrected))
print("rows w/ Correction Date BEFORE Survey Date:", len(anom))
import os
print("bytes:", os.path.getsize("sample_300.csv"))
