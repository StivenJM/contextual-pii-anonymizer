# Automated verification of the browser extension

## Decision

The browser extension is verified with an automated integration harness that loads
the real extension in Playwright's bundled Chromium, drives it against local pages
that mimic a chat attachment input, and asserts what the page actually receives.
The harness has two tiers: a fast tier with deterministic HTTP doubles that needs no
Docker, and a full-system tier, marked `integration`, that runs the real Privacy
Middleware, the real document conversion service, PostgreSQL, and a contract-faithful
BentoML stub.

The extension sources stay untouched. The harness builds a patched copy in which only
five values differ: the conversion URL, the protection URL, the shared token, the
supported-site allowlist, and the manifest permissions that admit the local test
origin.

## Rationale

The extension mediates the browser interaction, so the property worth verifying is
the boundary: what the chat page receives. That boundary is observable without a
commercial model, without a login, and without anti-bot countermeasures.

The extraction point is generic. `content.js` listens for `change` on `document` and
`drop` on `window`; the site-specific selectors are only used to re-inject the
replacement file. A local page with a file input and a drop zone therefore exercises
the real interception, conversion, cleanup, protection, and replacement path.

Two risks justify the second tier. A stub-based suite proves the plumbing but not the
protection contract, and a privacy claim that is only checked against a stub is not a
privacy claim. The full-system tier runs the real detection, fusion, policy, and
de-identification code so the leak oracle is meaningful.

## Evidence base

Method: four investigations were run on 2026-10-28 against the OpenAlex works index,
using title-and-abstract queries restricted to software-engineering venues where the
topic was engineering-specific. The corpora below are the retrieval result, not a
quality ranking; identifiers are included so every entry can be checked. Findings
quoted in the decisions were read from the abstract or the paper record.

### I1. End-to-end testing of browser extensions and web clients

