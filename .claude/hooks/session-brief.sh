#!/usr/bin/env bash
# SessionStart hook. Prints a short brief for this session. Claude Code adds the text to
# the context on start, resume, /clear and after a compaction, so a fresh or compacted
# session starts from the same state: branch, files to read, handoff note.
# It never blocks. Static rules stay in CLAUDE.md: this prints only what changes.

if [ -t 0 ]; then input="{}"; else input="$(cat)"; fi

# The cwd field of the hook input is the tree this session works in, also in a worktree.
cwd="$(printf '%s' "$input" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("cwd", ""))' 2>/dev/null)"
root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null)" || root="${CLAUDE_PROJECT_DIR:-}"
[ -n "$root" ] || exit 0
cd "$root" || exit 0

origin="$(printf '%s' "$input" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("source", "start"))' 2>/dev/null)"
[ -n "$origin" ] || origin="start"
branch="$(git branch --show-current 2>/dev/null)"
[ -n "$branch" ] || branch="(detached)"

session="lead"
brief=""
child=""
case "$branch" in
  area/*)
    area="${branch#area/}"
    area="${area%%-[0-9]*}" # area/vetting-2 is a replay of the vetting area
    if [ -f "briefs/area-$area.md" ]; then
      session="$area"
      brief="briefs/area-$area.md"
      child="docs/specs/$area.md"
    fi
    ;;
  setup)
    brief="briefs/00-setup.md, then briefs/10-contracts.md"
    child="docs/specs/delivery.md"
    ;;
  integration)
    brief="briefs/90-integrate.md"
    child="docs/specs/delivery.md"
    ;;
esac
note="handoff/$session.md"

echo "Session brief (source: $origin)"
echo "Branch: $branch. Session: $session."
if [ -n "$brief" ]; then
  echo "Read, if not yet in this conversation: docs/specs/mcp-greenroom.md, $child, $brief. No other child spec."
else
  echo "Lead session. The user gives the prompt for each phase."
fi

changed="$(git status --short 2>/dev/null | head -n 15)"
if [ -n "$changed" ]; then
  echo "Uncommitted files:"
  printf '%s\n' "$changed"
else
  echo "Working tree clean."
fi
echo "Last commits:"
git log --oneline -5 2>/dev/null || echo "(none yet)"

echo
if [ -f "$note" ]; then
  echo "Handoff note, $note. An earlier session wrote it: check it against the commits above."
  head -n 60 "$note"
else
  echo "No handoff note yet at $note. The handoff skill writes it."
fi
exit 0
