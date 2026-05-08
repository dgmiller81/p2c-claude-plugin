# Visual Standards & Mockup Mandate

> **This is absolute.** Visuals — specifically high-fidelity mockups of every key screen — are required for any p2c run that touches phase 3, phase 5, the POC commands, or any flow that will eventually involve UI. The orchestrator does **not** proceed past the design phase or into a build phase without mockups in place. There is no "we'll mock it up later" path.

## The mandate, stated plainly

1. **Every section of every active phase must be completed** — delivered with file-backed evidence in `p2c-workspace/` — or **explicitly skipped on direct user instruction** with the skip recorded in `status.json`. Silent gaps are a process failure.
2. **Mockups are required** for every key screen in the validated MVP scope (golden path + supporting flows + every state per screen).
3. **Mockups must look enterprise-grade.** Polished, beautified, B2B-business-credible. Real-feeling sample data, not Lorem ipsum. Working empty / loading / error / success states. Real-looking copy.
4. **Mockups must match brand if branding is provided.** If the user supplies brand assets (logo, palette, typography, voice/tone, brand book), the mockups conform to them. If no branding is provided, default to the **Enterprise Default Style** described below.
5. **No proceed without mockups.** The orchestrator pauses at phase 3 until mockups exist. The orchestrator pauses before starting `/p2c:tech-build` or the build leg of `/p2c:poc` until mockups exist.

## What counts as "mockups"

Acceptable formats, in priority order:

1. **Figma file (or Sketch, Penpot)** — link to a frame-per-screen file with the golden path connected. Best for handoff, dev mode, and design system integration. This is the gold standard.
2. **HTML mockups** — a self-contained `mockups/` folder of static HTML files that render the high-fidelity screens with real CSS, real components, and real-feeling sample data. Servable via the visual server (`/mockups` route added to `start_visual_server.py` if needed). This is the fallback when no design tool is available, and the **default we generate** when there is no designer in the loop.
3. **PNG / SVG exports** — only acceptable as a complement to (1) or (2), not as the sole deliverable.

What does **not** count: pencil sketches, Excalidraw scribbles, ASCII art, "imagine a screen with…" prose. Those are wireframes — fine as a precursor in phase 3, but they are not mockups.

## Required coverage per screen

For every screen in the MVP golden path **and** every supporting screen needed to complete the validated job:

- **Default state** — populated, plausible content
- **Empty state** — what a brand-new user sees
- **Loading state** — skeletons or spinners, in-place not full-page
- **Error state** — a real error message with a path to recovery
- **Success / confirmation state** — what the user sees when their action lands
- **Mobile breakpoint** if the product is web-responsive
- **Dark mode** if the product supports it (mention "later" if deferred — that's an explicit skip)

## Enterprise Default Style (when no branding is provided)

A neutral, premium B2B-SaaS aesthetic. Use this as the baseline.

### Palette
- **Background:** near-white `#F8FAFC` (light) or near-black `#0F1115` (dark)
- **Surface:** `#FFFFFF` (light) / `#161922` (dark) for cards, modals
- **Border / divider:** `#E2E8F0` (light) / `#262B39` (dark) — 1px, never heavy
- **Text primary:** `#0F172A` (light) / `#E7E9EE` (dark)
- **Text muted:** `#64748B` (light) / `#8A91A3` (dark)
- **Accent (one):** `#2563EB` (blue) — used sparingly for primary CTAs and links only
- **Status:** success `#16A34A`, warning `#D97706`, danger `#DC2626`. Use only on status indicators.

### Typography
- **System sans** by default: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`
- **Headings:** 600 weight, modular scale (1, 1.125, 1.25, 1.5, 1.875, 2.25 rem)
- **Body:** 400 weight, 1rem, line-height 1.5
- **Numbers:** `font-variant-numeric: tabular-nums` in tables and KPIs
- **No more than 2 type weights and 1 family per mockup.** Restraint signals enterprise.

### Layout
- **Generous whitespace.** Padding ≥ 16px on cards, ≥ 24px on sections, ≥ 48px between major regions.
- **Max content width** 1280–1440px on desktop. Don't fill 4K monitors.
- **Grid:** 12-column with 24px gutters, or CSS grid with explicit minmax — never floats.
- **Top nav** with the product name, primary nav, and the user/account chip in the corner. Sidebar nav is acceptable for app shells with deep IA.

### Components
- **Buttons:** 36–40px height, 6–8px radius, 12–16px horizontal padding, accent for primary, neutral outline for secondary, ghost for tertiary
- **Inputs:** 36–40px height, 1px border, focus ring in accent color, helper text + error text distinguished
- **Cards:** 1px border or subtle shadow `0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.04)`, 8–10px radius
- **Tables:** zebra optional, sticky header on scroll, right-align numbers, sort icons present, pagination or infinite-scroll cue at the bottom
- **Modals / drawers:** centered modal for confirmations; right-side drawer for entity editing
- **Empty states:** illustration or icon + 1-line headline + 1-line subhead + primary CTA

### Motion
- **Transitions** 120–200ms ease-out for hover, 200–300ms for state changes. Nothing that delays user input.
- **No motion** for tabular data refreshes — flicker is unprofessional.

### Sample data
- **Real-feeling names**: "Aisha Khan," "Marcus Williams," "Linnea Aaltonen" — not "John Doe" / "Jane Smith"
- **Real-feeling companies**: "Northwind Logistics," "Kestrel Analytics," "Silverline Health" — not "Acme Corp"
- **Real-feeling numbers**: "$24,180.50" not "$1,234.56"; non-round percentages like "62.3%" not "50%"
- **Real-feeling dates**: relative ("3 hours ago") and absolute, with the right locale

### Iconography
- One icon family throughout (Lucide is the default; Phosphor / Heroicons / Material Symbols are acceptable). 16/20/24px sizes only. No emoji as primary iconography in enterprise mockups.

### Accessibility baseline (already required by phase 6 — repeated here for the visual layer)
- **Contrast:** AA min on body text, AAA on critical UI text
- **Focus rings** visible in every state
- **Tap targets** ≥ 40px on mobile
- **Don't rely on color alone** to convey state — pair with icon and text

## When the user provides branding

If the user supplies any of the following, they take precedence over the Enterprise Default Style for that dimension:

- **Logo** — use it in the top nav at appropriate size (24–32px height) and in the auth/onboarding hero
- **Palette** — replace the accent and any color variables; preserve neutrals unless brand specifies
- **Typography** — swap the default system stack; preserve weight/scale rules
- **Voice / tone** — apply to all in-mockup copy, including empty states and errors
- **Imagery / illustration** — use brand-supplied illustrations or photos in marketing-adjacent screens
- **Brand book / style guide** — read it, mirror its rules in the design system tokens

When branding is partial (e.g., a palette but no type system), use the brand-supplied dimension and fall back to the Enterprise Default for the rest.

## Generating mockups when no designer is available

Default behavior when the team doesn't have a designer:

1. Confirm with the user: "I don't see a designer in the loop. I'll generate enterprise-grade HTML mockups in `p2c-workspace/03-design/mockups/` using the Enterprise Default Style (or your brand if you've shared it). OK?"
2. Dispatch the **lead-developer** agent (or the `frontend-design` skill if available) to produce the mockups.
3. Each screen is a self-contained HTML file with embedded CSS — runnable via the visual server's static-asset path or by opening the file directly.
4. Include a `mockups/index.html` that links every screen and shows the golden path.
5. The user reviews. The orchestrator does **not** proceed to phase 4 until the user confirms the mockups are approved or has explicitly accepted partial coverage in writing.

## How the orchestrator enforces this

In `status.json`, phase 3 is **never** marked `delivered` unless `files` contains entries pointing to mockups (Figma URL, `mockups/` folder, or PNG exports listed). If the user runs `/p2c:tech-build` or the build leg of `/p2c:poc` without phase 3 mockups in place, the orchestrator pauses and asks for one of:

1. Approve generating Enterprise Default mockups now.
2. Provide a Figma link or design files.
3. Explicitly skip with reason recorded in `status.json` (rare, requires user confirmation).

This is intentionally a hard gate. Building before visuals exist is how teams ship products that look like prototypes.