| # | Work | Year | Venue | Identifier |
|---|---|---|---|---|
| 1 | Challenges of End-to-End Testing with Selenium WebDriver and How to Face Them: A Survey | 2023 | ICST | 10.1109/icst57152.2023.00039 |
| 2 | Approaches and Tools for Automated End-to-End Web Testing | 2016 | Advances in Computers | 10.1016/bs.adcom.2015.11.007 |
| 3 | Exploring Browser Automation: A Comparative Study of Selenium, Cypress, Puppeteer, and Playwright | 2024 | CCIS | 10.1007/978-3-031-70245-7_10 |
| 4 | E2EGit: A Dataset of End-to-End Web Tests in Open Source Projects | 2025 | MSR | 10.1109/msr66628.2025.00121 |
| 5 | Towards Predicting Fragility in End-to-End Web Tests | 2024 | EASE | 10.1145/3661167.3661179 |
| 6 | WEFix: Intelligent Automatic Generation of Explicit Waits for Efficient Web End-to-End Flaky Tests | 2024 | WWW | 10.1145/3589334.3645628 |
| 7 | Feature-Driven End-to-End Test Generation | 2025 | ICSE | 10.1109/icse55347.2025.00141 |
| 8 | Automating End-to-End Web Testing via Manual Testing | 2022 | Journal of Information Processing | 10.2197/ipsjjip.30.294 |
| 9 | From User Stories to End-to-end Web Testing | 2023 | ICSTW | 10.1109/icstw58534.2023.00036 |
| 10 | ASSURE: Metamorphic Testing for AI-powered Browser Extensions | 2025 | arXiv | 10.48550/arxiv.2507.05307 |
| 11 | WalletProbe: A Testing Framework for Browser-based Cryptocurrency Wallet Extensions | 2025 | arXiv | 10.48550/arxiv.2504.11735 |
| 12 | WalleTruth: Visual-Oriented Software Testing for Web3 Wallet Browser Extensions | 2026 | PACMSE | 10.1145/3797150 |
| 13 | Enhancing Web Applications Observability through Instrumented Automated Browsers | 2023 | JSS | 10.1016/j.jss.2023.111723 |
| 14 | Selenium-Jupiter: A JUnit 5 extension for Selenium WebDriver | 2022 | JSS | 10.1016/j.jss.2022.111298 |
| 15 | A Survey of the Selenium Ecosystem | 2020 | Electronics | 10.3390/electronics9071067 |
| 16 | Analysis and Design of Selenium WebDriver Automation Testing Framework | 2015 | Procedia CS | 10.1016/j.procs.2015.04.038 |
| 17 | Prevalence and Maintenance of Automated Functional Tests for Web Applications | 2014 | ICSME | 10.1109/icsme.2014.36 |
| 18 | APOGEN: automatic page object generator for web testing | 2016 | Software Quality Journal | 10.1007/s11219-016-9331-9 |
| 19 | SleepReplacer: replacing thread sleeps in Selenium WebDriver test code | 2022 | Software Quality Journal | 10.1007/s11219-022-09596-z |
| 20 | BEWT: A Benchmark for End-to-End Web Testing | 2025 | LNCS | 10.1007/978-3-032-04207-1_20 |
| 21 | Automated Web Application Testing: End-to-End Test Case Generation with LLMs and Screen Transition Graphs | 2025 | arXiv | 10.48550/arxiv.2506.02529 |
| 22 | Cypress Copilot: An AI Assistant for Web Application Testing | 2024 | IEEE Access | 10.1109/access.2024.3521407 |
| 23 | Automated end to end testing with Playwright for React applications | 2024 | IJRERET | 10.63282/3050-922x.ijeret-v5i1p106 |
| 24 | Exploring the Effectiveness of End-to-End Testing Frameworks in Modern Web Development | 2022 | IJRERET | 10.63282/3050-922x.ijeret-v3i3p104 |
| 25 | Selenium Framework for Web Automation Testing: A Systematic Literature Review | 2021 | JUTI | 10.12962/j24068535.v19i2.a1021 |
| 26 | Testing using selenium web driver | 2017 | ICECCT | 10.1109/icecct.2017.8117878 |
| 27 | Hardening the security analysis of browser extensions | 2022 | SAC | 10.1145/3477314.3507098 |
| 28 | CoCo: Efficient Browser Extension Vulnerability Detection via Coverage-guided, Concurrent Abstract Interpretation | 2023 | CCS | 10.1145/3576915.3616584 |
| 29 | Chrowned by an Extension: Abusing the Chrome DevTools Protocol through the Debugger API | 2023 | EuroS&P | 10.1109/eurosp57164.2023.00054 |
| 30 | Impact of extensions on browser performance: An empirical study on Google Chrome | 2025 | EMSE | 10.1007/s10664-025-10633-1 |
| 31 | OBSERVER: Observing Browser Synthetic Environments for Robotization, Verification, Efficiency, and Resilience | 2025 | Software Impacts | 10.1016/j.simpa.2025.100752 |

### I2. Test doubles, integration architecture, and containerized environments

