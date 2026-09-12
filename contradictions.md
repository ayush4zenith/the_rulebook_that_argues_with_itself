# Contradictions in the SGSITS Academic Rulebook

## Overview

Three deliberate contradictions have been planted across the SGSITS corpus. Each is documented below with **exact file locations**, **verbatim excerpts**, and a precise description of the conflict. These are the ground-truth targets for the evaluation script.

---

## Contradiction A — Exam Eligibility: Absolute Bar at 60% vs Academic Council Dispensation at 50%

### Location 1 — Absolute Floor Set by Director's Condonation Power
**File**: `rulebook/sgsits_ordinance_ug.md`  
**Section**: Chapter 5, §5.4 — *Condonation of Attendance Deficiency by the Director*  
**Original Clause Number**: **Clause 4.10.4**

**Verbatim Text**:
> "The Director, upon recommendation of the HOD and production of an authorised District Hospital medical certificate, may condone attendance shortages down to a floor of 60%. Under no circumstances shall any candidate below 60% be admitted to the examination."

### Location 2 — Academic Council Override Down to 50%
**File**: `rulebook/sgsits_ordinance_ug.md`  
**Section**: Chapter 5, §5.5 — *Special Academic Council Dispensation*  
**Original Clause Number**: **Clause 4.12.3**

**Verbatim Text**:
> "The Academic Council reserves the extraordinary authority to condone student absence of up to 30% on sports and/or medical grounds, thereby permitting students with an overall attendance of not less than 50% to write the regular semester examinations."

### Nature of Conflict

Clause 4.10.4 uses the phrase **"under no circumstances"** to set an absolute floor of **60%**. Clause 4.12.3 — in the same document, enacted by a body (Academic Council) that supersedes the Director — permits attendance as low as **50%** for exam entry. The two clauses are directly contradictory:

| Aspect | Clause 4.10.4 | Clause 4.12.3 |
|---|---|---|
| Authority | Director | Academic Council |
| Floor Attendance | 60% | 50% |
| Language | "Under no circumstances below 60%" | "Not less than 50%" |
| Trigger | Medical certificate from District Hospital | Sports or medical grounds |

**The question "What is the minimum attendance to sit the exam with a medical certificate?" produces a CONTRADICTION state.** A student with 55% attendance cannot determine from the document alone whether they are eligible.

### Why It Is Hard to Spot
Clause 4.10.4 is in the attendance condonation section; Clause 4.12.3 is in a separate sub-section on special dispensations. No cross-reference exists between them. The phrase "under no circumstances" in 4.10.4 implies completeness — a reader stops reading, believing the matter settled.

---

## Contradiction B — Fee Refund on Branch Sliding: Total Forfeiture vs. Pro-Rata Adjustment

### Location 1 — Fees Are Non-Refundable After Round 2
**File**: `rulebook/fee_schedule_deadlines.md`  
**Section**: Section III, Line 14

**Verbatim Text**:
> "Tuition fees paid for institute transfer or internal branch sliding after Round 2 are strictly non-refundable and non-adjustable against subsequent semesters."

### Location 2 — Surplus Fees Must Be Adjusted for Internal Upgrades
**File**: `rulebook/sgsits_ordinance_ug.md`  
**Section**: Chapter 2, §2.4.2 — *Fee Adjustment on Branch Change / Transfer*  
**Original Clause Number**: **Clause 2.4.2**

**Verbatim Text**:
> "In the event of an upgraded branch allotment under institutional sliding, surplus tuition and development fees deposited during the initial round shall be adjusted against the third-semester fee dues on a pro-rata basis. The Finance Officer shall calculate and communicate the adjustment amount to the student within 30 days of the branch change confirmation."

### Nature of Conflict

| Aspect | Fee Schedule Line 14 | Ordinance Clause 2.4.2 |
|---|---|---|
| File | fee_schedule_deadlines.md | sgsits_ordinance_ug.md |
| Scenario | Branch sliding after Round 2 | Upgraded allotment (internal sliding) |
| Outcome | Strictly non-refundable, non-adjustable | Must be adjusted pro-rata against Semester III fees |
| Obligation | None — student forfeits fees | Finance Officer must calculate and communicate |

