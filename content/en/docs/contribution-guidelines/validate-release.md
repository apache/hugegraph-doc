---
title: "Validate Apache Release"
linkTitle: "Validate Apache Release"
weight: 3
---

> Note: this doc will be updated continuously.
> You need to use Java11 in runtime verification, we will drop Java8 support from version 1.5.0 (And currently doesn't support Java17)
>
> Graduation note: Apache HugeGraph graduated in January 2026. Official release voting is now completed within the HugeGraph community (PMC binding votes on `dev@hugegraph.apache.org`), and no longer requires Incubator `general@incubator.apache.org` approval.

## Verification

When the internal temporary release and packaging work is completed, other community developers (
especially PMC) need to participate in verification based on ASF release policy and checklist references:
- [ASF release policy](https://www.apache.org/legal/release-policy.html)
- [Incubator checklist (historical reference)](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist)
To ensure the "correctness + completeness" of someone's published version, here requires **everyone
** to participate as much as possible, and then explain which items you have **checked** in the
subsequent **email reply**.(The following are the core items)

#### 1. prepare

If there is no svn or gpg or wget environment locally, it is recommended to install it first 
(windows recommend using WSL2 environment, or at least `git-bash`), also make sure to install java 
(prefer Java 11) and maven software

```bash
# 1. install svn
# ubuntu/debian
sudo apt install subversion -y
# MacOS
brew install subversion
# To verify that the installation was successful, execute the following command:
svn --version

# 2. install gpg
# ubuntu/debian
sudo apt-get install gnupg -y
# MacOS
brew install gnupg
# To verify that the installation was successful, execute the following command:
gpg --version

# 3. install wget (we will enhance it later, like use `curl`)
# ubuntu/debian
sudo apt-get install wget -y
# MacOS
brew install wget

# 4. Download the hugegraph-svn directory 
# For version number, pay attention to fill in the verification version
svn co https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/
# (Note) If svn downloads a file very slowly, 
# you can consider wget to download a single file, as follows (or consider using a proxy)
wget https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/apache-hugegraph-toolchain-incubating-1.x.x.tar.gz
```

#### 2. check hash value

First you need to check the file integrity of the `source + binary` package, Verify by `shasum` to
ensure that it is consistent with the hash value published on apache/GitHub (Usually sha512), Here
is the same as the last step of 0x02 inspection.

```bash
execute the following command:
for i in *.tar.gz; do echo $i; shasum -a 512 --check  $i.sha512; done
```

#### 3. check gpg signature

This is to ensure that the published package is uploaded by a **reliable** person.
Assuming tom signs and uploads,
others should download A's **public key** and then perform **signature
confirmation**.

Related commands:

```bash
# 1. Download project trusted public key to local (required for the first time) & import
curl  https://downloads.apache.org/hugegraph/KEYS > KEYS
gpg --import KEYS

# After importing, you can see the following output, which means that x user public keys have been imported
gpg: /home/ubuntu/.gnupg/trustdb.gpg: trustdb created
gpg: key BA7E78F8A81A885E: public key "imbajin (apache mail) <jin@apache.org>" imported
gpg: key 818108E7924549CC: public key "vaughn <vaughn@apache.org>" imported
gpg: key 28DCAED849C4180E: public key "coderzc (CODE SIGNING KEY) <zhaocong@apache.org>" imported
...
gpg: Total number processed: x
gpg:               imported: x

# 2. Trust release users (trust n username mentioned in voting mail, if more than one user, 
#      just repeat the steps in turn or use the script below)
gpg --edit-key $USER # input the username, enter the interactive mode
gpg> trust
...output options..
Your decision? 5 # select 5
Do you really want to set this key to ultimate trust? (y/N) y # slect y, then q quits trusting the next user

# (Optional) You could also use the command to trust one user in non-interactive mode:
echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key $USER trust
# Or use the script to auto import all public gpg keys (be carefully):
for key in $(gpg --no-tty --list-keys --with-colons | awk -F: '/^pub/ {print $5}'); do
  echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key "$key" trust
done


# 3. Check the signature (make sure there is no Warning output, every source/binary file prompts Good Signature)
#Single file verification
gpg --verify xx.asc xxx-src.tar.gz
gpg --verify xx.asc xxx.tar.gz # Note: without the bin/binary suffix

# One-click shell traversal verification (recommended)
for i in *.tar.gz; do echo $i; gpg --verify $i.asc $i ; done

```

First confirm the overall integrity/consistency, and then confirm the specific content (**key**)

#### 4. Check the archive contents

Check the contents of the archive downloaded from preparation work. Divided into two aspects: source code package + binary package, The source code package is stricter, it can be said that the core part (Because it is longer, For a complete list refer to
the official [Wiki](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist))

##### A. source package

After decompressing `*hugegraph*src.tar.gz`, Do the following checks:

1. package/folder naming should match the release line (historical releases may still contain `incubating`), and no **empty** files/folders
2. `LICENSE` + `NOTICE` exist and the content is normal; `DISCLAIMER` is required for historical incubating artifacts
3. **does not exist** binaries (without LICENSE)
4. The source code files all contain the standard `ASF License` header (this could be done with
   the `Maven-MAT` plugin)
5. Check whether the `pom.xml` version number of each parent/child module is consistent (and meet
   expectations)
6. Finally, make sure the source code works/compiles correctly

```bash
# prefer to use/switch to `java 11` for the following operations (compiling/running) (Note: `Computer` only supports `java >= 11`)
# java --version

# try to compile in the Unix env to check if it works well (-P is optional)
mvn clean package -P stage -DskipTests -Dcheckstyle.skip=true
```

##### B. binary package

After decompressing `xxx-hugegraph.tar.gz`, perform the following checks:

1. package/folder naming should match the release line (historical releases may still contain `incubating`)
2. `LICENSE` and `NOTICE` file exists and the content is normal (`DISCLAIMER` applies to historical incubating artifacts)
3. start server

```bash
# hugegraph-server
bin/start-hugegraph.sh

# hugegraph-loader
bin/hugegraph-loader.sh -g hugegraph -f example/file/struct.json -s example/file/schema.groovy

# hugegraph-hubble
bin/start-hubble.sh

more reference official website: https://hugegraph.apache.org/docs/quickstart
```

**Note:** If a third-party dependency is introduced in the binary package, you need to update the
LICENSE and add the third-party dependent LICENSE; if the third-party dependent LICENSE is Apache
2.0, and the corresponding project contains NOTICE, you also need to update Our NOTICE file

#### 5. Check the official website and GitHub and other pages

1. Make sure that the official website at least meets [apache website check](https://whimsy.apache.org/pods/project/hugegraph),
   and no circular links, etc.
2. Update **download link** and release notes updated
3. ...

## Mail Template

After the check & test, you should reply to the mail with the following content: (normal devs & PMC)

```markdown
[] +1 approve

[] +0 no opinion

[] -1 disapprove with the reason
```

```markdown
+1 (non-binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE & DISCLAIMER are exist
4. Build successfully on XX OS & Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XXX service OK
10. ....
```

and the PMC members should reply with `binding`, it's important for summary the valid votes:

```markdown
+1 (binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE & DISCLAIMER are exist
4. Build successfully on XX OS & Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XX process OK
10. ....
```
