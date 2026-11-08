# Research capture security risks: owner review draft

- Status: **draft for owner review**, not an accepted risk assessment, security audit, ethics approval or deployment authorization.
- Prepared: 2026-10-30, from current source/configuration and the evidence below. No live university host or actual student record was inspected.
- Delivery instruction: leave this document and the related startup documentation **uncommitted** for the owner's review. Writing this review does not implement its proposed safeguards.

## Read this conclusion first

**No application-level storage encryption does not, by itself, demonstrate a high or unacceptable risk.** Earlier conversational wording that put this unconditionally in the high-priority category was too broad. Severity depends on the data, identifiability, access, retention, existing storage controls and consequences of disclosure.

The current fictional task cards explicitly prohibit real personal details. A supervised fictional pilot may justify a relatively simple protection baseline. The original proposed personal-information Form joined to a chat receipt is different: it can make the research record identifiable even if the text seems harmless. Neither case automatically needs the same controls as banking records; neither can be assessed from the university location alone.

**Pending owner review:** no measured likelihood, formal severity score, institutional risk acceptance or universal requirement to add application cryptography is asserted here. The host's disk encryption, account permissions, backup controls and actual campus reachability remain unverified.

## Scope and current architecture

| Location | Current content and boundary |
|---|---|
| Student browser | Submitted-attempt prompts and observed rendered replies buffered in extension `storage.local`; not every keystroke or unsent draft. Successful upload clears the extension's raw batch but retains receipt/session-capability metadata. |
| University research collector | Finalized raw text and consent/protocol/provider/task/time metadata in SQLite. The archive has no application-level encryption. Its host/volume may have protection, but that was not inspected. |
| Original privacy API PostgreSQL | Privacy configuration, recognizers, dictionaries, label mappings and rules, not research chat history. |
| Attachment converter | Separate backend for PDF/Office-to-Markdown conversion; the new SQLite research archive is not located there. |
| Google Forms / researcher linkage | Proposed separate identity/attribute collection joined by receipt; no live Form or automated join was created. |
| External chatbot | Receives the participant's submitted text through the provider page. This research mode does not de-identify the submitted text first. Its history is outside API deletion. |
| Export / backup | Additional copies requiring their own access, encryption, retention and recovery controls; none automatically inherit all application controls. |

Sources: [research controller](../../../../browser-extension/extension/research-background.js), [SQLite store](../../../../api/app/research/storage.py), [research authorization](../../../../api/app/research/router.py), [original PostgreSQL models](../../../../api/app/infrastructure/models.py), [study instruments](instruments.md).

## Risk register

### Stored raw data and device/profile access

**Known facts:** application code stores readable research text in SQLite and browser storage, with no extra cryptographic layer. Buffer state has no automatic local retention deadline. Server expiry is not the same as local-buffer expiry. HTTPS protects transport, not these files.

**Potential consequence:** someone with sufficient profile, filesystem, backup or device access could obtain the text. This is not a claim that every logged-in local user can already access every record; actual OS permissions and encryption are unknown. Malware or a compromised authorized account is a separate live-access threat.

**Existing controls:** explicitly enabled capture, bounded events/bodies, selected-tab/document scope, restricted extension storage contexts where supported, API authorization, raw-buffer clearing after confirmed save, and raw-local clearing on withdrawal. These are not disk encryption.

**Review action:** establish content sensitivity, actual identifiability and host protections before assigning severity. Verify restricted accounts and encrypted host/backups for real linked data. Consider application/database/envelope encryption only for a defined threat or institutional requirement; plan key custody/recovery/rotation rather than placing a key beside the archive and assuming the problem is solved.

### Researcher credential concentration and administrative access

**Known facts:** one researcher bearer key authorizes raw-record export, investigator deletion and expiry purge. Individual researcher accounts, per-person roles and an external access-audit trail are not implemented.

**Potential consequence:** a leaked researcher key gives broad access to known records and destructive operations; attribution and selective revocation are limited. Possession of a session receipt alone does **not** grant raw-record access. A stolen session capability has narrower upload/withdrawal rights and must also be protected.

**Existing controls:** separate enrollment/admin keys, hashed server-side session capabilities, researcher checks on export/purge/investigator deletion, and production rejection of admin-header session starts.

**Review action:** identify authorized operators, restrict secret/configuration files, define rotation and incident procedures, and decide whether a supervised pilot can operate with one controlled administrator. Wider multi-researcher operation needs a deliberate permissions/audit design. The original development Admin API is a separate local-only boundary; the standalone campus collector must not be replaced by publicly exposing the entire development application.

### Internal certificate authority and client trust

**Known facts:** private-IP production preparation uses Caddy's internal CA. Its public root must be verified and deliberately trusted on participant devices. Root/intermediate private keys persist on the server's TLS volume.

