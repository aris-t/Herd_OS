#!/bin/bash
set -e

# Update submodules to their latest commits on main branch
git submodule foreach '
  echo "🔄 Updating $name ..."
  git checkout main
  git pull origin main
'

# Stage all submodule pointer updates in the parent repo
echo "📦 Staging updated submodules in parent repo..."
git add $(git submodule--helper list | awk '{ print $4 }')

# Commit and push
echo "✅ Committing update..."
git commit -m "Auto-update submodules to latest commits on main" || echo "ℹ️ Nothing to commit."

echo "🚀 Pushing..."
git push