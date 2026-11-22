# Partner Quarterly Business Report (Power BI)

A direct primary care company charges partner businesses a monthly membership fee for each covered member. Every quarter it reports back to each partner, and each partner wants to know two things:

1. **Are our people using it?**
2. **Is this saving us money?**

The company does not want to build and maintain a separate report for every partner.

## The report

| Page | Answers | Main visuals |
|---|---|---|
| **Utilization** | Are our people using it? | Eligible staff, staff enrolled, engagement rate against a 70% target, which members used care, visits by quarter, visit reasons, how care was received |
| **Savings & ROI** | Is this saving us money? | Membership investment, estimated savings, return on investment, cost per member against an insurance benchmark, where the savings came from, top prescriptions by savings |

Both pages are filtered by year, quarter and partner, and each page has an introduction line that updates with the selection.

![Savings & ROI page](docs/screenshots/savings_roi.png)

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

The same rule is applied to **DimMember**. **DimLocation** keeps the public clinics and only the partner's own onsite clinic. All three rules are in [dax/rls_rules.dax](dax/rls_rules.dax).

**Testing:** the report was published to Power BI Service and shared through a Power BI app. Two test partner accounts were assigned to the Employer role and signed in separately. Each saw only its own partner's data, while the admin account saw all five.

 

## Data model

Star schema built from CSV files:

- **Facts:** FactVisits, FactPrescriptions, FactLabs, FactMemberMonths, FactEligibility
- **Dimensions:** DimDate, DimEmployer (partners), DimLocation, DimMember, DimProvider, DimVisitReason, DimMedication, DimLabTest
- **Reference:** BenchmarkAvoidedCare, Targets
- **Security:** UserAccess

 
## Key definitions

| KPI | Definition |
|---|---|
| Estimated savings | Avoided outside care costs + lower prescription prices + included lab tests |
| Return on investment | Estimated savings ÷ membership investment |
| Engagement rate | Members with at least one visit in the quarter ÷ covered members at quarter end |

Every other KPI, with its calculation, source and assumptions, is in the [data dictionary](docs/data_dictionary.md).

## Repository contents

```
data/     Synthetic CSV files and generate_data.py
dax/      Core measures and RLS rules
docs/     Data dictionary, report preview (PDF), Pbix and screenshots
```

  
## Tools

Power BI Desktop, Power BI Service, DAX, Python (synthetic data generation)

---

Built by Grace Kadiri · 
