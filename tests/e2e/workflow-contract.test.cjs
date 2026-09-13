const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const workflow = fs.readFileSync(
  path.resolve(__dirname, "../../.github/workflows/hugo.yml"),
  "utf8"
);

test("only publish receives write permission", () => {
  assert.equal((workflow.match(/: write\b/g) || []).length, 1);
  assert.doesNotMatch(workflow, /write-all/);
  assert.match(workflow, /publish:[\s\S]*?contents: write/);
});
