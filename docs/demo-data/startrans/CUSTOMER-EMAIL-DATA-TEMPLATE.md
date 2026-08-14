# Customer email — Star Trans data template (Aug 18 demo)

**Attachment:** `IPE_Data_Template_StarTrans_v1.xlsx`  
(repo copy: `ipe/docs/demo-data/startrans/IPE_Data_Template_StarTrans_v1.xlsx`)

---

Subject: IPE — Data template for Aug 18 demo cycle

Hi [name],

Ahead of Tuesday’s demo, please have your team fill out the attached data template with a representative sample of your production data. This lets us show the demo with your actual products, work centers, and manufacturing orders instead of generic sample data.

**Priority sheets (must be filled for Tuesday):**

| Sheet | Guidance |
|-------|----------|
| `01_Plants` | 1–3 rows |
| `02_WorkCenters` | Your top 15–20 work centers |
| `04_Products` | 10–15 representative transformer models |
| `05_Materials` | 30–50 key materials |
| `09_Customers` | 10–15 major customers |
| `12_ManufacturingOrders` | 15–20 current or recent MOs |

Everything else can be filled at your team’s pace. The **README** sheet explains conventions and color coding (required vs optional vs FK reference).

Please send back by **end of day Sunday** if possible so we can load it Sunday evening for Tuesday’s session.

Best,  
Waleed

---

## Internal load notes (IPE)

1. Upload via `/admin/data/upload` or `POST /api/v1/data/upload`
2. Parser expects header on **row 4**, data from **row 5** (matches this workbook)
3. Sample rows already in the template are valid Star Trans–shaped demo data if the customer returns late
