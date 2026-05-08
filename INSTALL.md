# Installing the p2c skill

This folder is a **local Claude Code marketplace** that hosts the `p2c` plugin. Installing the marketplace gives you commands with `:` namespacing (`/p2c:full`, `/p2c:product`, `/p2c:design`, …) and registers the bundled skill and seven sub-agents.

## Layout

```
p2c-skill/
├── .claude-plugin/
│   └── marketplace.json          ← marketplace manifest (this folder is the marketplace)
└── plugins/
    └── p2c/                      ← the plugin
        ├── .claude-plugin/
        │   └── plugin.json
        ├── commands/             ← /p2c:full, /p2c:product, /p2c:design, …
        ├── agents/               ← product-owner, scrum-master, lead-architect, …
        └── skills/p2c/           ← SKILL.md + references/ + scripts/ + assets/ + templates/
```

## Install (recommended — gives `:` namespacing)

In Claude Code, install from GitHub:

```
/plugin marketplace add dgmiller81/p2c-claude-plugin
/plugin install p2c@p2c-marketplace
```

Or from a local clone:

```
/plugin marketplace add /path/to/p2c-claude-plugin
/plugin install p2c@p2c-marketplace
```

Then restart Claude Code (or `/plugin reload` if your version supports it). The skill, agents, and the following commands should be available:

- `/p2c:full` — full Phase 1–8 orchestration
- `/p2c:product` — phases 1–2 + measurement framework
- `/p2c:design` — phase 3
- `/p2c:tech-scope` — phase 4 + sprint scope + cost estimates
- `/p2c:tech-build` — local working POC
- `/p2c:tech-prod` — production build, hardening, launch readiness
- `/p2c:launch` — launch strategy + comms + runbook
- `/p2c:poc` — all-in-one POC + production sprint plan + cost estimate
- `/p2c:help` — print the command map and quick-start

## Updating the plugin

To force Claude Code to check for and pull updates from the marketplace:

```
/plugin marketplace update p2c-marketplace
/plugin install p2c@p2c-marketplace
```

The first line refreshes the marketplace metadata (re-fetches the GitHub repo's `.claude-plugin/marketplace.json` and any plugin source paths it points to). The second re-installs the plugin from that refreshed cache, so new commits land in the active install.

To enable auto-update at startup, open `/plugin`, go to the **Marketplaces** tab, and toggle **Enable auto-update** for `p2c-marketplace`. With auto-update on, Claude Code refreshes the marketplace and updates installed plugins on every launch.

There is no built-in "update all plugins" command — update them one at a time, or rely on auto-update.

## Uninstall

```
/plugin uninstall p2c@p2c-marketplace
/plugin marketplace remove p2c-marketplace
```

## Fallback (no `:` namespacing)

If you don't want plugin/marketplace mechanics and just want the flat commands `/p2c-full`, `/p2c-product`, etc. (or you're on a Claude Code version that doesn't support local marketplaces), drop pieces directly into `~/.claude/`:

```bash
SRC="/h/dev/skills/p2c-skill/plugins/p2c"
DEST="$HOME/.claude"
mkdir -p "$DEST/skills/p2c" "$DEST/agents" "$DEST/commands"
cp -r "$SRC/skills/p2c/." "$DEST/skills/p2c/"
cp "$SRC/agents/"*.md     "$DEST/agents/"
# Rename commands to add the p2c- prefix so they don't collide
for f in "$SRC/commands/"*.md; do
  base=$(basename "$f" .md)
  cp "$f" "$DEST/commands/p2c-$base.md"
done
```

This gives flat commands (`/p2c-full`, `/p2c-product`, etc.) — same behavior, different invocation style.

> **Do not** copy the plugin into `%APPDATA%\Claude\plugins\` or `~/.config/Claude/plugins/`. That folder is for marketplace-managed cache and isn't auto-loaded as a source plugin.

## Python dependency

`scripts/estimate_cost.py` uses `PyYAML` to parse the sprint plan. Install once:

```bash
# Conda (matches the user's CLAUDE.md preference)
conda activate 312
pip install pyyaml

# Or system Python
pip install pyyaml
```

The visual server uses only the Python standard library — no extra deps.

## Verifying

In any working directory:

```
/p2c:help
```

Should print the command map. Then try:

```
/p2c:full
```

…with a brief like *"I want to build a tool that helps freelance designers track invoices."*

Expected behavior: the orchestrator reads its SKILL.md, creates `p2c-workspace/`, asks the first cluster of phase-1 questions, and offers to start the visual server.
