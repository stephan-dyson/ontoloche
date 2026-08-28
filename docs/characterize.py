# -*- coding: utf-8 -*-
"""Mechanical ground truth over the FULL CMS citations file.
Every number printed here is counted, not sampled. Method is the code itself."""
import csv, sys, json, collections

PATH = "nh_full.csv"
csv.field_size_limit(10_000_000)

rows = 0
ccn_names = collections.defaultdict(set)     # CCN -> set of names seen
name_ccns = collections.defaultdict(set)     # name -> set of CCNs
lowcard = {}                                 # col -> Counter (only if stays small)
LOWCARD_COLS = [
    "Survey Type", "Deficiency Prefix", "Deficiency Category", "Scope Severity Code",
    "Deficiency Corrected", "Inspection Cycle", "Standard Deficiency",
    "Complaint Deficiency", "Infection Control Inspection Deficiency",
    "Citation under IDR", "Citation under IIDR", "Processing Date",
]
for c in LOWCARD_COLS:
    lowcard[c] = collections.Counter()

corr_before_survey = 0
corr_present = 0
loc_matches = 0
loc_present = 0
blank_counts = collections.Counter()
tag_desc = collections.defaultdict(set)      # tag number -> set of descriptions

with open(PATH, newline="", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    cols = r.fieldnames
    for row in r:
        rows += 1
        ccn = (row.get("CMS Certification Number (CCN)") or "").strip()
        nm = (row.get("Provider Name") or "").strip()
        if ccn:
            ccn_names[ccn].add(nm)
        if nm:
            name_ccns[nm].add(ccn)
        for c in LOWCARD_COLS:
            v = (row.get(c) or "").strip()
            if len(lowcard[c]) < 400:
                lowcard[c][v] += 1
        sd = (row.get("Survey Date") or "").strip()
        cd = (row.get("Correction Date") or "").strip()
        if cd:
            corr_present += 1
            if sd and cd < sd:
                corr_before_survey += 1
        # Location redundancy
        loc = (row.get("Location") or "").strip()
        if loc:
            loc_present += 1
            built = ",".join([
                (row.get("Provider Address") or "").strip(),
                (row.get("City/Town") or "").strip(),
                (row.get("State") or "").strip(),
                (row.get("ZIP Code") or "").strip(),
            ])
            if loc == built:
                loc_matches += 1
        for c in cols:
            if not (row.get(c) or "").strip():
                blank_counts[c] += 1
        tag = (row.get("Deficiency Tag Number") or "").strip()
        desc = (row.get("Deficiency Description") or "").strip()
        if tag and len(tag_desc[tag]) < 6:
            tag_desc[tag].add(desc)

out = {}
out["total_rows"] = rows
out["columns"] = cols
out["distinct_CCN"] = len(ccn_names)
out["distinct_provider_names"] = len(name_ccns)
out["CCN_with_multiple_names"] = sum(1 for v in ccn_names.values() if len(v) > 1)
out["name_shared_by_multiple_CCN"] = sum(1 for v in name_ccns.values() if len(v) > 1)
out["correction_date_present"] = corr_present
out["correction_before_survey"] = corr_before_survey
out["correction_before_survey_pct"] = round(100.0 * corr_before_survey / corr_present, 3) if corr_present else None
out["location_present"] = loc_present
out["location_exactly_rebuilt_from_4_cols"] = loc_matches
out["location_redundant_pct"] = round(100.0 * loc_matches / loc_present, 3) if loc_present else None
out["distinct_tag_numbers"] = len(tag_desc)
out["tags_with_multiple_descriptions"] = sum(1 for v in tag_desc.values() if len(v) > 1)
out["blank_by_column"] = dict(blank_counts.most_common())
out["lowcard"] = {c: dict(lowcard[c].most_common(12)) for c in LOWCARD_COLS}

# examples of CCN with name variants
ex = [(k, sorted(v)) for k, v in ccn_names.items() if len(v) > 1][:5]
out["example_CCN_name_variants"] = ex

with open("ground_truth_mechanical.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)

print(json.dumps({k: v for k, v in out.items()
                  if k not in ("blank_by_column", "lowcard", "columns", "example_CCN_name_variants")}, indent=1))
print("\n-- Deficiency Corrected --")
print(json.dumps(out["lowcard"]["Deficiency Corrected"], indent=1))
print("\n-- Scope Severity Code (top 12) --")
print(json.dumps(out["lowcard"]["Scope Severity Code"], indent=1))
print("\n-- CCN name variants (examples) --")
for k, v in ex:
    print(" ", k, "->", v)
