import numpy as np, pandas as pd, os, sys

rng = np.random.default_rng(2026)
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

START, END = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-09-30")
MONTHS = pd.date_range(START, END, freq="MS")
FEE = 80

# ---------------- Dimensions ----------------
dates = pd.DataFrame({"Date": pd.date_range(START, END, freq="D")})
dates["Year"] = dates.Date.dt.year
dates["Quarter"] = "Q" + dates.Date.dt.quarter.astype(str)
dates["YearQuarter"] = dates.Year.astype(str) + "-" + dates.Quarter
dates["QuarterIndex"] = (dates.Year - 2025) * 4 + dates.Date.dt.quarter
dates["MonthNum"] = dates.Date.dt.month
dates["MonthName"] = dates.Date.dt.strftime("%b")
dates["YearMonth"] = dates.Date.dt.strftime("%Y-%m")
dates["MonthStart"] = dates.Date.dt.to_period("M").dt.start_time
dates["DayOfWeek"] = dates.Date.dt.day_name()
dates["IsWeekend"] = dates.Date.dt.dayofweek >= 5

employers = pd.DataFrame([
    ("E001", "Summit Logistics", "Warehousing", "CO", "2025-01-01", 420, 0.70, 1.00),
    ("E002", "Front Range Beverage Co.", "Beverage Distribution", "CO", "2025-01-01", 260, 0.66, 1.05),
    ("E003", "Desert Sun Distribution", "Warehousing", "AZ", "2025-04-01", 350, 0.62, 0.95),
    ("E004", "Lone Star Brew Distributors", "Beverage Distribution", "TX", "2025-07-01", 300, 0.60, 0.90),
    ("E005", "Peak Freight Partners", "Freight & Logistics", "TX", "2026-01-01", 180, 0.58, 0.85),
], columns=["EmployerID", "EmployerName", "Industry", "State", "ContractStartDate",
            "BaseEligible", "EnrollRate", "UseFactor"])
employers["ContractStartDate"] = pd.to_datetime(employers.ContractStartDate)
employers["MonthlyFeePerMember"] = FEE

locations = pd.DataFrame([
    ("L00", "Virtual Care", "Virtual", "", None),
    ("L01", "Colorado Springs Clinic", "Public Clinic", "CO", None),
    ("L02", "Arizona Clinic", "Public Clinic", "AZ", None),
    ("L03", "Texas Clinic", "Public Clinic", "TX", None),
    ("L04", "Summit Logistics Onsite", "Embedded Clinic", "CO", "E001"),
    ("L05", "Front Range Beverage Onsite", "Embedded Clinic", "CO", "E002"),
    ("L06", "Desert Sun Onsite", "Embedded Clinic", "AZ", "E003"),
    ("L07", "Lone Star Brew Onsite", "Embedded Clinic", "TX", "E004"),
], columns=["LocationID", "LocationName", "LocationType", "State", "HostEmployerID"])
public_by_state = {"CO": "L01", "AZ": "L02", "TX": "L03"}
embedded_by_emp = {"E001": "L04", "E002": "L05", "E003": "L06", "E004": "L07"}

reasons = pd.DataFrame([
    ("R01", "Acute Illness (cold, flu, infection)", 0.26),
    ("R02", "Injury / Musculoskeletal", 0.14),
    ("R03", "Chronic Disease Management", 0.16),
    ("R04", "Preventive / Screening", 0.10),
    ("R05", "Mental & Behavioral Health", 0.08),
    ("R06", "Skin Condition", 0.06),
    ("R07", "Weight Management", 0.07),
    ("R08", "Hormone Therapy", 0.04),
    ("R09", "Medication Refill / Follow-up", 0.09),
], columns=["ReasonID", "VisitReason", "Weight"])

