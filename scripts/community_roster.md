# Community roster data

`roster.json` is the checked-in, visitor-facing snapshot of current Apache
HugeGraph PMC members and Committers. It is generated from the three ASF public
sources recorded in the file:

```bash
python3 scripts/community_roster.py refresh
python3 scripts/community_roster.py validate --warn-after-days 90
```

`refresh` is a maintainer-run operation. It finishes all source, role, mapping,
and avatar checks before atomically replacing the last-good roster. It never
pushes or opens a pull request.

`github-map.json` is deliberately maintained by human review. A mapping must
record both the exact GitHub login and the account's numeric GitHub user ID.
Do not derive mappings from a person's name, email address, employer, or commit
history. Leave an ASF ID unmapped until a maintainer has confirmed the account.

Mapped avatars are downloaded during refresh, converted with `cwebp` when
needed, stripped of metadata, checked as 128 by 128 WebP, and stored under a
SHA-256 content-addressed filename. Unmapped members render initials and link
to the ASF phonebook without requiring JavaScript.
