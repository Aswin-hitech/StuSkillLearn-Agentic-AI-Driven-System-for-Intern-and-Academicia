# Portal Research & UI/UX Decisions

Research refreshed: 11 September 2026.

## AICTE National Internship Portal
Official source: https://internship.aicte-india.org/

Useful current patterns:
- Strong Student / Industry / Institute entry points rather than one overloaded portal.
- Fast opportunity discovery through remote/hybrid, stipend, closing-date, state and domain shortcuts.
- Employer verification and certificate verification are visible trust signals.
- Opportunity cards emphasize the decision data a student needs before opening details.

StuSkillLink adopts role clarity, compact discovery metadata, trust cues and certificate/badge verification, then adds the proposal-specific closed loop: skill gaps → LSRW → learning → explainable matching → allocation/reallocation → company feedback → curriculum insight.

## National Career Service (NCS)
Official source: https://www.ncs.gov.in/

Useful current patterns:
- Employability assessment is treated as a first-class career-readiness step.
- AI Interview Coach and mentoring are separated from the core job-search experience.
- The product communicates safety/trust information clearly.

StuSkillLink applies the same separation principle: readiness/LSRW is a dedicated journey, while opportunity matching and allocation remain distinct workflows.

## Handshake
Official source: https://support.joinhandshake.com/hc/en-us/articles/38856960612631-About-AI-powered-features-in-Handshake-for-students

Useful current patterns:
- AI guidance is contextual to a specific job/profile.
- AI can rank and recommend while students keep control of filters and application decisions.
- AI does not make hiring decisions.
- Complete profiles improve recommendation relevance.
- Candidate views emphasize skills, education, projects and evidence relevant to a role.

StuSkillLink follows the same human-control principle: NVIDIA NIM can explain and recommend, but eligibility, tiering, rank order, category-seat constraints, tie-breaking and final allocation are deterministic and inspectable.

## UI-reference tooling
Mobbin was connected as a UI-reference skill for this redesign. Its search endpoint requires a paid Mobbin plan in this environment, so no unverified Mobbin screenshots were copied. The final interface instead uses the official portal research above plus standard accessibility and information-hierarchy principles.

## UI system implemented
- Exactly four role-specific workspaces: Student, Industry, Academician and Institution.
- Persistent left navigation on desktop and a compact drawer on mobile.
- Neutral slate surfaces with one restrained sky accent; visual status colors are reserved for meaning.
- Large readable page titles, short explanatory copy, compact metrics and action-first cards.
- Tables/cards are used only where comparison helps; dense information is broken into evidence panels.
- Student control is explicit: preferences, general-pool opt-in, application, offer accept/reject, filters and learning completion.
- Company decisions expose score components, tier, rank, tie-break order, allocation round and category slot.
- LSRW is a guided assessment flow instead of a raw score-entry screen.
- Company feedback is a real form rather than a pre-filled demo-only action.
- Institution views prioritize readiness, gap evidence and curriculum actions instead of generic analytics.