**Potential consequence:** trusting the wrong root or theft of the CA's signing keys can enable forged certificates accepted by enrolled trust stores. Root trust is broader than the single research IP. This does not mean theft automatically decrypts all past sessions.

**Existing controls:** TLS validation is not disabled, the configured IP certificate is selected for no-SNI clients, private CA material is not distributed in the extension, and no host/client trust installation occurred during preparation.

**Review action:** involve university IT, verify the public certificate fingerprint through an independent channel, protect/restrict CA state/backups and define trust removal. An institutional CA is an alternative if available and approved; do not assume it already exists. Never ask students to bypass browser warnings.

### Reusable cohort enrollment, fabricated records and resource exhaustion

**Known facts:** the enrollment secret can start multiple sessions. It is not a single-use invitation, identity proof or participant quota. There is no global session/storage quota, distributed rate limiter or automatic disk-quota enforcement.

**Potential consequence:** a leaked code could permit unsolicited/fabricated sessions, disk consumption or degraded availability. Accepted JSON does not establish that a transcript came from a genuine student/provider interaction. The enrollment code cannot export other participants' records.

**Existing controls:** strict/bounded payload validation, session capabilities, immutable/idempotent finalization, API concurrency and container resource limits. Per-request limits do not limit the total number of requests or accumulated records.

**Review action:** supervise initial cohorts, rotate enrollment codes, restrict the allowed network and monitor capacity. Decide whether one-use invitations, per-study quotas or stronger rate limiting are needed before larger recruitment. Do not report a validated payload as proof of transcript authenticity.

### Identifiable linkage and raw disclosure to an external provider

**Known facts:** the proposed personal-data Form and receipt join can identify a participant. The software's research mode records raw text and forwards the supported submission to the commercial chatbot; it is not the protection intervention. Raw text may include third parties, indirectly identifying combinations or sensitive additions beyond the supplied scenario.

**Potential consequence:** disclosure may reveal student behavior, personal circumstances or information about others without involving banking credentials. Linking mild text to an actual student can change its impact. A code is not a guarantee of anonymisation.

**Existing controls:** fictional cards, explicit collection consent and separate training permission, task/document scope, no automatic live Form, and a proposed separate real-data amendment. These controls do not constitute institutional approval or verify that no participant ever adds real details.

**Review action:** decide which real attributes are scientifically necessary, keep the identity/receipt table separate and restricted, prohibit unnecessary sensitive/third-party data, explain external-provider processing and avoid connecting participation to grades. Use fictional rehearsal first; real-data collection requires the approved protocol. Do not send Form answers or session capabilities to the model.

### Retention, withdrawal and copies that survive deletion

**Known facts:** expired server sessions are unavailable through normal completion/export, but physical row deletion requires the purge operation. No scheduler is silently installed. API withdrawal does not erase Forms, exports, backups, provider history or trained weights; an offline withdrawal remains pending remotely.

**Potential consequence:** retained copies could outlive consent/policy or remain recoverable after a participant believes everything was erased. SQLite `secure_delete` is not a universal forensic-erasure guarantee for SSDs, browser remnants or backups.

**Existing controls:** expiry checks, capability-scoped participant deletion, researcher deletion by receipt, purge endpoint, explicit withdrawal UI and immediate removal of the extension's raw text when withdrawal starts. Deletion metadata is retained to retry remote removal.

**Review action:** define an approved retention schedule for each location, schedule/verify purge, handle outstanding local saves/deletions, align backup expiry and communicate withdrawal limits before training. A default technical retention parameter is not an approved policy.

### Unverified operating environment, recovery and extension/provider changes

**Known facts:** production Docker/TLS and browser fixtures were tested locally with synthetic data. No actual campus routing/firewall, student trust rollout, university host hardening, live provider DOM, Firefox or disaster restoration was verified. The preparation command produces an unpacked extension copy, not signed enterprise distribution.

**Potential consequence:** mistaken exposure, a modified extension package, an outdated adapter, unavailable server or failed recovery could expose data, omit/mix captures or lose study records. A single university computer is a single point of failure. A passing fixture is not proof of complete provider transcript capture.

**Existing controls:** separate non-root/read-only collector and TLS containers, internal collector network, only a selected host TLS port published, persistent archive/CA volumes, exact-IP extension permission and session-bound upload/withdrawal origin. Existing attachment regression and research lifecycle/TLS tests passed at the recorded milestone; these do not replace an independent security audit.

**Review action:** verify the actual host/subnet/firewall and client trust, control extension distribution/updates, perform live-provider rehearsal using fictional data, monitor capacity/availability and test recovery in isolation. No remote access, deployment or independent delegated review is claimed.

## Proportional storage-encryption assessment

