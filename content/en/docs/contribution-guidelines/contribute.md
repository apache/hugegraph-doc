---
title: "Contribute to the HugeGraph Community"
linkTitle: "Contribution Process"
weight: 1
---

## Choose How to Contribute

You can report problems through [GitHub Issues](https://github.com/apache/hugegraph/issues), or contribute code, tests, or documentation. Before starting a substantial change, consider opening an issue that explains its scope to avoid duplicated work.

The following example uses `apache/hugegraph`. The same process applies to other HugeGraph repositories, but follow each repository's `README.md`, `AGENTS.md`, and CI configuration for its build and test commands.

## Prepare the Repository

![Fork the HugeGraph repository on GitHub](/images/docs/contribution/github-fork.png)
{width="884" height="462"}

Fork [apache/hugegraph](https://github.com/apache/hugegraph) on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-name>/hugegraph.git
cd hugegraph
git remote add upstream https://github.com/apache/hugegraph.git
git fetch upstream master
```

Do not develop directly on `master`. Use a separate branch for each change:

```bash
git switch master
git merge --ff-only upstream/master
git switch -c fix/<short-description>
```

## Make and Verify Changes

HugeGraph Server code is under `hugegraph-server/`. For example, the core module is located at:

```text
hugegraph-server/hugegraph-core/src/main/java/org/apache/hugegraph/
```

Run the tests directly related to your change first. Common Server test commands include:

```bash
# Core tests with the in-memory backend
mvn test -pl hugegraph-server/hugegraph-test -am -P core-test,memory

# API tests with the RocksDB backend
mvn test -pl hugegraph-server/hugegraph-test -am -P api-test,rocksdb

# Format files and verify compilation
mvn editorconfig:format
mvn clean compile -Dmaven.javadoc.skip=true
```

GitHub requires a username and token for Git authentication instead of a username and password. Create a personal access token at https://github.com/settings/tokens:

![Authenticate Git pushes with a personal access token](/images/docs/contribution/github-authentication.png)
{width="1280" height="422"}

When adding a third-party dependency, also update the license information included in the distribution:

1. Add the dependency's license file to `hugegraph-server/hugegraph-dist/release-docs/licenses/`.
2. Update `hugegraph-server/hugegraph-dist/release-docs/LICENSE`. If the dependency includes a NOTICE file, update `NOTICE` as well.
3. Run `hugegraph-server/hugegraph-dist/scripts/dependency/regenerate_known_dependencies.sh` to update the known-dependency list.

## Submit a Pull Request

Make sure the email address used for your commits is associated with your GitHub account. See https://github.com/settings/emails for instructions:

![Verify your commit email on GitHub](/images/docs/contribution/github-email.png)
{width="1280" height="592"}

Use the `type(module): message` format for commit messages, for example:

```bash
git add <changed-files>
git commit -m "fix(core): handle empty vertex query"
git push -u origin fix/<short-description>
```

Then open a pull request from your fork branch to `apache/hugegraph:master`. Explain the problem, the implementation, and the validation commands you actually ran. Include screenshots for UI changes.

## Address Review Feedback

If CI fails or a reviewer requests changes, continue committing and pushing to the same branch. Rebase when you need to synchronize with upstream:

```bash
git fetch upstream master
git rebase upstream/master
git push --force-with-lease
```

Do not overwrite the remote branch with plain `--force`. After all CI and review requirements are satisfied, a project maintainer will merge the pull request.

Contributor agreements follow the official ASF process. See the [Contributor Agreement]({{< ref path="/docs/CLA.md" lang="en" >}}).