# Where the member would have gone without the clinic -> benchmark lookup
benchmarks = pd.DataFrame([
    ("Emergency Room", 1800),
    ("Urgent Care", 200),
    ("Specialist", 350),
    ("Imaging", 450),
    ("Primary Care Office Visit", 150),
    ("Virtual Primary Care", 80),
], columns=["AvoidedCareCategory", "BenchmarkCost"])
avoid_map = {
    "R01": (["Urgent Care", "Emergency Room", "Primary Care Office Visit"], [0.60, 0.08, 0.32]),
    "R02": (["Emergency Room", "Urgent Care", "Imaging", "Specialist", "Primary Care Office Visit"], [0.14, 0.34, 0.20, 0.14, 0.18]),
    "R03": (["Specialist", "Primary Care Office Visit"], [0.30, 0.70]),
    "R04": (["Primary Care Office Visit", "Imaging"], [0.85, 0.15]),
    "R05": (["Specialist", "Primary Care Office Visit"], [0.45, 0.55]),
    "R06": (["Specialist", "Primary Care Office Visit"], [0.40, 0.60]),
    "R07": (["Specialist", "Primary Care Office Visit"], [0.35, 0.65]),
    "R08": (["Specialist", "Primary Care Office Visit"], [0.50, 0.50]),
    "R09": (["Primary Care Office Visit"], [1.0]),
}
cpt_by_type = {
    "In-Person": (["99213", "99214", "99203", "99395"], [0.50, 0.25, 0.15, 0.10]),
    "Telehealth": (["99213-95", "99214-95"], [0.75, 0.25]),
    "Call/Text": (["99441", "98970"], [0.6, 0.4]),
}

meds = pd.DataFrame([
    # id, name, class, generic, included_in_membership, retail, wholesale
    ("M01", "Amoxicillin 500mg", "Antibiotic", True, True, 18, 3),
    ("M02", "Azithromycin 250mg", "Antibiotic", True, True, 25, 4),
    ("M03", "Prednisone 10mg", "Corticosteroid", True, True, 15, 2),
    ("M04", "Ibuprofen 800mg", "NSAID", True, True, 14, 2),
    ("M05", "Cyclobenzaprine 10mg", "Muscle Relaxant", True, True, 22, 3),
    ("M06", "Benzonatate 100mg", "Antitussive", True, True, 28, 4),
    ("M07", "Lisinopril 20mg", "Antihypertensive", True, True, 16, 2),
    ("M08", "Amlodipine 10mg", "Antihypertensive", True, True, 20, 2),
    ("M09", "Metformin 1000mg", "Antidiabetic", True, True, 19, 3),
    ("M10", "Atorvastatin 40mg", "Statin", True, True, 30, 3),
    ("M11", "Levothyroxine 50mcg", "Thyroid", True, True, 24, 4),
    ("M12", "Sertraline 50mg", "SSRI", True, True, 27, 3),
    ("M13", "Bupropion XL 150mg", "Antidepressant", True, True, 45, 6),
    ("M14", "Omeprazole 20mg", "PPI", True, True, 26, 3),
    ("M15", "Triamcinolone Cream 0.1%", "Topical Steroid", True, True, 32, 5),
    ("M16", "Montelukast 10mg", "Asthma", True, True, 35, 4),
    ("M17", "Albuterol HFA Inhaler", "Asthma", True, False, 70, 24),
    ("M18", "Fluticasone Nasal Spray", "Allergy", True, False, 38, 9),
    ("M19", "Testosterone Cypionate 200mg/mL", "Hormone", True, False, 95, 32),
    ("M20", "Estradiol 1mg", "Hormone", True, False, 48, 12),
    ("M21", "Semaglutide (compounded) 4-week", "GLP-1 Weight Mgmt", False, False, 1050, 290),
    ("M22", "Tirzepatide (compounded) 4-week", "GLP-1 Weight Mgmt", False, False, 1120, 330),
    ("M23", "Apixaban 5mg", "Anticoagulant", False, False, 560, 210),
    ("M24", "Insulin Glargine Pen", "Insulin", False, False, 420, 140),
    ("M25", "Rizatriptan 10mg", "Migraine", True, False, 85, 22),
], columns=["MedicationID", "MedicationName", "DrugClass", "IsGeneric",
            "IncludedInMembership", "RetailPricePerFill", "WholesalePricePerFill"])
acute_meds = {"R01": ["M01", "M02", "M03", "M06", "M18"],
              "R02": ["M04", "M05", "M03"],
              "R06": ["M15", "M03"]}

