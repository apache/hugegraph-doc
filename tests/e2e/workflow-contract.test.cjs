const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const workflow = fs.readFileSync(
  path.resolve(__dirname, "../../.github/workflows/hugo.yml"),
  "utf8"
);
const versionManifest = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "../../versions.json"), "utf8")
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

test("event plan derives runtime selection from versions.json", () => {
  assert.match(
    workflow,
    /all_selection="\$\(jq -er '\[\.versions\[\]\.id\] \| join\(","\)' versions\.json\)"/
  );
  assert.match(
    workflow,
    /latest_selection="\$\(jq -er '\[\.versions\[\] \| select\(\.archived == false\) \| \.id\] \| join\(","\)' versions\.json\)"/
  );
  assert.doesNotMatch(workflow, /selection="latest,1\.7,1\.5,1\.3,1\.0"/);
  assert.match(workflow, /selection="\$all_selection"/);
  assert.match(workflow, /selection="\$latest_selection"/);
  assert.match(workflow, /test "\$candidate" = "\$latest_ref"/);
  assert.deepEqual(
    versionManifest.versions.map(({ id }) => id),
    ["latest", "1.7", "1.5", "1.3", "1.0"],
    "the reviewed manifest still declares the accepted five-version product order"
  );
  assert.match(workflow, /test "\$CONFIRMATION" = "publish asf-staging-oink"/);
  assert.match(workflow, /test "\$CONFIRMATION" = "publish asf-site"/);
  assert.match(workflow, /production:asf-site\|staging:asf-staging-oink/);
  assert.doesNotMatch(workflow, /permissions:\s*write-all/);
});

test("concurrency serializes every writer to the same ASF target", () => {
  assert.match(
    workflow,
    /group: \$\{\{ github\.workflow \}\}-\$\{\{[\s\S]*inputs\.operation == 'staging-next'[\s\S]*'asf-staging-oink'[\s\S]*'asf-site'[\s\S]*\}\}/
  );
  assert.doesNotMatch(
    workflow,
    /group:[^\n]*(?:inputs\.operation \|\| 'automatic'|github\.ref)/
  );
});

test("aggregate binds the option-looking artifact suffix", () => {
  assert.match(
    workflow,
    /--artifact-suffix="-\$\{GITHUB_RUN_ID\}-\$\{GITHUB_RUN_ATTEMPT\}"/
  );
  assert.doesNotMatch(
    workflow,
    /--artifact-suffix\s+"-\$\{GITHUB_RUN_ID\}-\$\{GITHUB_RUN_ATTEMPT\}"/
  );
});

test("prepare pins Hugo and WebP tools before source validators", () => {
  const setupHugo = workflow.indexOf("name: Setup Hugo Extended");
  const setupWebp = workflow.indexOf("name: Install WebP validators");
  const validators = workflow.indexOf("name: Validate source and version tooling");
  assert.ok(setupHugo >= 0 && setupHugo < validators);
  assert.ok(setupWebp >= 0 && setupWebp < validators);
  assert.match(workflow, /apt-get install --yes --no-install-recommends webp/);
  assert.match(workflow, /command -v cwebp[\s\S]*command -v dwebp/);
  assert.match(
    workflow,
    /aggregate[\s\S]*--historical-origin "\$HISTORICAL_ORIGIN"/,
  );
});