| # | Work | Year | Venue | Identifier |
|---|---|---|---|---|
| 1 | The Oracle Problem in Software Testing: A Survey | 2014 | TSE | 10.1109/tse.2014.2372785 |
| 2 | Designing and comparing automated test oracles for GUI-based software applications | 2007 | TOSEM | 10.1145/1189748.1189752 |
| 3 | An automated framework for software test oracle | 2011 | IST | 10.1016/j.infsof.2011.02.006 |
| 4 | A Comparative Study on Automated Software Test Oracle Methods | 2009 | ICSEA | 10.1109/icsea.2009.29 |
| 5 | Use of test doubles in Android testing | 2022 | ICSE | 10.1145/3510003.3510175 |
| 6 | Mock-object generation with behavior | 2006 | ASE | 10.1109/ase.2006.51 |
| 7 | On the Detection of Test Smells: General Fixture and Eager Test | 2007 | TSE | 10.1109/tse.2007.70745 |
| 8 | Strategies for avoiding text fixture smells during software evolution | 2013 | MSR | 10.1109/msr.2013.6624053 |
| 9 | Are test smells really harmful? An empirical study | 2014 | EMSE | 10.1007/s10664-014-9313-0 |
| 10 | Test Smell Detection Tools: A Systematic Mapping Study | 2021 | EASE | 10.1145/3463274.3463335 |
| 11 | PyNose: A Test Smell Detector For Python | 2021 | ASE | 10.1109/ase51524.2021.9678615 |
| 12 | Test smells 20 years later: detectability, validity, and reliability | 2022 | EMSE | 10.1007/s10664-022-10207-5 |
| 13 | The secret life of test smells: test smell evolution and maintenance | 2021 | EMSE | 10.1007/s10664-021-09969-1 |
| 14 | Microservices testing: A systematic literature review | 2025 | IST | 10.1016/j.infsof.2025.107870 |
| 15 | Contract Testing in Microservices-Based Systems: A Survey | 2023 | ICSESS | 10.1109/icsess58500.2023.10293058 |
| 16 | Testing for Event-Driven Microservices Based on Consumer-Driven Contracts and State Models | 2022 | APSEC | 10.1109/apsec57359.2022.00064 |
| 17 | An Empirical Analysis of Microservices Systems Using Consumer-Driven Contract Testing | 2022 | SEAA | 10.1109/seaa56994.2022.00022 |
| 18 | Bunk8s: Enabling Easy Integration Testing of Microservices in Kubernetes | 2022 | SANER | 10.1109/saner53432.2022.00062 |
| 19 | Streamlining Integration Testing with Test Containers | 2023 | IJLEMR | 10.56581/ijlemr.8.3.19-26 |
| 20 | A Taxonomy of Integration-Relevant Faults for Microservice Testing | 2025 | ICST | 10.1109/icst62969.2025.10989000 |
| 21 | The Testing Mechanism for Software and Services Based on Mike Cohn's Testing Pyramid Modification | 2021 | IDAACS | 10.1109/idaacs53288.2021.9660999 |
| 22 | Service-Level Fault Injection Testing | 2021 | SoCC | 10.1145/3472883.3487005 |
| 23 | Service-Oriented Architectures Testing: A Survey | 2009 | LNCS | 10.1007/978-3-540-95888-8_4 |
| 24 | D-Cloud: A Software Testing Environment for Reliable Distributed Systems Using Cloud Computing | 2010 | CCGRID | 10.1109/ccgrid.2010.72 |
| 25 | When to Migrate Software Testing to the Cloud? | 2010 | ICSTW | 10.1109/icstw.2010.77 |
| 26 | Just TestIt! An SBST Approach To Automate System-Integration Testing | 2025 | ACM | 10.1145/3706594.3726980 |
| 27 | An interoperable and self-adaptive approach for SLA-based service virtualization | 2012 | FGCS | 10.1016/j.future.2012.05.016 |
| 28 | Virtual environments testing in cloud service environment | 2021 | IJSA | 10.1007/s13198-021-01105-y |
| 29 | THALIA: Test Harness for the Assessment of Legacy Information Integration Approaches | 2005 | ICDE | 10.1109/icde.2005.140 |
| 30 | Docker Container Performance Comparison on Windows and Linux Operating Systems | 2022 | CIEES | 10.1109/ciees55704.2022.9990683 |
| 31 | Software Aging in Container-based Virtualization: An Experimental Analysis on Docker | 2021 | CISTI | 10.23919/cisti52073.2021.9476625 |

### I3. Flakiness, determinism, and continuous-integration reliability