labs = pd.DataFrame([
    ("T01", "Complete Blood Count (CBC)", 45),
    ("T02", "Comprehensive Metabolic Panel", 60),
    ("T03", "Lipid Panel", 55),
    ("T04", "Hemoglobin A1c", 50),
    ("T05", "Thyroid Panel (TSH)", 65),
    ("T06", "Vitamin D", 90),
    ("T07", "Testosterone, Total", 110),
    ("T08", "Strep / Flu Rapid Test", 40),
    ("T09", "Urinalysis", 30),
], columns=["LabTestID", "LabTestName", "RetailPrice"])
labs_by_reason = {"R01": ["T08", "T01"], "R02": ["T01"], "R03": ["T02", "T03", "T04"],
                  "R04": ["T01", "T02", "T03", "T05", "T06"], "R05": ["T05"],
                  "R07": ["T02", "T03", "T04"], "R08": ["T07", "T02"], "R09": ["T02", "T09"]}

providers = pd.DataFrame([
    ("P01", "Provider A", "Family Nurse Practitioner"),
    ("P02", "Provider B", "Physician Assistant"),
    ("P03", "Provider C", "Physician (MD)"),
], columns=["ProviderID", "ProviderName", "Credential"])

# ---------------- Members & eligibility ----------------
members, elig_rows = [], []
mid = 1
for _, e in employers.iterrows():
    contract_months = [m for m in MONTHS if m >= e.ContractStartDate]
    # Paycom eligible headcount: slow growth + noise
    base = e.BaseEligible
    for i, m in enumerate(contract_months):
        elig = int(round(base * (1 + 0.004 * i) + rng.normal(0, base * 0.01)))
        elig_rows.append((e.EmployerID, m, elig))
    max_elig = max(r[2] for r in elig_rows if r[0] == e.EmployerID)
    n_emp = int(max_elig * e.EnrollRate)
    for k in range(n_emp):
        # most enroll at launch, others trickle in
        if rng.random() < 0.65:
            enroll = e.ContractStartDate
        else:
            enroll = rng.choice(contract_months)
        term = pd.NaT
        if rng.random() < 0.14:  # some leave the employer
            later = [m for m in contract_months if m > enroll]
            if later:
                term = rng.choice(later) - pd.Timedelta(days=1)
        age = int(np.clip(rng.normal(39, 11), 19, 66))
        sub_id = f"MBR{mid:05d}"
        members.append((sub_id, e.EmployerID, "Employee", sub_id, age,
                        rng.choice(["Male", "Female"], p=[0.62, 0.38]), enroll, term))
        mid += 1
        for _ in range(rng.choice([0, 1, 2, 3], p=[0.55, 0.22, 0.15, 0.08])):
            rel = "Spouse" if rng.random() < 0.45 else "Child"
            dage = int(np.clip(age + rng.normal(0, 4), 19, 66)) if rel == "Spouse" else int(rng.integers(1, 18))
            members.append((f"MBR{mid:05d}", e.EmployerID, rel, sub_id, dage,
                            rng.choice(["Male", "Female"]), enroll, term))
            mid += 1

dim_member = pd.DataFrame(members, columns=["MemberID", "EmployerID", "Relationship",
                                            "SubscriberID", "Age", "Sex", "EnrollDate", "TermDate"])
def band(a):
    for lo, hi, lab in [(0, 17, "0-17"), (18, 29, "18-29"), (30, 39, "30-39"),
                        (40, 49, "40-49"), (50, 64, "50-64")]:
        if lo <= a <= hi: return lab
    return "65+"
dim_member["AgeBand"] = dim_member.Age.map(band)
dim_member["HomeState"] = dim_member.EmployerID.map(employers.set_index("EmployerID").State)
# chronic / program flags drive Rx and visit reasons
dim_member["HasChronicCondition"] = (rng.random(len(dim_member)) < np.where(dim_member.Age >= 40, 0.38, 0.12))
adult = dim_member.Age >= 18
dim_member["InWeightProgram"] = adult & (rng.random(len(dim_member)) < 0.03)
dim_member["InHormoneProgram"] = adult & (dim_member.Age >= 30) & (rng.random(len(dim_member)) < 0.04)

# Member-months (enrolled each month)
mm = []
for r in dim_member.itertuples():
    for m in MONTHS:
        m_end = m + pd.offsets.MonthEnd(0)
        if r.EnrollDate <= m and (pd.isna(r.TermDate) or r.TermDate >= m_end):
            mm.append((r.MemberID, r.EmployerID, m, r.Relationship))
fact_mm = pd.DataFrame(mm, columns=["MemberID", "EmployerID", "MonthStart", "Relationship"])
fact_mm["MembershipFee"] = FEE

