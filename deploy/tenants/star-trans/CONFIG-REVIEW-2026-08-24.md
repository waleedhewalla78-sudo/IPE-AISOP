# Star Trans configuration review — 2026-08-24

**Status:** DRAFT for Waleed + Eng. Mohamed. **Not loaded** into the tenant.  
**Constraint:** Islamic holiday dates are approximations. Do not treat as authoritative.

Lab tenant id (operational): `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`  
Canonical uuid5: `6a7281ee-62cb-5a72-8162-d3c573e54877`

Sign-off required before BATCH2-2 STEP 10 (production/lab config insert).

---

## 1. Calendar — Cairo Plant Standard

- Working days: Sunday–Thursday
- Non-working: Friday–Saturday
- Shifts (confirm 2 vs 3 with Eng. Mohamed):
  - Morning 08:00–16:00 (8h)
  - Evening 16:00–24:00 (8h) — if 2-shift
  - Night 00:00–08:00 (8h) — if 3-shift **UNCONFIRMED**
- Break: 30 min / 8h (paid)
- OT: after 8h 1.5x; Friday work 2.0x

### Civil / Coptic holidays 2026 (verify official gazette)

| Date | Name | type |
|------|------|------|
| 2026-01-07 | Coptic Christmas | holiday |
| 2026-01-25 | 25 January Revolution Day | holiday |
| 2026-04-12 | Coptic Easter (verify) | holiday |
| 2026-04-13 | Sham El Nessim (verify; day after Coptic Easter) | holiday |
| 2026-04-25 | Sinai Liberation Day | holiday |
| 2026-05-01 | Labour Day | holiday |
| 2026-06-30 | June 30 Revolution Day | holiday |
| 2026-07-23 | Revolution Day | holiday |
| 2026-10-06 | Armed Forces Day | holiday |

### Islamic / reduced hours 2026 — **UNVERIFIED approximations**

| Approx date | Name | type |
|-------------|------|------|
| 2026-02-17 → 2026-03-18 | Ramadan (reduced 09:00–15:00, 6h) | reduced_hours |
| 2026-03-19 → 2026-03-22 | Eid Al-Fitr | holiday |
| 2026-05-26 → 2026-05-29 | Eid Al-Adha | holiday |
| 2026-06-15 | Islamic New Year | holiday |
| 2026-08-24 → 2026-08-25 | Prophet's Birthday | holiday |

---

## 2. Product families (structure only — no SKUs)

| family_code | family_name | default_lead_time_weeks | routing_template |
|-------------|-------------|-------------------------|------------------|
| DIST | Distribution Transformers (500–2500 kVA) | TBD | TBD |
| POWER | Power Transformers (5–50 MVA) | TBD | TBD |
| SPEC | Special Purpose / ETO | TBD | TBD |

Individual models load in BATCH2-3 Excel.

---

## 3. Customer tiers

| tier_code | tier_name | priority_weight | late_penalty_multiplier | credit_terms_days |
|-----------|-----------|-----------------|-------------------------|-------------------|
| T1 | Strategic (EEHC, DEWA, SEC) | 1.00 | 2.0 | TBD |
| T2 | Preferred | 0.80 | 1.5 | TBD |
| T3 | Standard | 0.60 | 1.0 | TBD |
| T4 | Occasional | 0.40 | 0.5 | TBD |

---

## 4. Supplier tiers

| tier_code | tier_name |
|-----------|-----------|
| S1 | Strategic (CRGO, copper) |
| S2 | Preferred (OTD > 95%) |
| S3 | Standard |
| S4 | Watch |

---

## 5. Work center categories

- Core Manufacturing: Winding, Core Assembly, Tank Fabrication, Core Insulation
- Testing: Routine, Type, Special
- Finishing: Painting, Bushings, Nameplate
- Support: Material Prep, Kitting, QC Incoming

---

## 6. Feasibility bands (Phase 1 default — no customisation)

- Critical 0–49
- Warning 50–69
- Review 70–84
- Good 85–94
- Excellent 95–100

## 7. Feasibility weights (Phase 1 default)

OTD 30% + Capacity 25% + Quality 20% + Supply 15% + Plan Coverage 10%.

Supply-weight bump for copper/CRGO: **not applied** (no operational justification this session).

---

## Config item count (for sign-off)

11 civil/Coptic rows + 5 Islamic groups + 3 families + 4 customer tiers + 4 supplier tiers + 4 WC categories + 5 bands + 5 weights ≈ **41 review items**.

**Waleed confirmation timestamp:** _pending_  
**Eng. Mohamed confirmation timestamp:** _pending_