| # | Work | Year | Venue | Identifier |
|---|---|---|---|---|
| 1 | An empirical analysis of flaky tests | 2014 | FSE | 10.1145/2635868.2635920 |
| 2 | A Survey of Flaky Tests | 2021 | TOSEM | 10.1145/3476105 |
| 3 | Understanding flaky tests: the developer's perspective | 2019 | FSE | 10.1145/3338906.3338945 |
| 4 | An Empirical Analysis of UI-Based Flaky Tests | 2021 | ICSE | 10.1109/icse43902.2021.00141 |
| 5 | iDFlakies: A Framework for Detecting and Partially Classifying Flaky Tests | 2019 | ICST | 10.1109/icst.2019.00038 |
| 6 | iFixFlakies: a framework for automatically fixing order-dependent flaky tests | 2019 | FSE | 10.1145/3338906.3338925 |
| 7 | Root causing flaky tests in a large-scale industrial setting | 2019 | ISSTA | 10.1145/3293882.3330570 |
| 8 | A study on the lifecycle of flaky tests | 2020 | ICSE | 10.1145/3377811.3381749 |
| 9 | Flakify: A Black-Box, Language Model-Based Predictor for Flaky Tests | 2022 | TSE | 10.1109/tse.2022.3201209 |
| 10 | Know You Neighbor: Fast Static Prediction of Test Flakiness | 2021 | IEEE Access | 10.1109/access.2021.3082424 |
| 11 | An Empirical Study of Flaky Tests in Python | 2021 | ICST | 10.1109/icst49551.2021.00026 |
| 12 | An Empirical Study of Flaky Tests in JavaScript | 2022 | ICSME | 10.1109/icsme55016.2022.00011 |
| 13 | A Survey on How Test Flakiness Affects Developers and What Support They Need | 2022 | ICST | 10.1109/icst53961.2022.00020 |
| 14 | On the use of test smells for prediction of flaky tests | 2021 | SAST | 10.1145/3482909.3482916 |
| 15 | Regression testing minimization, selection and prioritization: a survey | 2012 | STVR | 10.1002/stv.430 |
| 16 | Techniques for improving regression testing in continuous integration environments | 2014 | FSE | 10.1145/2635868.2635910 |
| 17 | Reinforcement learning for automatic test case prioritization and selection in continuous integration | 2017 | ISSTA | 10.1145/3092703.3092709 |
| 18 | Test case prioritization approaches in regression testing: A systematic literature review | 2017 | IST | 10.1016/j.infsof.2017.08.014 |
| 19 | Test Case Prioritization for Continuous Regression Testing: An Industrial Case Study | 2013 | ICSM | 10.1109/icsm.2013.91 |
| 20 | A history-based cost-cognizant test case prioritization technique in regression testing | 2011 | JSS | 10.1016/j.jss.2011.09.063 |
| 21 | An Information Retrieval Approach for Regression Test Prioritization Based on Program Changes | 2015 | ICSE | 10.1109/icse.2015.47 |
| 22 | How does regression test prioritization perform in real-world software evolution? | 2016 | ICSE | 10.1145/2884781.2884874 |
| 23 | DeepOrder: Deep Learning for Test Case Prioritization in Continuous Integration Testing | 2021 | ICSME | 10.1109/icsme52107.2021.00053 |
| 24 | A Multi-Armed Bandit Approach for Test Case Prioritization in Continuous Integration Environments | 2020 | TSE | 10.1109/tse.2020.2992428 |
| 25 | Test prioritization in continuous integration environments | 2018 | JSS | 10.1016/j.jss.2018.08.061 |
| 26 | Test Case Prioritization in Continuous Integration environments: A systematic mapping study | 2020 | IST | 10.1016/j.infsof.2020.106268 |
| 27 | An empirical analysis of the distribution of unit test smells and their impact on software maintenance | 2012 | ICSM | 10.1109/icsm.2012.6405253 |
| 28 | On the Relation of Test Smells to Software Code Quality | 2018 | ICSME | 10.1109/icsme.2018.00010 |
| 29 | Automatic Test Smell Detection Using Information Retrieval Techniques | 2018 | ICSME | 10.1109/icsme.2018.00040 |
| 30 | The Lost World: Characterizing and Detecting Undiscovered Test Smells | 2023 | TOSEM | 10.1145/3631973 |

