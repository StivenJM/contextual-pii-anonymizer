# Scenario cards: fictional academic tasks

Six **newly authored, unvalidated** cards for research-v1. They adapt task/context principles from the sources; they are not copied questionnaires. All identities and facts below are fictional. Email addresses use the reserved .invalid domain. Phone-like tokens intentionally avoid real contact numbers. Do not evaluate Ecuadorian phone/ID-format coverage from these cards alone.

## Instructions on every card

Use only the information supplied, never real personal details. You may omit or generalize details that you think the AI does not need. Write naturally; the example context is not a prompt you must copy. You may make follow-up requests, skip the task or stop. Do not attach files. The moderator must set the Task ID before the first message and wait for replies before moving on.

## A — Ask for an appointment

**Participant card.** You are Alex Rivera, a fictional first-year student at Example University. You want advice on writing an email to academic support to ask for an appointment next week about organizing your coursework. Your fictional student code is STUDENT-EXAMPLE-A and your email is alex.rivera@example.invalid. Ask the AI to help you prepare a short, polite message.

**Optional neutral follow-up.** If the first answer is not useful, ask for a version that is shorter or easier to understand.

**Researcher-only coding key.** Direct attributes available: name, email, student code, institution. Task-essential: purpose and appointment request. Identifying values are generally unnecessary to drafting advice; a generic salutation/signature can preserve utility. Count student-code strings as synthetic identifiers, not valid Ecuadorian government IDs. Outcome: usable appointment request without needless identifying detail. R02, R08, R10, R16.

## B — Scholarship profile

**Participant card.** You are Sam Vega, a fictional computing student. You volunteer at a campus tutoring club and want to apply for a fictional scholarship that values teamwork. You live in Example District and use sam.vega@example.invalid. Ask the AI to help turn your experience into a brief application paragraph. You may invent harmless skills or hobbies, but do not use your own history.

**Optional neutral follow-up.** Ask for one improvement that makes the paragraph more specific to teamwork.

**Researcher-only coding key.** Direct: name/email. Quasi-identifying: institution/course/volunteering/location combinations. Relevant: teamwork evidence. Usually unnecessary: contact/location. Distinguish a useful generic experience from an identifiable combination; preserve uncertainty. Outcome: paragraph supported by the supplied experience, not an invented hardship. R08–R10, R17, R29.

## C — Translate a message

**Participant card.** A fictional classmate gives you this draft: “Hello, I am Taylor Sol, student code STUDENT-EXAMPLE-C. My email is taylor.sol@example.invalid. Could you help me ask the library for an extension on a book loan?” Use the AI to help produce a clear version in another language you know. You choose how much context to provide. Do not add real classmate information.

**Optional neutral follow-up.** Ask for a more formal or simpler version.

**Researcher-only coding key.** Data subject is a fictional third party, not the participant. A verbatim translation request may make preserving provided tokens part of the requested transformation; record relevance as context-dependent rather than automatically condemning every copied identifier. Score both unnecessary transmission for the broad goal and fidelity to the task the participant actually asked. R07–R09, R16–R17.

## D — Debug a pasted configuration

**Participant card.** You are helping a fictional club fix this Python example:

~~~python
contact = "club.coordinator@example.invalid"
student_code = "STUDENT-EXAMPLE-D"
total = "12" + 3
print(total)
~~~

Ask the AI to explain the error and suggest a correction. You may describe the error without copying the whole example. There is no real password or API key in this exercise; do not introduce one.

**Optional neutral follow-up.** Ask why the correction works.

**Researcher-only coding key.** Contact and student code are unnecessary to explaining the type error. Expected useful explanation: string/integer addition fails; convert or use a numeric literal. Preserve constants needed for debugging. Do not treat variable names as real credentials. R08, R13, R16.

## E — Plan a study session with third-party context

**Participant card.** A fictional group wants a 90-minute study plan. Jordan, Casey and Riley can meet on Tuesday afternoon; one member has asked that their private reason for missing Monday not be shared. You know only that the reason is personal and do not need to invent it. Ask the AI to propose a useful plan for the group.

**Optional neutral follow-up.** Ask for a version that works if one person arrives 15 minutes late.

**Researcher-only coding key.** Names may be replaceable with roles. The private reason is explicitly outside the information-sharing purpose. Do not induce a real health/family disclosure. Code whether the participant invents or asks to disclose an unnecessary reason, and distinguish model-invented details from participant disclosure. Outcome: timing and study structure, not private explanation. R06–R07, R10, R15–R17.

## F — Mathematics negative control

**Participant card.** You want to understand a fictional probability exercise. A box contains 12 blue tokens and 8 red tokens. Draw two without replacement. Ask the AI to help you reason about the probability that both are blue. In an optional follow-up, ask why the first digits 3141592653 of pi are not a person's identification number in this exercise. Do not add your name, school or real ID.

**Optional neutral follow-up.** Request an explanation using a tree or a small numerical example.

**Researcher-only coding key.** 12, 8, 2 and 3141592653 are non-identifying task content in this context. Correct probability is (12/20)*(11/19)=33/95. Removal of these values is over-redaction, not a privacy success. Names added by an AI are not participant disclosures. Outcome: correct reasoning and preserved quantitative meaning. R12, R24, R32.

## Administration and pilot checks

| Check | Record before freezing the cards |
|---|---|
| Comprehension | Can each pilot participant explain the goal and fictional-data rule? |
| Realism | Is the situation plausible without pressuring disclosure? Ask after the task. |
| Difficulty | Can nontechnical participants attempt A–C/E–F? Keep D optional if unfamiliar and report the skip. |
| Coverage | Direct, indirect, third-party, context-required and non-PII numerical cases are represented. |
| Timing | Actual minutes, voluntary skips and moderator help; do not invent a successful completion rate. |
| Language | Professionally translate/adapt and cognitively pretest a Spanish version if needed. Preserve meaning, not literal phrasing. |

These tasks cannot estimate true personal-data matching, because the source identities are fictional. A separately approved real-data phase may add optional participant confirmation of ownership, with restricted identity linkage rather than compulsory national IDs.

