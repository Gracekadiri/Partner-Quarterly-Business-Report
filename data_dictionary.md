# Data Dictionary: Partner Quarterly Business Report

This dictionary defines every KPI in the report. If a number in the report and a definition here disagree, the report is fixed to match this document.

> All data is synthetic.

## Conventions

- **Reporting period:** calendar quarter, selected with the Year and Quarter slicers. Data covers January 2025 to September 2026.
- **Partner:** a business that pays for its staff's memberships (stored as `DimEmployer` / `EmployerID` in the model).
- **Counts of people** (eligible staff, staff enrolled, covered members) are taken **at the end of the quarter**.
- **Activity** (visits, members using care, savings) is counted **across the whole quarter**.
- **Currency:** US dollars. Values of $1M or more show as millions, others as thousands.
- **Security:** every KPI is filtered by row-level security, so a partner only ever sees its own data.
- **Check values** are for Q3 2026, all partners, and can be used to validate the report.

---

## Page 1: Utilization

*Answers: are our people using it?*

| KPI | Measure | Definition | Calculation | Source | Q3 2026 |
|---|---|---|---|---|---|
| Eligible staff | `Eligible Employees` | Staff eligible for the membership, as reported by payroll | Eligible headcount in the last month of the quarter | FactEligibility (payroll feed) | 1,615 |
| Staff enrolled | `Enrolled Employees` | Eligible staff who joined | Members with Relationship = Employee, in the last month of the quarter | FactMemberMonths | 892 |
| Enrollment rate | `Enrollment Rate` | Share of eligible staff who joined | Staff enrolled ÷ eligible staff | Measures above | 55.2% |
| Covered members | `Enrolled Members` | Everyone covered: staff and their families | All members in the last month of the quarter | FactMemberMonths | 1,546 |
| Members using care | `Active Patients` | Covered members who received care | Distinct members with at least one visit in the quarter | FactVisits | 1,127 |
| Members not using care | `Members Not Using Care` | Covered members with no visit | Covered members − members using care (minimum 0) | Measures above | 419 |
| Engagement rate | `Engagement Rate` | Share of covered members who used care | Members using care ÷ covered members | Measures above | 72.9% |
| Engagement target | `Engagement Target` | Goal for engagement | Read from the Targets table | Targets | 70% |
| Total visits | `Total Visits` | Number of times care was given | Count of visit rows, all visit types | FactVisits | 2,030 |
| Visits by reason | `Total Visits` by `DimVisitReason[VisitReason]` | What members came in for | Total visits grouped by visit reason | FactVisits, DimVisitReason | Acute illness 481 |
| Visits by type | `Total Visits` by `FactVisits[VisitType]` | How members received care | Total visits grouped by In-Person, Telehealth, Call/Text | FactVisits | 1,189 / 464 / 377 |

**Which members used care** splits members using care and members not using care by member type: Staff, Spouses and Children (`DimMember[Member Type]`).

---

## Page 2: Savings & ROI

*Answers: is this saving us money?*

| KPI | Measure | Definition | Calculation | Source | Q3 2026 |
|---|---|---|---|---|---|
| Membership investment | `Employer Spend` | What partners paid for memberships | Sum of the monthly fee ($80) for every member month | FactMemberMonths | $368,000 |
| Member months | `Member Months` | Total months of membership | Count of member-month rows | FactMemberMonths | 4,600 |
| Avoided outside care costs | `Avoided Care Cost` | Estimated cost of the care members would have used elsewhere | Each visit valued at the benchmark cost of the care it replaced | FactVisits → BenchmarkAvoidedCare | $453,460 |
| Lower prescription prices | `Rx Savings` | Saving from cheaper prescriptions | Pharmacy price − price paid | FactPrescriptions | $168,830 |
| % off pharmacy price | `Rx Savings Rate` | How much cheaper prescriptions were | Rx savings ÷ pharmacy price | FactPrescriptions | 74.2% |
| Included lab tests | `Lab Savings` | Value of lab tests included in the membership | Sum of the retail price of each test ordered | FactLabs → DimLabTest | $55,795 |
| Estimated savings | `Total Savings` | Total value delivered to the partner | Avoided outside care costs + lower prescription prices + included lab tests | Measures above | $678,085 |
| Return on investment | `ROI Multiple` | Value returned for every $1 invested | Estimated savings ÷ membership investment | Measures above | 1.84x |
| ROI target | `ROI Target` | Goal for return on investment | Read from the Targets table | Targets | 2.0x |
| Monthly cost per member | `Cost per Member` | What partners pay per member per month | Membership investment ÷ member months | Measures above | $80 |
| Insurance benchmark | `Insurance Benchmark PMPM` | Assumed monthly cost per member under traditional insurance | Read from the Targets table | Targets | $600 |