elig = pd.DataFrame(elig_rows, columns=["EmployerID", "MonthStart", "EligibleEmployees"])
enrolled = fact_mm.groupby(["EmployerID", "MonthStart"]).agg(
    EnrolledMembers=("MemberID", "count"),
    EnrolledEmployees=("Relationship", lambda s: (s == "Employee").sum())).reset_index()
elig = elig.merge(enrolled, on=["EmployerID", "MonthStart"], how="left").fillna(0)
elig["SourceSystem"] = "Paycom"
elig["FeedLoadedDate"] = (elig.MonthStart + pd.Timedelta(days=3)).dt.date
# Planted data-quality issue: Desert Sun's Paycom feed missed Aug 2026
elig = elig[~((elig.EmployerID == "E003") & (elig.MonthStart == "2026-08-01"))]

# ---------------- Visits, Rx, Labs ----------------
emp = employers.set_index("EmployerID")
mem = dim_member.set_index("MemberID")
visits, fills, labrows = [], [], []
vid = fid = lid = 1
reason_ids, reason_w = reasons.ReasonID.values, reasons.Weight.values / reasons.Weight.sum()

for r in fact_mm.itertuples():
    m = r.MonthStart
    e = emp.loc[r.EmployerID]
    mrow = mem.loc[r.MemberID]
    tenure = (m.year - e.ContractStartDate.year) * 12 + m.month - e.ContractStartDate.month
    season = {1: 1.45, 2: 1.30, 3: 1.10, 12: 1.15}.get(m.month, 1.0)
    if m == pd.Timestamp("2026-01-01"): season = 1.75          # flu spike anomaly
    ramp = min(1.0, 0.55 + 0.09 * tenure)                       # new contracts ramp up
    rate = 0.44 * e.UseFactor * season * ramp
    if mrow.HasChronicCondition: rate *= 1.5
    if mrow.InWeightProgram or mrow.InHormoneProgram: rate *= 1.3
    n = rng.poisson(rate)
    q3_2026_drop = (r.EmployerID == "E002" and m >= pd.Timestamp("2026-07-01"))
    days = (m + pd.offsets.MonthEnd(0)).day
    for _ in range(n):
        vt = rng.choice(["In-Person", "Telehealth", "Call/Text"], p=[0.56, 0.26, 0.18])
        if q3_2026_drop and vt == "Telehealth" and rng.random() < 0.70:
            continue  # telehealth engagement collapse at Employer B
        if q3_2026_drop and vt != "Telehealth" and rng.random() < 0.12:
            continue
        w = reason_w.copy()
        if mrow.HasChronicCondition: w[2] *= 3; w[8] *= 2
        if mrow.InWeightProgram: w[6] *= 8
        if mrow.InHormoneProgram: w[7] *= 8
        if m.month in (1, 2, 12): w[0] *= 1.8
        rid = rng.choice(reason_ids, p=w / w.sum())
        d = m + pd.Timedelta(days=int(rng.integers(0, days)))
        if vt == "In-Person":
            st = mrow.HomeState
            loc = embedded_by_emp.get(r.EmployerID) if (r.EmployerID in embedded_by_emp and rng.random() < 0.72) else public_by_state[st]
            cats, p = avoid_map[rid]
            cat = rng.choice(cats, p=p)
        else:
            loc = "L00"
            if vt == "Telehealth":
                cats, p = avoid_map[rid]
                cat = rng.choice(cats, p=p)
                if cat in ("Imaging", "Emergency Room"): cat = "Urgent Care"
            else:
                cat = "Virtual Primary Care"
        cpts, cp = cpt_by_type[vt]
        cpt = "99395" if (vt == "In-Person" and rid == "R04") else rng.choice(cpts, p=cp)
        prov = rng.choice(providers.ProviderID, p=[0.55, 0.30, 0.15])
        sameday = rng.random() < (0.78 if vt != "In-Person" else 0.62)
        visit_id = f"V{vid:06d}"; vid += 1
        visits.append((visit_id, d.date(), r.MemberID, r.EmployerID, loc, prov, vt, rid, cpt,
                       cat, "Same Day" if sameday else "Next Day"))
        # acute prescription
        if rid in acute_meds and rng.random() < 0.55:
            med = rng.choice(acute_meds[rid])
            fills.append((f"F{fid:06d}", d.date(), r.MemberID, r.EmployerID, med, 1, visit_id)); fid += 1
        # labs
        if vt == "In-Person" and rid in labs_by_reason and rng.random() < 0.55:
            for t in rng.choice(labs_by_reason[rid], size=min(len(labs_by_reason[rid]), int(rng.integers(1, 4))), replace=False):
                labrows.append((f"LB{lid:06d}", d.date(), r.MemberID, r.EmployerID, t, visit_id)); lid += 1

    # monthly maintenance fills
    fd = (m + pd.Timedelta(days=int(rng.integers(0, days)))).date()
    if mrow.HasChronicCondition:
        h = int(r.MemberID[3:]) % 1000
        regimen = [["M07", "M10"], ["M09", "M08"], ["M11"], ["M12", "M14"], ["M13"], ["M16", "M17"],
                   ["M09", "M24"], ["M23", "M07"], ["M10", "M25"], ["M08", "M10", "M09"]][h % 10]
        for med in regimen:
            if rng.random() < 0.85:
                fills.append((f"F{fid:06d}", fd, r.MemberID, r.EmployerID, med, 1, None)); fid += 1
    if mrow.InWeightProgram and rng.random() < 0.80:
        med = "M21" if int(r.MemberID[3:]) % 3 else "M22"
        fills.append((f"F{fid:06d}", fd, r.MemberID, r.EmployerID, med, 1, None)); fid += 1
    if mrow.InHormoneProgram and rng.random() < 0.85:
        med = "M19" if mrow.Sex == "Male" else "M20"
        fills.append((f"F{fid:06d}", fd, r.MemberID, r.EmployerID, med, 1, None)); fid += 1

