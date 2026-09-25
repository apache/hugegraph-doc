const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const workflow = fs.readFileSync(
  path.resolve(__dirname, "../../.github/workflows/hugo.yml"),
  "utf8"
);

test("only publish receives write permission", () => {
  const jobsStart = workflow.indexOf("\njobs:\n");
  const jobsSource = jobsStart < 0 ? "" : workflow.slice(jobsStart + 7);
  const jobs = [
    ...jobsSource.matchAll(
      /^  ([A-Za-z0-9_-]+):\s*\n((?:(?!^  [A-Za-z0-9_-]+:)[\s\S])*)/gm
    )
  ];
  const permissions = jobs.flatMap(([, job, body]) => {
    const inline = body.match(/^    permissions:\s*\{([^}]*)\}/m);
    const block = body.match(
      /^    permissions:\s*\n((?:^      [^\n]+\n?)+)/m
    );
    return [...(inline?.[1] ?? block?.[1] ?? "").matchAll(
      /\b([A-Za-z0-9_-]+):\s*(read|write)\b/g
    )].map(([, scope, level]) => ({ job, scope, level }));
  });
  assert.ok(jobs.length > 0);
  assert.ok(permissions.length > 0);
  assert.equal(
    permissions.filter((permission) => permission.level === "write").length,
    1
  );
  assert.deepEqual(
    permissions.filter((permission) => permission.level === "write"),
    [{ job: "publish", scope: "contents", level: "write" }]
  );
  assert.doesNotMatch(workflow, /write-all/);
});

test("build consumers check out the immutable prepared source SHA", () => {
  assert.match(workflow, /echo "source_sha=\$latest_sha"/);
  const refs = [...workflow.matchAll(/^\s+ref: \$\{\{([^}]+)\}\}/gm)].map((match) => match[1]);
  assert.equal(refs.length, 4);
  assert.doesNotMatch(refs[0], /candidate_branch/);
  assert.equal(refs.slice(1).filter((ref) => ref.includes("needs.prepare.outputs.source_sha")).length, 3);
  assert.doesNotMatch(workflow, /test \"\$GITHUB_REF\" = \"refs\/heads\/\$candidate\"/);
  assert.match(workflow, /test \"\$GITHUB_REF\" = \"refs\/heads\/master\"/);
});

test("trusted workflow bounds the candidate module graph without pinning its version", () => {
  const step = workflow.split("      - name: Verify pinned OINK module\n")[1]
    .split("      - name:")[0];
  assert.match(step, /go list -m -f '\{\{ \.Path \}\}'.*github\.com\/apache\/hugegraph-doc/);
  assert.match(step, /go list -m all \| wc -l.*-eq 2/);
  assert.match(step, /test -z .*\.Replace.*github\.com\/pgsty\/oink/);
  assert.doesNotMatch(step, /github\.com\/pgsty\/oink@v/);
  assert.match(step, /python3 scripts\/update_oink\.py --check-baseline/);
});

test("dependency artifacts keep stable names across selective reruns", () => {
  assert.match(workflow, /name: resolved-versions-\$\{\{ github\.run_id \}\}/);
  assert.match(workflow, /name: \$\{\{ needs\.prepare\.outputs\.artifact_prefix \}\}-\$\{\{ matrix\.version\.id \}\}-\$\{\{ github\.run_id \}\}/);
  assert.match(workflow, /pattern: \$\{\{ needs\.prepare\.outputs\.artifact_prefix \}\}-\*-\$\{\{ github\.run_id \}\}/);
  assert.match(workflow, /--artifact-suffix="-\$\{GITHUB_RUN_ID\}"/);
  assert.match(workflow, /name: hugegraph-site-\$\{\{ needs\.prepare\.outputs\.artifact_prefix \}\}-\$\{\{ github\.run_id \}\}/);
  assert.doesNotMatch(workflow, /name: (?:resolved-versions|hugegraph-site-[^\n]+)-\$\{\{ github\.run_id \}\}-\$\{\{ github\.run_attempt \}\}/);
  assert.equal((workflow.match(/\n\s+overwrite: true/g) ?? []).length, 3);
});

function jobBody(name) {
  const body = workflow.match(new RegExp(`^  ${name}:\\n([\\s\\S]*?)(?=^  [a-z_]+:|$(?![\\s\\S]))`, "m"));
  assert.ok(body, `missing job ${name}`);
  return body[1];
}

test("superseded runs can cancel reporting and the required gate", () => {
  assert.match(workflow, /group:.*format\('pr-\{0\}', github.event.pull_request.number\)/);
  assert.match(workflow, /cancel-in-progress: true/);
  assert.doesNotMatch(workflow, /if: always\(\)/);
  assert.match(jobBody("deploy"), /if: \$\{\{ !cancelled\(\) \}\}/);
});

test("assembly runs blocking browser tests on its local artifact", () => {
  const aggregate = jobBody("aggregate");
  assert.doesNotMatch(workflow, /^  e2e:/m);
  assert.match(aggregate, /SITE_ROOT: \$\{\{ runner.temp \}\}\/public-site/);
  assert.match(aggregate, /run: npm run test:ci/);
  assert.doesNotMatch(aggregate, /continue-on-error:/);
  assert.match(jobBody("deploy"), /needs: \[prepare, build, aggregate\]/);
  assert.match(jobBody("publish"), /needs: \[prepare, deploy\]/);
});

test("required gate rejects failed, skipped and cancelled prerequisites", () => {
  const { spawnSync } = require("node:child_process");
  const gate = jobBody("deploy").split("        run: |\n")[1]
    .split("\n").filter(line => line.startsWith("          "))
    .map(line => line.slice(10)).join("\n");
  const success = { PREPARE_RESULT: "success", BUILD_RESULT: "success", AGGREGATE_RESULT: "success" };
  const run = env => spawnSync("bash", ["-e", "-c", gate], {env: {...process.env, ...env}}).status;
  assert.equal(run(success), 0);
  for (const key of Object.keys(success)) {
    for (const result of ["failure", "skipped", "cancelled"]) {
      assert.notEqual(run({...success, [key]: result}), 0, `${key}=${result}`);
    }
  }
});
