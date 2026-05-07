# The Essential Stack for Design

Strip away the trend-chasing — keep what reliably produces usable, shippable interfaces.

## The "Best of" Shortlist
- **Lo-fi wireframes first** — the cheapest way to kill bad ideas
- **Clickable prototypes** — the only way to test flow before code
- **5-user usability testing** — Nielsen's rule: 5 users find ~85% of issues
- **Design system / component library** — consistency without reinventing per screen
- **Accessibility-first mindset (WCAG 2.1 AA)** — cheaper now than retrofitted later
- **Design tokens** — colors/spacing/type as variables, not hardcoded values

Everything else is polish.

## How to Structure the Process

### Phase 1: Sketch the Flow (Days 1–3)
- Start on **paper or Excalidraw** — boxes and arrows, no pixels
- Draw the **golden path** end-to-end before any single screen detail
- Identify **3–5 critical screens** — focus design energy there
- Validate the flow against the story map — every step earns its place

### Phase 2: Wireframe (Week 1)
- Move to **Figma** for low-fidelity wireframes (grayscale, no images, system fonts)
- One frame per screen, connected with prototype arrows
- Annotate intent, not implementation
- Review with 1–2 users — kill what confuses them

### Phase 3: Prototype the Golden Path (Week 2)
- Build a **clickable Figma prototype** for the primary flow only
- Don't prototype edge cases yet — they'll change after testing
- Add realistic copy (no lorem ipsum) — bad copy hides bad UX

### Phase 4: Usability Test (Week 2)
- Recruit **5–8 target users** (Maze, UserTesting, or just Calendly + Zoom)
- Give them tasks, not tours: *"Sign up and create your first X"*
- Watch silently; note hesitation, wrong clicks, abandoned tasks
- Fix anything 2+ users hit; ignore 1-off complaints

### Phase 5: Visual Design & System (Week 3)
- Lock **design tokens** (colors, type scale, spacing, radii, shadows)
- Build **core components** (button, input, card, modal, nav) — 10–15 max for MVP
- Use **a proven base** (shadcn/ui, Radix, Material, Tailwind UI) — don't draw buttons from scratch
- Apply tokens + components to wireframes → high-fidelity screens

### Phase 6: Accessibility & Edge Cases (Week 3)
- Run **WCAG 2.1 AA checks** (contrast, focus states, keyboard nav, alt text, semantic HTML)
- Design **empty, loading, error, and success states** for every screen
- Document **responsive breakpoints** (mobile-first)
- Hand off with **Figma Dev Mode** or **Zeplin** — no PNG-and-pray

## The Minimum Viable Toolset
- **Figma** — wireframes, prototypes, component library, dev handoff (one tool, end-to-end)
- **Excalidraw** — early sketching inside docs
- **Maze or UserTesting** — async usability tests
- **Stark or Figma a11y plugins** — contrast + accessibility checks
- **A component base** — shadcn/ui, Radix, Tailwind UI (pick one)

Four tools plus a component base. No tool sprawl.

## The Mental Model
Design isn't about making things pretty — it's about **removing friction between user intent and outcome**. The shortlist is built around three loops:

1. **Diverge cheaply** (sketch → wireframe)
2. **Test before committing** (prototype → 5 users)
3. **Standardize what works** (tokens + components)

Skip the first loop and you over-invest in the wrong idea. Skip the second and you ship confusion. Skip the third and every new screen reopens decisions you already made.