fact_visits = pd.DataFrame(visits, columns=["VisitID", "VisitDate", "MemberID", "EmployerID",
    "LocationID", "ProviderID", "VisitType", "ReasonID", "CPTCode", "AvoidedCareCategory", "AccessTiming"])
fact_rx = pd.DataFrame(fills, columns=["FillID", "FillDate", "MemberID", "EmployerID",
                                       "MedicationID", "Quantity", "VisitID"])
md = meds.set_index("MedicationID")
fact_rx["RetailPrice"] = fact_rx.MedicationID.map(md.RetailPricePerFill)
fact_rx["PricePaid"] = np.where(fact_rx.MedicationID.map(md.IncludedInMembership), 0,
                                fact_rx.MedicationID.map(md.WholesalePricePerFill))
fact_labs = pd.DataFrame(labrows, columns=["LabOrderID", "LabDate", "MemberID", "EmployerID", "LabTestID", "VisitID"])

# ---------------- RLS, targets ----------------
user_access = pd.DataFrame([
    ("hr.benefits@summitlogistics.example", "E001"),
    ("benefits@frontrangebev.example", "E002"),
    ("hr@desertsundist.example", "E003"),
    ("people@lonestarbrew.example", "E004"),
    ("hr@peakfreight.example", "E005"),
    ("cfo@summitlogistics.example", "E001"),
], columns=["UserEmail", "EmployerID"])
targets = pd.DataFrame([
    ("ROI Multiple", 2.0, "x", "Leadership target"),
    ("Engagement Rate", 0.70, "%", "Active patients in quarter / avg enrolled members"),
    ("Traditional Insurance Cost PMPM", 600, "$", "Assumed employer cost per member per month under traditional insurance"),
    ("Membership Fee PMPM", 80, "$", "Flat monthly membership"),
], columns=["Metric", "TargetValue", "Unit", "Note"])

# ---------------- Write ----------------
out = {
    "DimDate": dates, "DimEmployer": employers.drop(columns=["BaseEligible", "EnrollRate", "UseFactor"]),
    "DimLocation": locations, "DimMember": dim_member.drop(columns=["Age"]), "DimProvider": providers,
    "DimVisitReason": reasons.drop(columns=["Weight"]), "DimMedication": meds, "DimLabTest": labs,
    "BenchmarkAvoidedCare": benchmarks, "Targets": targets, "UserAccess": user_access,
    "FactEligibility": elig, "FactMemberMonths": fact_mm, "FactVisits": fact_visits,
    "FactPrescriptions": fact_rx, "FactLabs": fact_labs,
}
for name, df in out.items():
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
    print(f"{name:22s} {len(df):>7,} rows")