Internal sliding (student upgraded within SGSITS) and institute transfer (student moves to another college) are different scenarios — but "internal branch sliding" appears explicitly in **both** clauses, and the outcomes are diametrically opposite. A student who is internally upgraded after Round 2 is simultaneously told their fees cannot be adjusted (Line 14) and that they will be adjusted (Clause 2.4.2).

### Why It Is Hard to Spot
The fee schedule and the academic ordinance are separate documents. Line 14 is in a fee table — administrative staff who process fees see it; academic staff who process branch changes see Clause 2.4.2. Neither group routinely reads the other's document.

---

## Contradiction C — Hostel Overnight Absence Penalty: ₹500 Fine vs. Two-Week Suspension (No Fine)

### Location 1 — Monetary Fine Prescribed
**File**: `rulebook/sgsits_hostel_handbook.md`  
**Section**: Section 4, §4.2 — *Overnight Leave (First-Year Residents)*  
**Original Rule Number**: **Rule 7.2**

**Verbatim Text**:
> "First-year hostel residents seeking overnight leave must submit a written application signed by their local guardian at least 48 hours in advance to the Chief Warden. Unapproved overnight absence by a first-year resident incurs a fine of ₹500 per night of unapproved absence, payable to the Hostel Mess Fund."

### Location 2 — Suspension Mandated, Monetary Fine Explicitly Excluded
**File**: `rulebook/sgsits_hostel_handbook.md`  
**Section**: Section 8 — *Curfew Violation Penalties*  
**Original Rule Number**: **Rule 11.4**

**Verbatim Text**:
> "Any unnotified night absence past the 8:30 PM biometric curfew results in immediate temporary suspension from the hostel for two weeks, without the provision of any monetary penalty."

### Nature of Conflict

| Aspect | Rule 7.2 | Rule 11.4 |
|---|---|---|
| Trigger | Unapproved overnight leave (1st-year resident) | Unnotified absence past 8:30 PM biometric curfew |
| Penalty | ₹500 monetary fine per night | Two-week hostel suspension |
| Monetary fine? | Yes — mandatory | Explicitly excluded ("without the provision of any monetary penalty") |
| File | sgsits_hostel_handbook.md | sgsits_hostel_handbook.md (same file) |

An unapproved overnight absence **necessarily** involves being absent past the 8:30 PM biometric curfew (since the curfew is before midnight). Therefore, a single incident of unapproved overnight absence by a first-year resident simultaneously triggers:
- Rule 7.2: ₹500 fine per night (monetary penalty)
- Rule 11.4: two-week suspension + explicitly **no monetary penalty**

The two rules cannot both be applied. They are in the same document, seven sections apart.

### Why It Is Hard to Spot
Rule 7.2 is in the "Leave Rules" section; Rule 11.4 is in the "Curfew Violation Penalties" section. Both sections are thematically distinct to a casual reader. The warden applying one rule is unlikely to cross-check the other.

---

## Summary Table for Eval Script

| ID | Expected State | Clause A | File A | Clause B | File B | Conflict Nature |
|----|---------------|----------|--------|----------|--------|-----------------|
| A  | CONTRADICTION | Clause 4.10.4 (60% floor, absolute) | sgsits_ordinance_ug.md | Clause 4.12.3 (50% minimum) | sgsits_ordinance_ug.md | Incompatible absolute floors for exam eligibility |
| B  | CONTRADICTION | Fee Schedule Line 14 (no refund/adjust) | fee_schedule_deadlines.md | Clause 2.4.2 (must adjust pro-rata) | sgsits_ordinance_ug.md | Opposite outcomes for the same scenario |
| C  | CONTRADICTION | Rule 7.2 (₹500 fine) | sgsits_hostel_handbook.md | Rule 11.4 (suspension, no fine) | sgsits_hostel_handbook.md | Same trigger, incompatible penalties |

---

*Generated for: The Rulebook That Argues With Itself — SGSITS Indore Academic Corpus*
