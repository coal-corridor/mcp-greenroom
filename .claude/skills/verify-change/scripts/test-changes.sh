#!/usr/bin/env bash
# Lists what changed in the tests since a base ref, working tree included, so that a
# weakened test is seen and not guessed: removed assertions, new skip or xfail markers,
# removed test functions. It reports and always exits 0, except on a bad base ref.
#
#   test-changes.sh [base]     base defaults to main

base="${1:-main}"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "test-changes: not inside a git repository." >&2
  exit 2
}
cd "$root" || exit 2
if ! git rev-parse --verify --quiet "$base^{commit}" >/dev/null; then
  echo "test-changes: no commit named '$base'." >&2
  echo "Expected a branch or commit to compare with. Pass one as the first argument." >&2
  exit 2
fi
from="$(git merge-base "$base" HEAD 2>/dev/null)" || from="$base"

diff="$(git diff "$from" -- tests evals)"
removed_asserts="$(printf '%s\n' "$diff" | grep -E '^-[^-].*\bassert' || true)"
skips="$(printf '%s\n' "$diff" | grep -E '^\+[^+].*(skip|xfail)' || true)"
removed_defs="$(printf '%s\n' "$diff" | grep -E '^-[[:space:]]*(async )?def test_' | sed -E 's/^-[[:space:]]*(async )?def (test_[A-Za-z0-9_]*).*/\2/' | sort -u || true)"
added_defs="$(printf '%s\n' "$diff" | grep -E '^\+[[:space:]]*(async )?def test_' | sed -E 's/^\+[[:space:]]*(async )?def (test_[A-Za-z0-9_]*).*/\2/' | sort -u || true)"
gone="$(comm -23 <(printf '%s\n' "$removed_defs") <(printf '%s\n' "$added_defs") | grep -v '^$' || true)"

count() { if [ -z "$1" ]; then echo 0; else printf '%s\n' "$1" | wc -l | tr -d ' '; fi; }

echo "Test changes since $base ($(git rev-parse --short "$from")), working tree included"
echo
echo "Files:"
git diff --stat "$from" -- tests evals | sed 's/^/  /'
echo
echo "Removed assertions: $(count "$removed_asserts")"
[ -n "$removed_asserts" ] && printf '%s\n' "$removed_asserts" | sed 's/^/  /'
echo "New skip or xfail markers: $(count "$skips")"
[ -n "$skips" ] && printf '%s\n' "$skips" | sed 's/^/  /'
echo "Removed test functions: $(count "$gone")"
[ -n "$gone" ] && printf '%s\n' "$gone" | sed 's/^/  /'
echo
echo "A removed assertion can be a rewrite. Read each one and say why it is right, or restore it."
exit 0
