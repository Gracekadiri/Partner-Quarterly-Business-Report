# Partner Quarterly Business Report with RLS

A direct primary care organization charges partner businesses a monthly membership fee for each covered member. Every quarter it reports back to each partner, and each wants to know two things:
 
1. **Are our people using it?**
2. **Is this saving us money?**
The organization does not want to build and maintain a separate report for every partner.
 
## The report
 
| Page | Answers | Main visuals |
|---|---|---|
| **Utilization** | Are our people using it? | Eligible staff, staff enrolled, engagement rate against a 70% target, which members used care, visits by quarter, visit reasons, how care was received |
| **Savings & ROI** | Is this saving us money? | Membership investment, estimated savings, return on investment, cost per member against an insurance benchmark, where the savings came from, top prescriptions by savings |
 
Both pages are filtered by year, quarter and partner, and each page has an introduction line that updates with the selection.
 
<img width="876" height="435" alt="utilization" src="https://github.com/user-attachments/assets/909462b0-9f07-43a1-be51-3f7a8e63d264" />
<img width="874" height="438" alt="savings_roi" src="https://github.com/user-attachments/assets/7128525a-350c-473c-8bed-faeab4f0d92f" />

**[Watch the 1-minute demo](LINK-TO-LINKEDIN-POST)**: an admin login sees all five partners; two test partner logins each see only their own.

## Key insights (Q3 2026)
 
- **Partners saved more than they spent.** Across all five partners, $368K in memberships produced an estimated $678K in savings, a 1.84x return. That is below the 2.0x target, so the value story holds but has room to grow.
- **Most of the value came from avoided outside care.** About two thirds of savings came from clinic visits that replaced specialist, ER, urgent care and other outside visits.
- **Engagement is above target, but families lag.** 72.9% of covered members used care against a 70% target. Staff used it most; children were least likely to use care.
- **Results differ by partner.** Summit Logistics returned 1.94x, while Front Range Beverage returned 1.63x, the lowest of the five, partly because its telehealth visits dropped sharply.
- **Visits fell slightly from Q2,** mainly from fewer acute illness visits, which is consistent with a seasonal pattern rather than a drop in engagement.
## Row-level security
 
Shared as it is, any partner could use the Partner filter to see other partners' data. Dynamic row-level security solves this with one report:
 
- A **UserAccess** table links each sign-in to a partner (EmployerID).
- One **Employer** role filters the data by whoever is signed in.
- An **Admin** role has no filter and sees all partners.
```dax
-- Employer role, filter on DimEmployer
VAR UserEmployers =
    SELECTCOLUMNS (
        FILTER ( UserAccess, UserAccess[UserEmail] = USERPRINCIPALNAME () ),
        "EmployerID", UserAccess[EmployerID]
    )
RETURN
    [EmployerID] IN UserEmployers
```
 
The same rule is applied to **DimMember**. **DimLocation** keeps the public clinics and only the partner's own onsite clinic. All three rules are in the [dax folder](dax/).
 
**Testing:** the report was published to Power BI Service and shared through a Power BI app. Two test partner accounts were assigned to the Employer role and signed in separately. Each saw only its own partner's data, while the admin account saw all five.
 
## Data model
 
Star schema built from CSV files:
 
- **Facts:** FactVisits, FactPrescriptions, FactLabs, FactMemberMonths, FactEligibility
- **Dimensions:** DimDate, DimEmployer (partners), DimLocation, DimMember, DimProvider, DimVisitReason, DimMedication, DimLabTest
- **Reference:** BenchmarkAvoidedCare, Targets
- **Security:** UserAccess
 <img width="1726" height="861" alt="Data model" src="https://github.com/user-attachments/assets/95580a37-d656-4e76-8d65-d3af6a00f6e1" />
 
## Key definitions
 
| KPI | Definition |
|---|---|
| Estimated savings | Avoided outside care costs + lower prescription prices + included lab tests |
| Avoided outside care costs | Each clinic visit valued at the typical cost of the care the member would otherwise have used |
| Return on investment | Estimated savings ÷ membership investment |
| Engagement rate | Members with at least one visit in the quarter ÷ covered members at quarter end |
 
Every other KPI, with its calculation, source and assumptions, is in the [data dictionary](docs/Data%20Dictionary.pdf).
 
## Repository contents
 
```
data/     Synthetic CSV files and generate_data.py
dax/      Core measures and RLS rules
docs/     Data dictionary, report preview (PDF), .pbix file and screenshots
```
 
## Tools
 
Power BI Desktop, Power BI Service, DAX, Python (synthetic data generation)
All data is synthetic. Partner names, members and figures are fictional.

---
 
Built by Grace Kadiri · [LinkedIn](LINK-TO-YOUR-PROFILE)
 