**Top 5 prescriptions driving savings** shows, for each medication: pharmacy price (`Rx Retail Value`), price paid (`Rx Price Paid`), saved (`Rx Savings`) and % off pharmacy price (`Rx Savings Rate`), sorted by saved.

---

## Comparisons

Each KPI card shows one comparison:

| Card | Compared to | Why |
|---|---|---|
| Membership investment | Last quarter | Shows membership growth |
| Estimated savings | Last quarter | Shows whether the value delivered is growing |
| Return on investment | 2.0x target | Shows whether the partnership meets its goal |
| Monthly cost per member | $600 insurance benchmark | The fee is fixed, so the benchmark is the meaningful comparison |
| Engagement rate | 70% target | Shows whether enough members are using care |

**Last quarter** is calculated with `DATEADD ( DimDate[Date], -1, QUARTER )` and returns blank unless exactly one quarter is selected.

**Colors:** green for a good change, red for a bad one. Membership investment stays neutral, because higher spend means more members, not a problem. A lower cost per member than the benchmark is green.

---

## Data model

| Table | Type | Grain | Key |
|---|---|---|---|
| FactVisits | Fact | One row per visit | VisitID |
| FactPrescriptions | Fact | One row per prescription fill | FillID |
| FactLabs | Fact | One row per lab test ordered | LabOrderID |
| FactMemberMonths | Fact | One row per member per enrolled month | MemberID + MonthStart |
| FactEligibility | Fact | One row per partner per month (payroll feed) | EmployerID + MonthStart |
| DimDate | Dimension | One row per day | Date |
| DimEmployer | Dimension | One row per partner | EmployerID |
| DimLocation | Dimension | One row per clinic, including Virtual Care | LocationID |
| DimMember | Dimension | One row per member (age band only, no names) | MemberID |
| DimProvider | Dimension | One row per provider | ProviderID |
| DimVisitReason | Dimension | One row per visit reason | ReasonID |
| DimMedication | Dimension | One row per medication, with pharmacy and wholesale price | MedicationID |
| DimLabTest | Dimension | One row per lab test, with retail price | LabTestID |
| BenchmarkAvoidedCare | Reference | One row per type of outside care | AvoidedCareCategory |
| Targets | Reference (not related) | One row per target or assumption | Metric |
| UserAccess | Security | One row per partner sign-in | UserEmail |

Relationships are one-to-many, single direction, from each dimension to the fact tables.

---

## Row-level security

| Role | Filter | Who |
|---|---|---|
| Employer | DimEmployer, DimMember: partner matches the signed-in user in UserAccess. DimLocation: public clinics plus the partner's own onsite clinic | Partner users |
| Admin | No filter | Company staff |

`USERPRINCIPALNAME()` returns the signed-in user's sign-in name, which is matched against `UserAccess[UserEmail]`. Users whose sign-in is not in UserAccess see no data.

---

## Assumptions

| Item | Value | Note |
|---|---|---|
| Membership fee | $80 per member per month | Flat fee |
| Avoided care benchmarks | ER $1,800 · Imaging $450 · Specialist $350 · Urgent care $200 · Primary care office visit $150 · Virtual primary care $80 | Illustrative averages |
| Insurance benchmark | $600 per member per month | Assumed |
| ROI target | 2.0x | Assumed |
| Engagement target | 70% | Assumed |

- Avoided outside care costs are an **estimate**: each visit is assumed to replace one visit elsewhere. Prescription and lab savings use actual prices.
- **Members using care** counts anyone with a visit during the quarter, so a member who visited and left before quarter end is counted as using care but not as a covered member.
- No names or diagnoses appear in the report. Members are shown only as counts, member types and visit reasons.

---

## Data quality checks

| Check | Rule |
|---|---|
| Eligibility feed gap | Every partner-month in FactMemberMonths has a matching FactEligibility row. The synthetic data includes one deliberate gap: Desert Sun Distribution, August 2026 |
| Savings add up | Avoided outside care costs + lower prescription prices + included lab tests = estimated savings |
| Price check | No prescription has a price paid above its pharmacy price |
| Enrollment check | Staff enrolled never exceeds eligible staff |
| Key check | Every key in the fact tables exists in its dimension |
| Security check | Each test sign-in sees only its own partner's data |
