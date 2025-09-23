#!/usr/bin/env bash
set -euo pipefail

# usage: ./release.sh [patch|minor|major]
BUMP=${1:-patch}

# 1. bump version
uv version --bump "$BUMP"
VERSION=$(uv version --short)

echo "Releasing v$VERSION"

# 2. commit the version bump
git add pyproject.toml uv.lock
git commit -m "chore: bump version to $VERSION"

# 3. derive GitHub repo URL (strip .git, convert ssh → https)
REPO_URL=$(git remote get-url origin | sed -E 's/\.git$//' | sed -E 's#^git@github.com:#https://github.com/#')

# 4. find previous tag (if any)
PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

# 5. collect commits for this release
if [ -n "$PREV_TAG" ]; then
  RANGE="$PREV_TAG..HEAD"
else
  RANGE=HEAD
fi

DATE=$(date +%Y-%m-%d)

{
  echo "## [v$VERSION]($REPO_URL/releases/tag/v$VERSION) - $DATE"
  echo
  git log $RANGE --pretty=format:"- %s ([%h]($REPO_URL/commit/%H))" --no-merges
  echo
  echo
} > release_notes.md

# 6. prepend new section to CHANGELOG.md
if [ -f CHANGELOG.md ]; then
  { echo "# Changelog"; echo; cat release_notes.md; tail -n +3 CHANGELOG.md; } > CHANGELOG.new
  mv CHANGELOG.new CHANGELOG.md
else
  echo "# Changelog" > CHANGELOG.md
  echo >> CHANGELOG.md
  cat release_notes.md >> CHANGELOG.md
fi


# 7. amend commit to include changelog
git add CHANGELOG.md release_notes.md pyproject.toml uv.lock
git commit --amend --no-edit

# 8. create tag
git tag v"$VERSION"

# 9. push commit + tag
git push origin main --tags

echo "Release v$VERSION complete!"