### I4. Privacy and PII evaluation as a test oracle

| # | Work | Year | Venue | Identifier |
|---|---|---|---|---|
| 1 | Analyzing Leakage of Personally Identifiable Information in Language Models | 2023 | S&P | 10.1109/sp46215.2023.10179300 |
| 2 | The Text Anonymization Benchmark (TAB) | 2022 | Computational Linguistics | 10.1162/coli_a_00458 |
| 3 | No Intruder, no Validity: Evaluation Criteria for Privacy-Preserving Text Anonymization | 2021 | arXiv | 10.48550/arxiv.2103.09263 |
| 4 | A Survey on Current Trends and Recent Advances in Text Anonymization | 2025 | DSAA | 10.1109/dsaa65442.2025.11247969 |
| 5 | Enhancing text anonymization via re-identification risk-based explainability | 2025 | Knowledge-Based Systems | 10.1016/j.knosys.2024.112945 |
| 6 | Clinical Text Anonymization, its Influence on Downstream NLP Tasks and the Risk of Re-Identification | 2023 | EACL SRW | 10.18653/v1/2023.eacl-srw.11 |
| 7 | Robust Utility-Preserving Text Anonymization Based on Large Language Models | 2025 | ACL | 10.18653/v1/2025.acl-long.1404 |
| 8 | Detecting Personally Identifiable Information Through Natural Language Processing: A Step Forward | 2025 | Applied System Innovation | 10.3390/asi8020055 |
| 9 | Exploring the Application of LLMs in Detecting and Protecting PII in Archival Data | 2023 | BigData | 10.1109/bigdata59044.2023.10386949 |
| 10 | Privacy-Preserving Personal Identifiable Information Label Detection Using Machine Learning | 2023 | ICCCNT | 10.1109/icccnt56998.2023.10307924 |
| 11 | PII-Codex: a Python library for PII detection, categorization, and severity assessment | 2023 | JOSS | 10.21105/joss.05402 |
| 12 | Privacy-Preserving Detection of Sensitive Data Exposure | 2015 | TIFS | 10.1109/tifs.2015.2398363 |
| 13 | Privacy-Preserving Scanning of Big Content for Sensitive Data Exposure with MapReduce | 2015 | CODASPY | 10.1145/2699026.2699106 |
| 14 | A Comparative Study of Data Anonymization Techniques | 2019 | BigDataSecurity | 10.1109/bigdatasecurity-hpsc-ids.2019.00063 |
| 15 | Privacy Utility Tradeoff Between PETs: Differential Privacy and Synthetic Data | 2024 | TCSS | 10.1109/tcss.2024.3479317 |
| 16 | The Data Minimization Principle in Machine Learning | 2025 | FAccT | 10.1145/3715275.3732195 |
| 17 | From Principle to Practice: Vertical Data Minimization for Machine Learning | 2024 | S&P | 10.1109/sp54263.2024.00089 |
| 18 | Operationalizing the Legal Principle of Data Minimization for Personalization | 2020 | SIGIR | 10.1145/3397271.3401034 |
| 19 | The General Data Protection Regulation and Log Pseudonymization | 2021 | LNNS | 10.1007/978-3-030-75078-7_48 |
| 20 | A Named Entity Recognition Based Approach for Privacy Requirements Engineering | 2021 | REW | 10.1109/rew53955.2021.00072 |
| 21 | Leveraging NLP Techniques for Privacy Requirements Engineering in User Stories | 2024 | IEEE Access | 10.1109/access.2024.3364533 |
| 22 | Toward a Holistic Privacy Requirements Engineering Process | 2024 | IEEE Access | 10.1109/access.2024.3380888 |
| 23 | Privacy by design: Aligning GDPR and software engineering specifications | 2025 | IST | 10.1016/j.infsof.2025.107946 |
| 24 | CoBAn: A context based model for data leakage prevention | 2013 | Information Sciences | 10.1016/j.ins.2013.10.005 |
| 25 | Designing Sensitive Personal Information Detection and Classification Model for Amharic Text | 2021 | ICT4DA | 10.1109/ict4da53266.2021.9672227 |
| 26 | Is Data Privacy Always Good for Software Testing? | 2010 | ISSRE | 10.1109/issre.2010.13 |
| 27 | Precursor of privacy leakage detection for individual user | 2024 | Computers & Security | 10.1016/j.cose.2024.103879 |
| 28 | Privacy Leakage via De-Anonymization and Aggregation in Heterogeneous Social Networks | 2017 | TDSC | 10.1109/tdsc.2017.2754249 |
| 29 | VoicePM: A Robust Privacy Measurement on Voice Anonymity | 2023 | ACM CODASPY | 10.1145/3558482.3590175 |
| 30 | Smart metering de-pseudonymization | 2011 | ACSAC | 10.1145/2076732.2076764 |

