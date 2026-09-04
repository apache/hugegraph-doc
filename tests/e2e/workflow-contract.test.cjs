const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const workflow = fs.readFileSync(
  path.resolve(__dirname, "../../.github/workflows/hugo.yml"),
  "utf8"
);

test("each build fetches and verifies its immutable matrix SHA", () => {
  assert.match(workflow, /RESOLVED_SHA: \$\{\{ matrix\.version\.sha \}\}/);
  assert.match(workflow, /git fetch --no-tags origin "\$RESOLVED_SHA"/);
  assert.match(workflow, /git cat-file -e "\$RESOLVED_SHA\^\{commit\}"/);
});

test("only publish receives write permission and deploy stays read-only", () => {
  const writeMatches = workflow.match(/contents: write/g) || [];
  assert.equal(writeMatches.length, 1);
  assert.match(
    workflow,
    /deploy:[\s\S]*?permissions: \{ contents: read \}[\s\S]*?publish:/
  );
  assert.match(workflow, /publish:[\s\S]*?permissions: \{ contents: write \}/);
});

test("event plan fixes origins, branches, confirmations, and five-version order", () => {
  assert.match(workflow, /selection="latest,1\.7,1\.5,1\.3,1\.0"/);
  assert.match(workflow, /test "\$CONFIRMATION" = "publish asf-staging-oink"/);
  assert.match(workflow, /test "\$CONFIRMATION" = "publish asf-site"/);
  assert.match(workflow, /production:asf-site\|staging:asf-staging-oink/);
  assert.doesNotMatch(workflow, /permissions:\s*write-all/);
});
