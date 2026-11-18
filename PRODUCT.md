# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Participants** (primary): students and other people with or without technical training who do study tasks in a commercial LLM chat through the browser extension. Near-term design work prioritizes them.
- **Researchers**: configure and supervise study sessions, then analyse minimized, traceable results.
- **Administrators**: configure models, recognizers, dictionaries, thresholds and protection rules.

In a small deployment one person may hold both the research and administration roles.

## Product Purpose

Reduce the exposure of sensitive information before an interaction reaches a commercial language model. The system analyses the interaction before send, proposes a comprehensible protection, and lets the person review, edit and confirm a protected version of the text. When a mandatory rule is still unmet it prevents the send. Success means a participant understands what will leave the browser, finishes the task, and sends less personal information than they would have unaided.

## Positioning

Detection, classification, policy and de-identification live inside a boundary the commercial provider never sees, while the browser remains the send path — the middleware is not a provider proxy. Detection and the decision to protect are separate responsibilities, and the canonical taxonomy is versioned and cannot be changed from administration. The product is scoped to Spanish academic interactions and Ecuadorian formats, and its protection model is evaluated through an institutional study rather than asserted as a generic PII scrubber.

## Operating Context

- Participants work inside ChatGPT, Claude and Gemini pages with the extension installed and pinned.
- The extension popup is the control panel: attachment protection, chat protection, and the research capture session.
- Review happens in the page, on the send path, before content leaves the browser.
- Research capture runs in a separate chat tab under an explicit consent step, with protection controls disabled for that tab.
- Local development runs a Docker Compose stack (PostgreSQL, inference service, FastAPI middleware, attachment converter); pgAdmin is optional.
- There is no campus deployment. This checkout has no production deployment guide, collector Compose or private-network HTTPS setup; a student-computer deployment needs a separately approved design.
- Fieldwork with real students is blocked on ethics approval, a responsible investigator, and retention/access decisions.

## Capabilities and Constraints

- Detection by meaning, structure, or membership in known collections; overlapping or repeated detections are fused.
- Treatments per detection: replace, mask, pseudonymize, keep. Protection rules are configurable; mandatory rules can block a send.
- The person can re-analyse text after a manual edit, and must be able to see which kind of information was detected and what treatment is proposed.
- Shipping in the extension today: typed chat messages are reviewed and protected before send, attachments are intercepted and delegated to the local converter, and a visible error replaces silent failure.
- Advertised attachment formats: PDF, DOCX, DOC, XLSX, XLS, PPTX.
- Research capture records supported text submissions and rendered replies without de-identification and without model calls; it is explicitly enabled and is not a protection guarantee.
- Content scope: Spanish text, academic interactions, Ecuador-relevant formats. No image, audio or video processing.
- Protection reduces exposure but is not irreversible anonymization and does not replace a full legal assessment.
- The canonical taxonomy is system-owned; administration changes operational configuration only and never participates in processing an interaction.
- Accessibility standard: undecided (open decision).

## Brand Commitments

- The name shown to users is the browser extension **IA Middleware** (confirmed by the product owner).
- The repository and engineering identity is **Contextual PII Anonymizer**; **Prompt Privacy System** is the functional-documentation name.
- The current popup still titles the surface "PDF Middleware"; that is outdated legacy copy, not a brand commitment.
- Participant-facing language must be Spanish and understandable to people without technical training. The research kit is currently an English master and needs an approved Spanish adaptation plus a comprehension check before fieldwork.

## Evidence on Hand

- `docs/project/`: functional product vision, module capabilities, flows and rules (Spanish).
- `docs/architecture/`: target architecture with module boundaries and documented decisions (Spanish).
- `docs/project/experimentacion/research-study/`: 32-paper literature review, six original scenario cards (proposed instruments, not validated scales), protocol, instruments, analysis plan, report scaffold, consent and security-risk drafts.
- Working test suites: `api/tests`, `inference/tests`, `browser-extension/tests`, `e2e`.
- Must not be fabricated: ethics approval, responsible investigator, retention policy, live recruitment or external form, commercial accounts, empirical student findings, or measured model improvement.

## Product Principles

1. **Never send silently.** A protection failure blocks the send or shows an error; it never falls back to the original text unnoticed.
2. **Show before sending.** The person must be able to explain what will leave the browser and why, in their own language.
3. **Detect and decide are separate.** Detection can change; the canonical taxonomy cannot be edited by administration.
4. **Minimize and make traceable.** Study data is minimized, consent precedes recording, and results stay auditable.
5. **Claim only what is verified.** Target capabilities, shipped behaviour and measured findings are documented as distinct states.

## Accessibility & Inclusion

No standard has been established yet — an open decision. Participants include people without technical training, and participant-facing study material must be adapted to their language and accessibility needs and comprehension-checked before use.
