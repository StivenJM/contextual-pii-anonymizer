---
name: IA Middleware
description: Dark graphite checkpoint UI for reviewing and protecting text before it reaches a commercial LLM.
colors:
  signal-blue: "#4f8cff"
  signal-deep: "#295eb0"
  signal-line: "#527bbd"
  pass-green: "#3ecf8e"
  hold-amber: "#b26a00"
  hold-soft: "#ffd8a8"
  refused-red: "#e05c5c"
  refused-soft: "#ffd0d0"
  graphite-night: "#1a1b1e"
  graphite-card: "#26272b"
  graphite-raised: "#35373e"
  ink-field: "#18191c"
  chip-fill: "#33343a"
  overlay-top: "#2a2c31"
  overlay-bottom: "#222327"
  switch-off: "#4a4b52"
  muted-steel: "#9a9ba1"
  text-main: "#e8e8ea"
  text-bright: "#ffffff"
  hairline: "#3a3c42"
  border-field: "#656873"
typography:
  title:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.45
  micro:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "10px"
    fontWeight: 600
rounded:
  sm: "5px"
  md: "6px"
  lg: "10px"
  xl: "12px"
  pill: "20px"
  full: "9999px"
spacing:
  hair: "2px"
  tight: "4px"
  base: "6px"
  gap: "8px"
  inset: "12px"
  airy: "16px"
components:
  button-primary:
    backgroundColor: "{colors.signal-deep}"
    textColor: "{colors.text-bright}"
    rounded: "{rounded.sm}"
    padding: "6px 8px"
    height: "32px"
  button-secondary:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.sm}"
    padding: "6px 8px"
    height: "32px"
  button-danger:
    backgroundColor: "#693333"
    textColor: "{colors.text-bright}"
    rounded: "{rounded.sm}"
    padding: "6px 8px"
    height: "32px"
  input-field:
    backgroundColor: "{colors.ink-field}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.sm}"
    padding: "7px"
  card-popup:
    backgroundColor: "{colors.graphite-card}"
    rounded: "{rounded.lg}"
    padding: "12px"
  card-overlay:
    backgroundColor: "{colors.overlay-bottom}"
    rounded: "{rounded.xl}"
    padding: "12px 14px"
  chip-format:
    backgroundColor: "{colors.chip-fill}"
    textColor: "{colors.muted-steel}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"
  toggle-track:
    backgroundColor: "{colors.switch-off}"
    rounded: "{rounded.full}"
    width: "44px"
    height: "24px"
---

# Design System: IA Middleware

## Overview

**Creative North Star: "The Checkpoint"**

Everything the participant types or attaches crosses one inspection desk before it leaves the browser. The extension is that desk: a control booth in the popup, a stamp on the page in the form of the review card. The design has exactly one job — make the crossing legible. Nothing here celebrates, nothing threatens. A person mid-task should always be able to answer, at a glance, what will leave, in what state, and what to do next.

The surface is dark because the work happens beside a chat window that is usually light, and because a graphite panel recedes until it has something to report. Color is not decoration but verdict: a single Signal Blue for action and active state, then three status colors that only ever describe an outcome. When a card has nothing to say it is a flat #26272b rectangle with 10px corners and no shadow. Contrast comes from text weight and the hairline border, not from elevation.

Restraint is the aesthetic. Density is high because a 320px column must hold a toggle, a format list and a nine-state research flow; the answer is a strict 4px rhythm, 12–13px body text and one accent, never a wider canvas. Motion exists only to confirm a state change and is always removable. The system's characteristic gesture is the status disc plus the gradient hairline at the foot of an overlay card: a quiet instrument light that says "processing", "done" or "blocked" without an alarm.

**Key Characteristics:**

- Graphite ground, one blue accent, three semantic status colors.
- Flat cards inside the popup; lifted overlays on the host page.
- 320px fixed column, 4px rhythm, 12–13px body text.
- Segoe UI at two weights, with a single monospace exception for identifiers.
- Every state is named in Spanish, in words a non-technical participant can act on.
- Motion: 160–180ms ease-out entries, instant removal under `prefers-reduced-motion`.

## Colors