## Decisions

### D1. Playwright with bundled Chromium

Decision: the harness uses Playwright for Python and launches the Chromium build that
Playwright ships, through a persistent context.

Evidence: Playwright documents that extensions only work in Chromium launched with a
persistent context and that Chrome and Edge removed the flags needed to side-load
extensions, so the bundled build is the supported path. Chrome 137 removed
`--load-extension` from branded builds and Chrome 142 removed the workaround flag; the
machine used for development has Chrome 156, so the installed browser cannot load an
unpacked extension at all. The Selenium ecosystem survey and the E2E challenge survey
describe the maintenance and waiting problems of the older stack; the comparative study
of Selenium, Cypress, Puppeteer, and Playwright documents the four-tool trade space;
Cypress cannot navigate `chrome-extension://` origins, and Chrome's own guidance notes
that Selenium cannot read the Manifest V3 service worker.

Consequence: one runtime, no cloud cost, access to the service worker, the MAIN-world
content script, the bridge, and the popup.

### D2. Test the boundary, not the third-party site

Decision: the suite drives the extension against local pages. It does not attempt to
reach ChatGPT, Claude, or Gemini.

Evidence: the interception listeners are generic (`change` on `document`, `drop` on
`window`); site-specific selectors only re-inject the replacement. End-to-end suites are
documented as fragile and maintenance-heavy, with UI order nondeterminism as a leading
cause (WEFix 2024; UI-based flakiness 2021; E2EGit 2025). A test oracle must be
observable and stable; the page's received file is both.

Consequence: authentication, anti-bot countermeasures, and DOM churn do not affect the
suite. The residual gap is the re-injection strategy on each site, which stays manual.

### D3. Two tiers with one explicit stub seam

Decision: a fast tier replaces the conversion service and the protection endpoint with
HTTP doubles. The full-system tier replaces only BentoML, keeping the middleware, the
conversion service, and PostgreSQL real.

Evidence: test doubles are the established remedy for slow, flaky, or hard-to-debug
dependencies (Use of test doubles in Android testing, 2022), but the oracle problem
warns that a double must preserve the contract being asserted (The Oracle Problem,
2014). Microservice testing surveys and consumer-driven contract work place the
integration boundary at the message contract, not at the internal implementation.
Chrome's own guidance distinguishes unit testing from end-to-end testing of extensions.

Consequence: the fast tier protects the pipeline contract on every run; the integration
tier protects the privacy contract on demand and before release. The inference stub is
legitimate because the middleware already treats inference as a remote HTTP service
with two fixed routes.

### D4. Deterministic waiting, no retries

Decision: positive conditions wait for an observable state; negatives sample a bounded
window. Nothing retries a failing test.

Evidence: flakiness research attributes a large share of nondeterminism to timing and
execution-order assumptions (WEFix 2024; iFixFlakies 2019; lifecycle study 2020), and
retries hide the defect instead of fixing it (Survey of Flaky Tests, 2021; developer
perspective 2019). SleepReplacer and WEFix both replace fixed delays with explicit
conditions.

