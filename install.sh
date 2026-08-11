#!/usr/bin/env bash
#
# p2c installer — installs the p2c skill, agents, and commands into a
# Claude Code configuration directory.
#
#   Interactive:
#     curl -fsSL https://raw.githubusercontent.com/dgmiller81/p2c-claude-plugin/main/install.sh | bash
#
#   Non-interactive:
#     ... | bash -s -- --user
#     ... | bash -s -- --project /path/to/repo
#     ... | bash -s -- --user --uninstall
#
# Prompts run against /dev/tty, so piping the script into bash still works.

set -euo pipefail

REPO="dgmiller81/p2c-claude-plugin"
REF="${P2C_REF:-main}"
TARBALL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}"

SCOPE=""
PROJECT_DIR=""
UNINSTALL=0
ASSUME_YES=0

bold=$'\033[1m'; dim=$'\033[2m'; red=$'\033[31m'; grn=$'\033[32m'; ylw=$'\033[33m'; rst=$'\033[0m'
if [ ! -t 1 ]; then bold=""; dim=""; red=""; grn=""; ylw=""; rst=""; fi

say()  { printf '%s\n' "$*"; }
info() { printf '  %s\n' "$*"; }
ok()   { printf '  %s%s%s\n' "$grn" "$*" "$rst"; }
warn() { printf '  %s%s%s\n' "$ylw" "$*" "$rst"; }
die()  { printf '%serror:%s %s\n' "$red" "$rst" "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
p2c installer

  --user                Install for the current user (~/.claude)
  --project [DIR]       Install into a project (DIR/.claude, default: cwd)
  --uninstall           Remove a previous install from the chosen scope
  --yes                 Do not prompt; requires --user or --project
  --ref REF             Install from a branch or tag (default: main)
  -h, --help            Show this help

With no flags the installer asks which scope you want.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --user)      SCOPE="user"; shift ;;
    --project)   SCOPE="project"
                 if [ $# -ge 2 ] && [ "${2#-}" = "$2" ]; then PROJECT_DIR="$2"; shift 2; else shift; fi ;;
    --uninstall) UNINSTALL=1; shift ;;
    --yes|-y)    ASSUME_YES=1; shift ;;
    --ref)       [ $# -ge 2 ] || die "--ref needs a value"; REF="$2"; TARBALL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}"; shift 2 ;;
    -h|--help)   usage; exit 0 ;;
    *)           die "unknown option: $1 (try --help)" ;;
  esac
done

# ---------------------------------------------------------------- prompting

# Piping into bash makes stdin the script itself, so read from the terminal.
have_tty() { [ -r /dev/tty ] && [ -w /dev/tty ]; }

# ask <prompt> -> echoes the reply. Returns 1 on EOF, so callers can tell a
# bare Enter (use the default) apart from no interactive input at all (a
# headless run that should fail loudly rather than pick a default for you).
ask() {
  local prompt="$1" reply="" status=0
  have_tty || return 1
  printf '%s' "$prompt" > /dev/tty 2>/dev/null || return 1
  IFS= read -r reply < /dev/tty 2>/dev/null || status=1
  printf '%s' "$reply"
  return $status
}

choose_scope() {
  have_tty || die "no terminal available for prompting — pass --user or --project DIR"
  say ""
  say "${bold}Where should p2c be installed?${rst}"
  say ""
  say "  ${bold}1${rst}) This user      ${dim}~/.claude${rst}"
  say "     Available in every project you open."
  say ""
  say "  ${bold}2${rst}) One project    ${dim}<project>/.claude${rst}"
  say "     Scoped to a single repo. Commit it and your whole team gets p2c."
  say ""
  local reply
  while :; do
    if ! reply="$(ask "Choose 1 or 2 [1]: ")"; then
      say ""
      die "no interactive input available — pass --user or --project DIR"
    fi
    case "${reply:-1}" in
      1) SCOPE="user"; return ;;
      2) SCOPE="project"; return ;;
      *) warn "Enter 1 or 2." ;;
    esac
  done
}

# ---------------------------------------------------------------- resolve target

[ -n "$SCOPE" ] || choose_scope

case "$SCOPE" in
  user)
    DEST="${HOME}/.claude"
    LABEL="this user"
    ;;
  project)
    if [ -z "$PROJECT_DIR" ]; then
      if [ "$ASSUME_YES" -eq 1 ]; then
        PROJECT_DIR="$PWD"
      else
        reply="$(ask "Project directory [${PWD}]: ")"
        PROJECT_DIR="${reply:-$PWD}"
      fi
    fi
    # Expand a leading ~ without eval.
    case "$PROJECT_DIR" in "~"|"~/"*) PROJECT_DIR="${HOME}${PROJECT_DIR#\~}" ;; esac
    [ -d "$PROJECT_DIR" ] || die "not a directory: $PROJECT_DIR"
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd -P)"
    DEST="${PROJECT_DIR}/.claude"
    LABEL="project ${PROJECT_DIR}"
    ;;
  *) die "internal: bad scope '$SCOPE'" ;;
esac

# ---------------------------------------------------------------- uninstall

