# Synthetic Dataset: Direct Primary Care Employer Value Report

Fully synthetic data for a Power BI portfolio project. All employers, members, emails and figures are fictional. Members carry no names, birth dates or addresses (age band only), mirroring de-identified reporting.

- **Period:** Jan 2025 – Sep 2026 (7 complete quarters; Q4 2026 is "in progress")
- **Employers:** 5, with staggered contract starts (some have YoY history, one is brand new in 2026)
- **Membership fee:** $80 per member per month

## Tables and relationships (star schema)

| Table | Grain | Key(s) | Relates to |
|---|---|---|---|
| DimDate | 1 row per day | Date | All fact dates (VisitDate, FillDate, LabDate, MonthStart) |
| DimEmployer | 1 row per employer | EmployerID | All facts, UserAccess |
| DimLocation | 1 row per site (incl. Virtual Care) | LocationID | FactVisits |
| DimMember | 1 row per member | MemberID | FactVisits, FactPrescriptions, FactLabs, FactMemberMonths |
| DimProvider | 1 row per provider | ProviderID | FactVisits |
| DimVisitReason | 1 row per reason category | ReasonID | FactVisits |
| DimMedication | 1 row per drug | MedicationID | FactPrescriptions |
| DimLabTest | 1 row per test | LabTestID | FactLabs |
| BenchmarkAvoidedCare | 1 row per care setting | AvoidedCareCategory | FactVisits |
| FactVisits | 1 row per encounter | VisitID | |
| FactPrescriptions | 1 row per fill | FillID | |
| FactLabs | 1 row per lab test ordered | LabOrderID | |
| FactMemberMonths | 1 row per member per enrolled month | MemberID + MonthStart | |
| FactEligibility | 1 row per employer per month (Paycom feed) | EmployerID + MonthStart | |
| UserAccess | 1 row per employer login | UserEmail | DimEmployer (for RLS) |
| Targets | 1 row per target/assumption | Metric | Disconnected (read with measures) |

Relationships are one-to-many, single direction, from each dimension to the facts. Keep Targets disconnected.

## Key columns

- **FactVisits.VisitType:** In-Person, Telehealth, Call/Text. Virtual visits use LocationID `L00`.
- **FactVisits.AvoidedCareCategory:** where the member would likely have gone without the clinic. Look up `BenchmarkCost` to value each encounter (this is the "apply healthcare cost benchmarks" step from the job description; do it in Power Query or with `RELATED()`).
- **FactVisits.CPTCode:** illustrative visit codes (`-95` suffix = telehealth).
- **FactVisits.AccessTiming:** Same Day / Next Day.
- **FactPrescriptions.RetailPrice / PricePaid:** generics included in membership have `PricePaid = 0`; other drugs are sold at wholesale.
- **FactMemberMonths.MembershipFee:** $80 per row. Summing it gives employer spend.
- **FactEligibility.EligibleEmployees:** from Paycom. `EnrolledMembers` and `EnrolledEmployees` are reconciled from the member roster.
- **DimMember flags:** HasChronicCondition, InWeightProgram, InHormoneProgram (synthetic, drive visit and Rx patterns).

## Core measure definitions

| KPI | Calculation |
|---|---|
| Employer Spend | SUM(FactMemberMonths[MembershipFee]) |
| Avoided Care Cost | SUM of BenchmarkCost over visits |
| Rx Savings | SUM(RetailPrice) − SUM(PricePaid) |
| Rx Savings Rate | Rx Savings ÷ SUM(RetailPrice) |
| Lab Savings | SUM of DimLabTest[RetailPrice] over lab orders |
| Total Savings | Avoided Care + Rx Savings + Lab Savings |
| ROI Multiple | Total Savings ÷ Employer Spend |
| Member Months | COUNTROWS(FactMemberMonths) |
| Cost per Member (PMPM) | Employer Spend ÷ Member Months (compare to $600 benchmark in Targets) |
| Active Patients | DISTINCTCOUNT(FactVisits[MemberID]) in period |
| Avg Enrolled Members | AVERAGEX over months of COUNTROWS(FactMemberMonths) |
| Engagement Rate | Active Patients ÷ Avg Enrolled Members (quarterly; target 70%) |
| Enrollment Rate | Enrolled Employees ÷ Eligible Employees |
| Visits per Member per Month | Visits ÷ Member Months |

## Patterns built in for the AI Insights page

1. **Engagement drop at Front Range Beverage Co. (E002), Q3 2026.** Telehealth visits fall from ~104 to ~28 vs Q2, and engagement drops below the 70% target. ROI also falls below the 2.0x target.
2. **High-cost medication concentration.** Three drugs (apixaban, compounded semaglutide, insulin glargine) make up roughly 70% of Rx spend.
3. **Flu-season anomaly.** Jan 2026 visits spike to ~1,060 vs ~650 in Dec 2025. Good for anomaly detection.
4. **New-contract ramp-up.** Utilization starts low after each contract start and climbs over the first months (see E004, E005).
5. **Overall ROI** runs about 1.6x–2.4x by quarter, so some quarters beat the target and some miss it.

## Planted data-quality issue

- **FactEligibility is missing Desert Sun Distribution (E003) for Aug 2026**, simulating a broken Paycom feed. Build a check that flags employer-months present in FactMemberMonths but missing from FactEligibility. It's a good talking point for the "monitor payroll and eligibility feeds" duty.

## RLS setup

- Role **Employer**: on DimEmployer, filter
  `[EmployerID] IN CALCULATETABLE(VALUES(UserAccess[EmployerID]), UserAccess[UserEmail] = USERPRINCIPALNAME())`
  (or relate UserAccess → DimEmployer and filter `UserAccess[UserEmail] = USERPRINCIPALNAME()`).
- Role **Admin**: no filter (CEO/COO).
- Test with *Modeling → View as → Other user* using an email from UserAccess.

## Assumptions (state these on the dashboard)

- Benchmark costs per care setting are illustrative averages, not sourced market rates.
- Traditional insurance cost assumed at $600 per member per month.
- Every encounter is valued at the setting the member would otherwise have used; this is an estimate, which is why Rx and lab savings (actual prices) are shown separately.

`generate_data.py` regenerates the dataset (fixed seed, so output is reproducible): `python generate_data.py <output_folder>`.