| Study/data condition | Preliminary assessment, subject to actual controls |
|---|---|
| Entirely fictional task content, no realistic author/identity linkage and supervised access | Often low confidentiality impact; do not automatically block the pilot on application-level cryptography |
| Fictional text linked to real Form responses, identities or individual performance | Identifiable research record; impact depends on access, intended uses and potential consequences |
| Free conversation with real self/third-party disclosures | Do not assume low impact from the scenario label alone; inspect the protocol and necessary attributes |
| Sensitive personal disclosures, broad sharing or a large joinable archive | Stronger safeguards and institutional assessment before collection; severity is not determined by whether bank accounts appear |

**Different controls address different threats:** HTTPS protects transit. Disk/volume encryption mainly helps against offline storage loss/theft under the solution's authentication assumptions. It does not replace protection of live OS accounts. Exported files may lose that protection. Application/database encryption can help against archive-only disclosure, but protection depends on key access and architecture; a fully compromised service that can decrypt records remains a concern. Loss of the decryption keys can also lose the dataset.

SQLite versus PostgreSQL is not the deciding security property. Changing database engines alone neither verifies disk encryption nor implements a key-management or access policy. No database migration or encryption feature was authorized by this review.

## Owner review checklist

- [ ] Confirm the phase: fictional rehearsal only, or identifiable real-data collection.
- [ ] Record necessary Form attributes and who can access the receipt-to-identity link.
- [ ] Verify actual host/profile permissions, storage encryption and backup/export handling.
- [ ] Assign custody and rotation/recovery procedures for researcher/enrollment/session/CA credentials.
- [ ] Confirm campus firewall/trust and approved extension distribution without warning bypasses.
- [ ] Decide retention for API, local buffers, Forms, exports and backups; schedule purge and withdrawal follow-up.
- [ ] Decide acceptable enrollment/volume limits for the expected supervised cohort.
- [ ] Complete synthetic live-provider rehearsal and an isolated restore test.
- [ ] Obtain the institution's privacy/ethics/security decisions before using real personal data.
- [ ] Record a reasoned residual-risk decision; no box in this document is already approved by software tests.

## Evidence and limitations

The register is source/configuration review plus literature-informed reasoning, **not** a penetration test, vulnerability scan, measured probability, legal opinion or claim of institutional compliance. No real records were read. Proposed mitigations have not been silently implemented. This documentation-only update did not rerun the software suites; previous observed results are in the operation guide.

Primary technical and governance sources:

- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final): context-based PII confidentiality impact, not an Ecuadorian legal requirement. Age of publication does not make it evidence of current local host controls.
- [NIST SP 800-111](https://csrc.nist.gov/pubs/sp/800/111/final): storage-encryption layers and offline/live-access limitations.
- [OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html): threat-based layer selection and key/data separation.
- [Microsoft BitLocker FAQ](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/faq): offline disk protection versus additional file/user controls.
- [UK Data Service participant protection](https://ukdataservice.ac.uk/learning-hub/data-producer-support/preparing-data-for-sharing-and-reuse/anonymising-data-and-protecting-participants/): identifiability, proportionate access and research-data governance.
- [Caddy local HTTPS](https://caddyserver.com/docs/automatic-https#local-https): CA state and explicit client trust responsibilities.
- [SPDP security and incidents](https://www.spdp.gob.ec/docs/proteccion-de-datos-personales/general/seguridad-e-incidentes/): if the institution is in Ecuador, security measures must reflect actual processing risks; institutional reviewers determine applicable obligations.
- [PostgreSQL encryption options](https://www.postgresql.org/docs/current/encryption-options.html): several encryption layers exist; changing engines is not automatic protection for every stored copy.

Relevant primary research, with transfer limits:

- [Ngong et al., ACL 2025](https://aclanthology.org/2025.findings-acl.1343/): indirect/contextual disclosure; the formative study had six participants, not a prevalence estimate for this university.
- [Staab et al., ICLR 2024](https://arxiv.org/pdf/2310.07298): attribute inference from Reddit profiles, not evidence that every fictional academic prompt identifies its author.
- [Tran et al., AIES 2025](https://ojs.aaai.org/index.php/AIES/article/download/36735/38873/40810): survey experiment with 300 US users; population and self-report limitations prevent direct local extrapolation.
- [Zhan et al., USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/zhan): official abstract reports a 502-participant malicious-chatbot trial. The adversarial condition differs from this pilot; this source was consulted at abstract level because the full PDF exceeded the web tool's retrieval limit.

The reviewed materials do not establish a student-disclosure percentage, automatic high-risk rating or universal obligation to add application cryptography. The [32-work study review](literature-review.md) is a separate, explicitly scoped narrative/design review; this note is not a new systematic review.

## Related procedures

- [Extension-first developer startup](../../../guides/developer-startup.md)
- [Research capture operation](../../../guides/research-capture.md)
- [University-network deployment and trust/backup procedures](../../../guides/research-campus-deployment.md)
- [Fictional task cards](scenario-cards.md), [instruments/linkage/withdrawal](instruments.md), [proposed real-data amendment](real-data-amendment.md)
