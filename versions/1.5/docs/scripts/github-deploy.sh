#!/bin/bash
set -x
# this script is for developers to manually deploy doc to GitHub Pages
REMOTE="github"
REMOTE_URL="https://github.com/hugegraph/hugegraph-doc"
REPO="hugegraph-doc"
BRANCH_BUILD="master"
BRANCH_PAGES="gh-pages"
BUILD_OUTPUT="_book"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ $BRANCH != "$BRANCH_BUILD" ]; then
    echo "Must deploy $REPO on branch $BRANCH_BUILD."
    exit 1
fi

echo "Building $REPO..."
git pull && gitbook build || exit 1

echo "Committing(locally) to $BRANCH_PAGES..."
LAST_COMMIT=$(git log -1 --oneline)

# ensure BRANCH_PAGES exist
git remote | grep $REMOTE > /dev/null
if [ $? -ne 0 ]; then
    git remote add $REMOTE $REMOTE_URL
fi
git rev-parse --verify $BRANCH_PAGES > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Pulling $REMOTE/$BRANCH_PAGES..."
    git pull $REMOTE $BRANCH_PAGES
    git checkout -b $BRANCH_PAGES $REMOTE/$BRANCH_PAGES || exit 1
else
    git checkout $BRANCH_PAGES || exit 1
fi
# commit to BRANCH_PAGES
cp -r $BUILD_OUTPUT/* ./ && git add . && git commit -m "$LAST_COMMIT" || exit 1

echo "Publishing $REPO to $REMOTE/$BRANCH_PAGES..."
git push $REMOTE || exit 1

git checkout "$BRANCH_BUILD" || exit 1
echo "Deployed $REPO successfully!"