Consequence: a failure is reproducible. The cost is that a negative assertion needs a
time bound; that bound is documented in the helper and kept short.

### D5. Isolated browser profile per session

Decision: each harness instance uses a fresh profile directory and its own patched
extension copy.

Evidence: order-dependent tests are a documented flakiness class with dedicated repair
frameworks (iFixFlakies 2019; iDFlakies 2019). Extension state lives in
`chrome.storage`, so a shared profile would leak the toggle between tests.

Consequence: no test depends on the previous one. The autouse fixture still resets the
toggle, the doubles, and their recorders to keep the contract explicit.

### D6. Privacy oracle on the delivered file

Decision: the central assertion is that the sensitive values present in the fixture
never appear in the bytes the page receives. The full-system tier additionally asserts
the pseudonymized form produced by the real middleware.

Evidence: text-anonymization evaluation literature shows that missing a single
identifying attribute can reveal an identity, and that privacy benchmarks must be
evaluated with dedicated criteria rather than assuming scrubbing is sufficient (TAB
2022; No Intruder, no Validity 2021; PII leakage in language models 2023). A
leak-oriented oracle is therefore the right shape for this system.

Consequence: the suite can fail for the right reason. It does not claim to measure
residual re-identification risk, only the absence of the fixture's sensitive values on
the boundary under test.

### D7. Compose overlay for the full-system tier

Decision: a dedicated `compose.test.yaml` with an ephemeral database, a stub inference
service, the real conversion image, and the real API. The development `compose.yaml`
is untouched.

Evidence: containerized integration environments are the documented practice for
service-level testing (Bunk8s 2022; test containers 2023; D-Cloud 2010), and the
repository already standardizes on Compose, so a second orchestrator would add cost
without benefit. Ephemeral state follows the isolation argument in D5.

Consequence: one command starts and destroys the stack; no named volume survives; the
development environment keeps its own data.

### D8. Patched copy instead of product changes

Decision: the harness rewrites five values in a copy. The product extension keeps its
hardcoded endpoints, token, and allowlist.

Evidence: fixture and test-double literature warns that a test fixture that diverges
from production hides defects, so the divergence is minimized, enumerated, and
asserted: every replacement records its expected and observed count and the build
fails if the upstream shape changes.

Consequence: the harness breaks loudly when the extension changes, instead of silently
testing a stale assumption. The cost is that the artifact under test is a copy, which
is recorded as a boundary in the guide.

## Consequences

- The fast tier runs without Docker in about fifteen seconds after the browser starts.
- The full-system tier builds images; the first run takes minutes, later runs are
  bounded by container startup.
- Firefox stays outside the automated suite: Playwright cannot load extensions in
  Firefox. The extension itself keeps its cross-browser manifest, but that path is
  manual.
- Prompt-level protection is not covered because this extension does not intercept the
  prompt text; the suite verifies attachments only.

## Materialization status

Implemented and verified on 2026-10-28: six fast tests and one full-system test passed.
The fast tier was verified with Playwright 1.64.1 and its bundled Chromium. The
full-system tier was verified with Docker 29.8.2.

## Alternatives considered

- Selenium with WebDriver BiDi extension installation: cross-browser, but no service
  worker access, which is where the extension's orchestration lives.
- WebDriverIO: the only mainstream option that automates Firefox extensions today;
  rejected for this unit because the repository has no Node toolchain and Firefox is
  not the delivery target.
- Puppeteer: same engine as Playwright with a narrower context model and no Python
  runner.
- Cloud device grids: solve browser coverage, not the site-authentication problem.
- Testcontainers instead of Compose: equivalent isolation, extra dependency, and a
  second lifecycle model next to the existing Compose usage.

## Open questions

- Whether the re-injection strategies (input, synthetic paste, synthetic drop) should
  get per-site fixtures once a site changes its DOM.
- Whether the full-system tier should also run the conversion service's own unit
  tests, or keep them in that component.