remove_install() {
  local removed=0
  if [ -d "${DEST}/skills/p2c" ]; then rm -rf "${DEST}/skills/p2c"; ok "removed skills/p2c"; removed=1; fi
  for a in business-analyst lead-architect lead-developer lead-qa-coordinator \
           lead-ux-designer product-owner research-marketing scrum-master; do
    if [ -f "${DEST}/agents/${a}.md" ]; then rm -f "${DEST}/agents/${a}.md"; removed=1; fi
  done
  [ "$removed" -eq 1 ] && ok "removed p2c agents" || true
  local found=0
  for c in "${DEST}"/commands/p2c-*.md; do
    [ -e "$c" ] || continue
    rm -f "$c"; found=1
  done
  [ "$found" -eq 1 ] && ok "removed p2c- commands" || true
  [ "$removed" -eq 1 ] || [ "$found" -eq 1 ] || warn "nothing to remove in ${DEST}"
}

if [ "$UNINSTALL" -eq 1 ]; then
  say ""
  say "${bold}Uninstalling p2c${rst} from ${LABEL}"
  say "  ${dim}${DEST}${rst}"
  say ""
  if [ "$ASSUME_YES" -ne 1 ] && have_tty; then
    reply="$(ask "Proceed? [y/N]: ")"
    case "$reply" in [yY]*) ;; *) say "Aborted."; exit 0 ;; esac
  fi
  remove_install
  say ""
  ok "Done. Restart Claude Code."
  exit 0
fi

# ---------------------------------------------------------------- fetch

command -v curl >/dev/null 2>&1 || die "curl is required"
command -v tar  >/dev/null 2>&1 || die "tar is required"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

say ""
say "${bold}Installing p2c${rst} for ${LABEL}"
say "  ${dim}source: ${REPO}@${REF}${rst}"
say "  ${dim}target: ${DEST}${rst}"
say ""

info "Downloading…"
curl -fsSL "$TARBALL" -o "${TMP}/p2c.tar.gz" \
  || die "download failed — check the ref '${REF}' exists and you have network access"
tar -xzf "${TMP}/p2c.tar.gz" -C "$TMP" || die "could not extract archive"

# Archive root is <repo>-<ref>/, so plugins/p2c sits three levels below $TMP.
SRC="$(find "$TMP" -maxdepth 4 -type d -path '*/plugins/p2c' -print -quit)"
[ -n "$SRC" ] && [ -d "${SRC}/skills/p2c" ] || die "archive layout unexpected — plugins/p2c not found"

# ---------------------------------------------------------------- confirm overwrite

if [ -d "${DEST}/skills/p2c" ] && [ "$ASSUME_YES" -ne 1 ] && have_tty; then
  warn "An existing p2c install is present at ${DEST}/skills/p2c"
  reply="$(ask "Overwrite it? [y/N]: ")"
  case "$reply" in [yY]*) ;; *) say "Aborted. Nothing changed."; exit 0 ;; esac
fi

# ---------------------------------------------------------------- install

mkdir -p "${DEST}/skills/p2c" "${DEST}/agents" "${DEST}/commands"

rm -rf "${DEST}/skills/p2c"
mkdir -p "${DEST}/skills/p2c"
cp -R "${SRC}/skills/p2c/." "${DEST}/skills/p2c/"
ok "skill        → ${DEST}/skills/p2c"

cp "${SRC}/agents/"*.md "${DEST}/agents/"
ok "agents (8)   → ${DEST}/agents"

# Flat installs have no ':' namespacing, so prefix commands to avoid collisions.
n=0
for f in "${SRC}/commands/"*.md; do
  base="$(basename "$f" .md)"
  cp "$f" "${DEST}/commands/p2c-${base}.md"
  n=$((n + 1))
done
ok "commands (${n}) → ${DEST}/commands  (as /p2c-*)"

# ---------------------------------------------------------------- deps

say ""
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else PY=""; fi

if [ -n "$PY" ] && "$PY" -c "import yaml" >/dev/null 2>&1; then
  ok "PyYAML present ($("$PY" --version 2>&1))"
else
  warn "PyYAML not found. trace.py and estimate_cost.py need it:"
  info "  pip install pyyaml"
fi

# ---------------------------------------------------------------- done

say ""
say "${bold}Installed.${rst} Restart Claude Code, then try ${bold}/p2c-help${rst}."
say ""
if [ "$SCOPE" = "project" ]; then
  info "Commit ${DEST#$PROJECT_DIR/} to share p2c with your team."
  say ""
fi
say "${dim}Prefer '/p2c:help' style namespacing? Install as a plugin instead —${rst}"
say "${dim}run these inside Claude Code (they replace this flat install):${rst}"
say "  /plugin marketplace add ${REPO}"
say "  /plugin install p2c@p2c-marketplace"
say ""
if [ "$SCOPE" = "project" ]; then
  UNINSTALL_ARGS="--project '${PROJECT_DIR}' --uninstall"
else
  UNINSTALL_ARGS="--user --uninstall"
fi
say "${dim}Uninstall: curl -fsSL https://raw.githubusercontent.com/${REPO}/main/install.sh | bash -s -- ${UNINSTALL_ARGS}${rst}"
say ""
