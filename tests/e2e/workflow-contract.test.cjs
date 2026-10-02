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
  assert.match(workflow, /name: \$\{\{ needs\.prepare\.outputs\.artifact_prefix \}\}-versions-\$\{\{ matrix\.group\.id \}\}-\$\{\{ github\.run_id \}\}/);
  assert.match(workflow, /--artifacts version-artifacts --workers 2/);
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
  assert.match(jobBody("aggregate"), /if: \$\{\{ !cancelled\(\) \}\}/);
});

test("assembly runs blocking browser tests on its local artifact", () => {
  const aggregate = jobBody("aggregate");
  assert.doesNotMatch(workflow, /^  e2e:/m);
  assert.match(aggregate, /SITE_ROOT: \$\{\{ runner.temp \}\}\/public-site/);
  assert.match(aggregate, /run: npm run test:ci/);
  assert.doesNotMatch(aggregate, /continue-on-error:/);
  assert.match(aggregate, /^    name: deploy$/m);
  assert.match(aggregate, /needs: \[prepare, build\]/);
  assert.doesNotMatch(workflow, /^  deploy:/m);
  assert.match(jobBody("publish"), /needs: \[prepare, aggregate\]/);
});

test("required gate rejects failed, skipped and cancelled prerequisites", () => {
  const { spawnSync } = require("node:child_process");
  const aggregate = jobBody("aggregate");
  assert.match(aggregate, /if: \$\{\{ !cancelled\(\) \}\}/);
  assert.match(aggregate, /steps:\n      - name: Require all blocking predecessors to succeed/);
  assert.ok(aggregate.indexOf('test "$BUILD_RESULT" = success') < aggregate.indexOf("- uses: actions/checkout@"));
  assert.match(aggregate, /PREPARE_RESULT: \$\{\{ needs.prepare.result \}\}/);
  assert.match(aggregate, /BUILD_RESULT: \$\{\{ needs.build.result \}\}/);
  const gate = aggregate.split("        run: |\n")[1].split("      - uses:")[0]
    .split("\n").filter(line => line.startsWith("          "))
    .map(line => line.slice(10)).join("\n");
  const success = { PREPARE_RESULT: "success", BUILD_RESULT: "success" };
  const run = env => spawnSync("bash", ["-e", "-c", gate], {env: {...process.env, BASH_ENV: "", ...env}}).status;
  assert.equal(run(success), 0);
  for (const key of Object.keys(success)) {
    for (const result of ["failure", "skipped", "cancelled"]) {
      assert.notEqual(run({...success, [key]: result}), 0, `${key}=${result}`);
    }
  }
});


test("version work uses bounded groups and preserves full validation", () => {
  const build = jobBody("build");
  assert.match(build, /max-parallel: 3/);
  assert.match(build, /fromJSON\(needs.prepare.outputs.groups\)/);
  assert.match(build, /scripts\/build_versions\.py/);
  assert.match(build, /--workers 2/);
  assert.match(build, /name: Restore historical artifact bundle/);
  assert.match(build, /if: github.event_name != 'workflow_dispatch'/);
  assert.match(build, /scripts\/version_cache\.py plan/);
  assert.match(jobBody("aggregate"), /scripts\/versioning\.py aggregate/);
  assert.match(jobBody("publish"), /keep_files: false/);
});


test("warm reruns exclude stale cold-group artifacts and only complete caches are saved", () => {
  const prepare = jobBody("prepare");
  assert.match(prepare, /lookup-only: true/);
  assert.match(prepare, /echo 'pattern=0'/);
  assert.match(jobBody("aggregate"), /versions-\$\{\{ needs\.prepare\.outputs\.group_pattern \}\}/);
  assert.match(jobBody("aggregate"), /merge-multiple: true/);
  assert.match(jobBody("build"), /--expected-plan resolved\/cache-plan\.json/);
  assert.match(jobBody("aggregate"), /if: steps.history-record.outputs.complete == 'true'/);
});

test("cache recording failures cannot block an already validated site", () => {
  const { spawnSync } = require("node:child_process");
  const os = require("node:os");
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "history-record-"));
  const block = jobBody("aggregate").split("      - name: Record validated historical artifacts\n")[1]
    .split("      - name: Save complete historical bundle\n")[0];
  const script = block.split("        run: |\n")[1].split("\n")
    .filter(line => line.startsWith("          ")).map(line => line.slice(10)).join("\n");
  try {
    fs.mkdirSync(path.join(directory, "resolved"));
    fs.writeFileSync(path.join(directory, "resolved/cache-plan.json"), JSON.stringify({
      versions: [{id: "latest", archived: false}, {id: "1.7", archived: true}]
    }));
    for (const code of [0, 1]) {
      fs.writeFileSync(path.join(directory, "python3"), `#!/bin/sh\nexit ${code}\n`, {mode: 0o755});
      const output = path.join(directory, `outputs-${code}`);
      const result = spawnSync("bash", ["-e", "-c", script], {
        cwd: directory,
        env: {...process.env, BASH_ENV: "", PATH: `${directory}:${process.env.PATH}`, GITHUB_OUTPUT: output, RUNNER_TEMP: directory}
      });
      assert.equal(result.status, 0, result.stderr.toString());
      assert.equal(fs.readFileSync(output, "utf8"), `complete=${code === 0}\n`);
    }
  } finally {
    fs.rmSync(directory, {recursive: true, force: true});
  }
});


test("cache lookup and restore outages fall back without bypassing tests", () => {
  for (const [job, id] of [["prepare", "history-lookup"], ["build", "history-cache"]]) {
    assert.match(jobBody(job), new RegExp(`id: ${id}\\n        continue-on-error: true`));
    assert.equal((jobBody(job).match(/continue-on-error:/g) ?? []).length, 1);
  }
  assert.match(jobBody("prepare"), /history-lookup.outcome == 'success'/);
  assert.doesNotMatch(jobBody("aggregate"), /continue-on-error:/);
});


test("fingerprints use the same resolved Python patch on all version runners", () => {
  assert.match(jobBody("prepare"), /python_version: \$\{\{ steps.python.outputs.python-version \}\}/);
  for (const job of ["build", "aggregate"]) {
    assert.match(jobBody(job), /python-version: \$\{\{ needs.prepare.outputs.python_version \}\}/);
  }
});