A single blue signal over a near-black graphite family, with green, amber and red reserved exclusively for verdicts.

### Primary

- **Signal Blue** (#4f8cff): the only brand color. Active toggles, focus outlines, links inside help text, the accent hairline on a processing overlay, and the `:focus-visible` ring everywhere (2px solid, 2–3px offset). It marks "this is live" or "you are here".
- **Signal Deep** (#295eb0): the fill of a primary action — the blue a participant presses when the next step is theirs. Deliberately darker than Signal Blue so text at 12px still clears contrast.
- **Signal Line** (#527bbd): the 1px border that separates a primary button from the graphite behind it. Used instead of a second fill so the button keeps one flat value.

### Secondary

- **Pass Green** (#3ecf8e): "on", "done", "saved". It appears on status words, on the disc of a completed card, and in the `data-state="copied"` confirmation. Never used for a neutral highlight.

### Tertiary

- **Hold Amber** (#b26a00): "attention", "pending", "you must copy this now". Paired with the warm **Hold Soft** (#ffd8a8) for text on the tinted 2e2417 warning surface.
- **Refused Red** (#e05c5c): "off", "error", "blocked". Paired with **Refused Soft** (#ffd0d0) for text on the tinted 4a2020 error surface and the d58686 error border.

### Neutral

- **Graphite Night** (#1a1b1e): the popup canvas and the fixed backdrop behind every in-page overlay.
- **Graphite Card** (#26272b): the resting surface of a popup card and of a toast notice.
- **Graphite Raised** (#35373e): secondary buttons, chips at rest, and the neutral fill of a disabled control.
- **Ink Field** (#18191c): input wells. The only neutral darker than the canvas, so a field reads as a recess, not a button.
- **Chip Fill** (#33343a): the format chips (PDF, DOCX, XLSX…). A third neutral step so chips do not compete with secondary buttons.
- **Overlay Top** (#2a2c31) / **Overlay Bottom** (#222327): the two stops of the 180° gradient that identifies an overlay card. Its top is lighter than Graphite Card; that gradient is the overlay's signature, not a generic shading.
- **Switch Off** (#4a4b52): the unfilled toggle track.
- **Muted Steel** (#9a9ba1): secondary text — descriptions, help lines, chip labels, fact names. Never for something the person must act on.
- **Text Main** (#e8e8ea): default body text on every dark surface.
- **Text Bright** (#ffffff): titles inside overlay cards and label text on a primary button. Reserved for the first thing read in a block.
- **Hairline** (#3a3c42): the 1px border of overlay cards, notices and icon buttons. This border, not a shadow, defines the edge on the page.
- **Border Field** (#656873): the 1px stroke of a text input, one step brighter than Hairline so a field is findable before it is focused.

### Named Rules

**The One Signal Rule.** Signal Blue is used on ≤10% of any given surface. If an element has no state to report and no action to take, it stays graphite. Its rarity is what makes "live" readable.

**The Verdict-Only Color Rule.** Green, amber and red never appear as brand, never as decoration, and never as a hover tint. They are a sentence about an outcome — nothing else.

## Typography

**Display Font:** none — this system has no display scale.
**Body Font:** Segoe UI (with system-ui, sans-serif)
**Label/Mono Font:** the same family, plus 12px monospace for confirmation identifiers only.

**Character:** a single humanist UI face at two weights. It reads as an operating-system utility rather than a product voice, which is the intent: the person should recognize this as part of the browser, not as another assistant.

### Hierarchy

- **Title** (600, 15px, 1.3): the popup masthead and the one line that names a state ("Captura activa", "Sesión guardada").
- **Body** (400, 13px, 1.5): toggle labels, buttons, descriptions and every sentence the participant must read. 60–70 characters per line inside cards.
- **Label** (400, 12px, 1.45): status lines, help copy, research facts, button text, error and warning bodies.
- **Micro** (600, 10px): format chips only. Nothing else in the system is set below 11px.

### Named Rules

**The One-Family Rule.** Segoe UI and its system fallback. No display face, no second sans, no icon font — icons are inline SVG at 18px, or a single text glyph inside a disc. Monospace is permitted only for the research receipt value.

**The Two-Weight Rule.** Text uses 400 and 600 only. A single 700 is allowed inside a 30–34px status disc, where a glyph needs weight to survive at that size.

## Layout

The popup is a fixed 320px column with 16px padding: masthead (34px logo, 10px gap, 14px below), then cards stacked at 12px intervals. Nothing in the popup is responsive — it is a fixed instrument, and its width is a hard constraint on copy length.

Inside a card the rhythm is 4px-based: 2px between a label and its status word, 6px between stacked controls, 8px between action buttons, 10px between the header row and the body of an overlay card, 12px card padding, 14px horizontal padding on overlays, 16px canvas padding.

Overlays injected into the host page are fixed at 16px from the bottom and right edges, `max-width: min(360px, calc(100vw - 32px))`, with a 270px floor on the review card so two buttons never wrap into a stack. They sit at `z-index: 2147483647` and never reflow the page. The research flow swaps blocks in place inside one card (`hidden` on inactive states) — it never opens a second window or a modal.

## Elevation & Depth

Two tiers, and the split is doctrine. **Inside the popup, everything is flat**: cards at rest carry no shadow, separation comes from a 2-step tonal jump (#26272b over #1a1b1e) and 12px gaps. **On the host page, overlays are lifted**: a 180° gradient from #2a2c31 to #222327, a 1px #3a3c42 hairline, a heavy ambient shadow, and a 1px inset white highlight at 5% that reads as a lit top edge. A shadow is therefore a statement — "this object does not belong to the page underneath" — and the popup never makes it.

### Shadow Vocabulary

- **Overlay rest** (`box-shadow: 0 14px 36px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.05)`): every card and status overlay on the host page. It floats above someone else's interface, so it must separate hard and immediately.
- **Notice rest** (`box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35)`): the lighter dismissible research notice. One step softer than a card because it is informational and non-blocking.
- **Popup cards** (`none`): flat by definition.

### Named Rules

**The Flat-Inside, Lifted-Outside Rule.** If it renders in the popup, it has no shadow. If it renders on a host page, it has a gradient, a hairline and a shadow. Never import the overlay treatment into the popup, and never ship a shadowless floating card onto someone else's page.

## Shapes

Corners are small and functional: 5px on buttons, inputs and icon buttons; 6px on the darker secondary action and on a hovered icon button; 10px on popup cards and toast notices; 12px on overlay cards. Only three shapes break that scale, and each has a reason: format chips at 20px, the 44×24 toggle track at a full pill, and 18px white knob as a circle. Status marks are 30px or 34px discs at 50%, tinted with 12% of their semantic color and stroked at ~32–40% of it.

Borders are 1px everywhere. Inputs and secondary controls get a lit stroke (#656873 / #555965); overlays get #3a3c42; an error surface gets a #d58686 stroke. There is no 2px border in the system, and no decorative divider — separation is spacing or a tonal step.

The one ornamental gesture allowed is the 2px status hairline at the foot of an overlay card: a horizontal gradient that fades out at both ends, in Signal Blue while processing, Pass Green when done, Refused Red on failure.

### Named Rules

**The Small-Radius Rule.** 5–6px for controls, 10–12px for containers. Anything above 12px is either a chip or the switch. A 20px-radius card reads as a consumer app and is wrong here.

## Components

### Buttons

- **Shape:** 5px radius, 32px minimum height, 6px × 8px padding, 12px/1.2 text. On the host page the radius relaxes to 6px because the surrounding page is not ours.
- **Primary:** Signal Deep (#295eb0) fill, Signal Line (#527bbd) 1px border, Text Bright label. Full-width inside the popup research flow; in overlay action rows it is `flex: 1 1 130px`, so two actions share the row and three wrap.
- **Hover / Focus:** hover is `filter: brightness(1.08)` on overlays, or the background step to #3a3c42 for icon buttons — never a shadow. Focus is `outline: 2px solid #4f8cff; outline-offset: 2px` (3px on the research summary). Active is `transform: scale(0.94)` on icon buttons only.
- **Secondary:** Graphite Raised (#35373e) fill with a #555965 border. It is the default for "assign", "go to tab", "start over" — anything that changes context without committing.
- **Danger:** #693333 fill with a #d58686 border. Used only for discarding a capture session, always paired with a primary save action beside it.
- **Disabled:** opacity 0.6 on the control; a disabled card drops to 0.55 and its switch stops receiving pointer events.

### Chips

- **Style:** 20px radius, #33343a fill, Muted Steel label at 10px/600, `2px 8px` padding, 6px gaps and wrapping.
- **State:** static inventory only — chips announce which formats are accepted and are never clickable or selectable.

### Cards / Containers

- **Corner Style:** 10px in the popup, 12px on the host page.
- **Background:** #26272b flat in the popup; the #2a2c31→#222327 gradient on overlays.
- **Shadow Strategy:** see Elevation & Depth.
- **Border:** none in the popup; 1px #3a3c42 on overlays.
- **Internal Padding:** 12px (popup), 12px 14px (overlay).
- Popup cards stack at 12px and never nest more than one level.

### Inputs / Fields

- **Style:** #18191c well, 1px #656873 stroke, 5px radius, 7px padding, 13px text, full width inside the card.
- **Focus:** the shared 2px Signal Blue ring is not drawn on text fields — the field relies on its own brighter stroke, and the ring is reserved for keyboard-reachable controls that have no border change.
- **Error / Disabled:** an error is a sibling block, never a red input border. Error blocks use #d58686 border, #4a2020 fill and Refused Soft text with `role="alert"`. Warnings use #b26a00 / #2e2417 / Hold Soft.
- Checkboxes use the platform control tinted with `accent-color: var(--acento)`. Never restyle a checkbox into a div.

### Toggle (signature control)

- 44×24 pill track, #4a4b52 at rest, Signal Blue when checked, `transition: background 0.2s`.
- 18px white circular knob inset 3px, `transition: transform 0.2s`, translating 20px when on.
- The state word beside it is mandatory: "Activada" in Pass Green or "Desactivada" in Refused Red at 13px/600. The switch is never the only signal, and the whole card dims to 0.55 when the feature is unavailable for the current tab.

### Status Overlay (signature component)

- 30–34px semantic disc + 13px/600 Text Bright title + 12px/1.45 Muted Steel body, 12px gap, 12px 14px padding, 12px radius.
- The footer hairline is the state, and the state is also stated in words — never color alone.
- Entry: `opacity 0 → 1` plus `translateY(6px) → 0` over 160–180ms ease-out. Both the entry and the spinner are disabled under `prefers-reduced-motion: reduce`, where the spinner becomes a static disc.

### Masthead

- 34px logo (linked with `alt=""` since the title repeats it), 10px gap, 15px/600 title, 11px Muted Steel subtitle, 14px below.
- The masthead is the only place the product name appears; the popup still reads "PDF Middleware" as legacy copy and must become **IA Middleware**.

## Do's and Don'ts

### Do:

- **Do** name every state in words next to its color — "Activada", "Captura interrumpida", "No se pudo procesar el documento".
- **Do** keep the 320px popup column and 12px card rhythm; resize copy to fit, not the surface.
- **Do** use one Signal Blue action per block, and let secondary and danger actions recede.
- **Do** give every overlay a 1px hairline, a gradient and the ambient shadow — that is how it separates from a page it does not own.
- **Do** draw a 2px Signal Blue `:focus-visible` ring on every reachable control, and honour `prefers-reduced-motion` by removing entry animation and spinners.
- **Do** let a card do nothing visually when it has nothing to report: flat fill, no accent, no shadow.

### Don't:

- **Don't** build security scare-UI: no shield iconography, no alarm red as a background wash, no threat badges, no countdown pressure. The confirmed anti-reference for this system.
- **Don't** use a gradient, glow or shadow on a popup card, or a tonal card on top of a card.
- **Don't** introduce a second accent, a purple/indigo gradient, or a glassy translucent surface.
- **Don't** round a container above 12px (chips and the switch aside) or add a 2px border.
- **Don't** set anything below 11px outside the format chips, and don't set a weight other than 400/600 outside a status glyph.
- **Don't** signal state with color alone, or replace a text status line with an icon.
- **Don't** restyle a native checkbox or a native select into custom markup — tint the platform control.
