---
title: "Apache HugeGraph Committer Guide"
linkTitle: "Apache HugeGraph Committer Guide"
weight: 5
---

> This document outlines the requirements and process for becoming an Apache Committer. The corresponding ASF official document can be found at: https://community.apache.org/newcommitter.html

# Candidate Requirements

1. Candidates must adhere to the [Apache Code of Conduct](https://www.apache.org/foundation/policies/conduct.html).
2. PMC members will assess candidates' interactions with others and contributions through [mailing lists](https://lists.apache.org/list?dev@hugegraph.apache.org), [issues](https://github.com/apache/hugegraph/issues), [pull requests](https://github.com/apache/hugegraph/pulls), and [official documentation](https://hugegraph.apache.org/docs).
3. Considerations for evaluating candidates as potential Committers include:
   1. Ability to collaborate with community members
   2. Mentorship capabilities
   3. Community involvement
   4. Level of contribution
   5. Personal skills/abilities

# Nomination Process

**Discussion → Vote → Invitation → Announcement**

## Initiate Community Discussion (DISCUSS)

Any PMC member of HugeGraph can initiate a voting discussion. After identifying valuable contributions from a community contributor and obtaining the candidate's consent, a discussion can be initiated via private@hugegraph.apache.org.
The initiator of the discussion should clearly state the candidate's contributions in the discussion email and provide URLs or other information for confirming the contributions, facilitating discussion and analysis.

Below is a template for HugeGraph emails: (For reference only)

> Note: The term `xxx` will be used to refer to the candidate. Typically, `xxx` represents an easily readable name (e.g., `Simon Jay`). 
> 
> ASF-INFRA recommends **avoiding** the use of less readable `ID` directly as a reference to the person in emails (e.g., avoid `simon321` or `wh0isSim0n` 😄).
>
> In addition, it is best to choose the **"pure text"** mode, otherwise the typesetting may be chaotic in the ASF Mailing-list UI

```markdown
To: private@hugegraph.apache.org
Subject: [DISCUSS] XXX as a HugeGraph Committer Candidate

Hi all:

I am pleased to nominate xxx for the role of HugeGraph Committer based on his/her contributions over the past few months.

[ Candidate's Contribution Summary ]

Here are the relevant PRs (issues) he/she has participated in:

**Core Features:**
- Feature 1: [ Reference Links ]
- ...

**Fix/Chore/Release:**

**Doc:**

[ Candidate's Current Notable Contributions ]

His/Her contributions bring the following benefits to the community, helping us in the following ways:

[ Candidate's Contributions and Benefits to the Community ]

In view of the above contributions, I elect xxx as Committer of the HugeGraph project.

[ Reference Links ]
1. PR1
2. PR2
3. ...

Welcome everyone to share opinions~

Thanks!
```

For contribution links in discussion emails, you can use the statistical feature of [GitHub Search](https://github.com/search) by entering corresponding keywords as needed. You can also adjust parameters and add new repositories such as `repo:apache/hugegraph-computer`. Pay special attention to adjusting the **time range** (below is a template reference, please adjust the parameters accordingly):

- Number of PR submissions
  - `is:pr author:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Lines of code submissions/changes
  - https://github.com/apache/hugegraph/graphs/contributors?from=2023-06-01&to=2023-12-25&type=c
  - https://github.com/apache/hugegraph-doc/graphs/contributors?from=2023-06-01&to=2023-12-25&type=c
- Number of PR submissions associated with issues
  - `linked:issue involves:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Number of PR reviews
  - `type:pr reviewed-by:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Number of merge commits
  - `type:pr author:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Effective lines merged
  - https://github.com/apache/hugegraph/graphs/contributors?from=2023-06-01&to=2023-12-25&type=c
  - https://github.com/apache/hugegraph-doc/graphs/contributors?from=2023-06-01&to=2023-12-25&type=c
- Number of issue submissions
  - `type:issue author:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Number of issue fixes
  - Based on the number of issue submissions, select those with a closed status.
- Number of issue participations
  - `type:issue involves:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Number of issue comments
  - `type:issue commenter:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`
- Number of PR comments
  - `type:pr commenter:xxx repo:apache/hugegraph repo:apache/hugegraph-doc created:>2023-06-01 updated:<2023-12-25`

For participation in mailing lists, you can use https://lists.apache.org/list?dev@hugegraph.apache.org:lte=10M:xxx.

## Initiate Community Voting Email (VOTE)

If there are no dissenting opinions within the specified time frame of the discussion email, the initiator of the discussion needs to initiate a voting email for the committer election at private@hugegraph.apache.org.

Below is the corresponding email template:

```text
To: private@hugegraph.apache.org
Subject: [VOTE] xxx as a HugeGraph Committer

Hi all:

Through the discussion of last week:
[ Discussion Mailing List Link ]

We have discussed and listed what xxx participated in the HugeGraph community.
I believe making him/her a Committer will enhance the work for HugeGraph. 

So, I am happy to call VOTE to accept xxx as a HugeGraph Committer.
 
Voting will continue for at least 72 hours or until the required number of votes is reached.
 
Please vote accordingly:
[ ] +1 approve
[ ] +0 no opinion
[ ] -1 disapprove with the reason  

Thanks!
```

Then, PMC members reply to the email with +1 or -1 to express their opinions. Generally, at least 3 votes of +1 are needed to conclude the vote.

## Announcement of Voting Results (RESULT)

After the voting email concludes, the initiator of the vote needs to remind the end of the voting in the email. Additionally, the initiator needs to announce the voting results via email to private@hugegraph.apache.org. The email template can be as follows:

```text
To: private@hugegraph.apache.org
Subject: [RESULTS][VOTE] xxx as a HugeGraph Committer

Hi all: The vote for "xxx" as a HugeGraph Committer has PASSED and closed now.

The result is as follows: X PMC +1 Votes: 
- A (PMC ID)
- B
- C...

Vote thread:
put vote thread link here
 
Then I'm going to invite xxx to join us soon. Thanks for everyone's support!
```

## Send Invitation Email to Candidate (INVITE)

After the announcement of the voting results email is sent, the initiator of the vote should send an invitation email to the candidate. The invitation email is addressed to the candidate and cc'd to private@hugegraph.apache.org. The invited candidate must reply to the specified email address to accept or reject the invitation.

Below is a template for reference:

```text
To: [ Candidate's Email ]
Cc: private@hugegraph.apache.org
Subject: Invitation to become HugeGraph committer: xxx

Hello xxx,

The HugeGraph Project Management Committee (PMC)
hereby offers you committer privileges to the project.
These privileges are offered on the understanding that you'll use them
reasonably and with common sense. We like to work on trust
rather than unnecessary constraints.

Being a committer enables you to more easily make
changes without needing to go through the patch
submission process.

Being a committer does not require you to
participate any more than you already do. It does
tend to make one even more committed.  You will
probably find that you spend more time here.

Of course, you can decline and instead remain as a
contributor, participating as you do now.

A. This personal invitation is a chance for you to
accept or decline in private.  Either way, please
let us know in reply to the private@hugegraph.apache.org
address only.

B. If you accept, the next step is to register an iCLA:
    1. Details of the iCLA and the forms are found
    through this link: https://www.apache.org/licenses/#clas

    2. Instructions for its completion and return to
    the Secretary of the ASF are found at
    https://www.apache.org/licenses/#submitting

    3. When you transmit the completed iCLA, request
    to notify the Apache HugeGraph project and choose a
    unique Apache ID. Look to see if your preferred
    ID is already taken at
    https://people.apache.org/committer-index.html
    This will allow the Secretary to notify the PMC
    when your iCLA has been recorded.

When recording of your iCLA is noted, you will
receive a follow-up message with the next steps for
establishing you as a committer.

With the expectation of your acceptance, welcome!

The Apache HugeGraph PMC
```

## Candidate Accepts Invitation (ACCEPT)

The candidate should reply to the aforementioned email (select **reply all**) to indicate acceptance of the invitation. Below is a template for the email:

```text
To: [ Sender's Email ]
Cc: private@hugegraph.apache.org
Subject: Re: Invitation to become HugeGraph committer: xxx

Hello Apache HugeGraph PMC,

I accept the invitation.

Thanks to the Apache HugeGraph Community for recognizing my work, I
will continue to actively participate in the work of the Apache
HugeGraph.

Next, I will follow the instructions to complete the next steps:
Signing and submitting iCLA and registering Apache ID.

xxx
```

Of course, the candidate may also choose to decline the invitation, in which case there is no template:)

Once the invitation is accepted, the candidate needs to complete the following tasks:

- Subscribe to dev@hugegraph.apache.org, for specific steps/filtering configurations, please refer to the [documentation](https://hugegraph.apache.org/docs/contribution-guidelines/subscribe/)
- Sign the [ICLA](https://www.apache.org/licenses/icla.pdf), follow the steps below↓

### ICLA Signing Process

1. Download the [ICLA](https://www.apache.org/licenses/icla.pdf)
2. Open the PDF and fill in the required information. All fields must be filled in English. It is recommended to use a PDF tool to edit and sign.
   1. **Full name**: First name followed by last name
   2. **Public name**: Optional, defaults to the same as `Full name`
   3. Check the box only if you entered names with your family name first
   4. **Postal Address**: English address, starting from small to large, including detailed street address
   5. **Country:** Country of residence in English
   6. **E-mail**: Email address, preferably the same as the one used in the invitation email
   7. **(optional) preferred Apache id(s)**: Choose an SVN ID that is not listed on the [Apache committer](http://people.apache.org/committer-index.html) page
   8. **(optional) notify project**: Apache HugeGraph
   9. **Signature: Must be handwritten using a PDF tool**
   10. **Date:** Format as xxxx-xx-xx
3. After signing, rename `icla.pdf` to `name-pinyin-icla.pdf`
4. Send the following email and attach `name-pinyin-icla.pdf` as a reference.

```text
To: secretary@apache.org
Subject: ICLA Information

Hello everyone:

I have accepted the Apache HugeGraph PMC invitation to
become a HugeGraph committer, the attachment is my ICLA information.

(Optional) My GitHub account is https://github.com/xxx. Thanks!

xxx
```

> For more details, please refer to https://github.com/apache/hugegraph/issues/1732.

PMC members will await confirmation of the ICLA record from the Apache secretary team. Candidates and PMC members will receive the following email:

```text
Dear xxx,

This message acknowledges receipt of your ICLA, which has been filed in the Apache Software Foundation records.

Your account (with id xxx) has been requested for you and you should receive email with next steps
within the next few days (this process can take up to a week).

Please refer to https://www.apache.org/foundation/how-it-works.html#developers
for more information about roles at Apache.
```

### Setting Up Apache Account and Development Environment (CONFIG)

After the record is completed, the candidate will receive an email from root@apache.org with the subject `Welcome to the Apache Software Foundation`. At this point, the candidate needs to follow the steps in the email to set up the Apache account and development environment:

1. Reset the password at https://id.apache.org/reset/enter.
2. Configure personal information at https://whimsy.apache.org/roster/committer/xxx.
3. Associate GitHub account at https://gitbox.apache.org/boxer.
   - This step requires configuring GitHub Two-Factor Authentication (2FA).
4. **The nominating PMC member must add the new Committer to the official list of committers via the [Roster](https://whimsy.apache.org/roster/pmc/hugegraph) page.** (**Important**, otherwise repository permissions will not take effect).
   - After this step, the candidate becomes a new Committer and gains write access to the GitHub HugeGraph repository.
5. (Optional) The new Committer can apply for free use of JetBrains' full range of products with their Apache account [here](https://www.jetbrains.com/shop/eform/apache).


## Announcing via Email (ANNOUNCE)

After the candidate completes the above steps, they will officially become a Committer of HugeGraph. At this point, they need to send an announcement email to dev@hugegraph.apache.org. Below is a template for the email:

```text
To: dev@hugegraph.apache.org
Subject: [ANNOUNCE] New Committer: xxx

Hi everyone, The PMC for Apache HugeGraph has invited xxx to
become a Committer and we are pleased to announce that he/she has accepted.

xxx is being active in the HugeGraph community & dedicated to ... modules, 
and we are glad to see his/her more interactions with the community in the future.

(Optional) His/Her GitHub account is https://github.com/xxx

Welcome xxx, and please enjoy your community journey~ 

Thanks! 

The Apache HugeGraph PMC
```

## Update Governance Information

Since Apache HugeGraph graduated in January 2026, governance information is maintained in ASF committee/project data rather than Incubator clutch pages.

Please check:

- [ASF Committee data for HugeGraph](https://projects.apache.org/committee.html?hugegraph)
- [PMC roster page](https://whimsy.apache.org/roster/pmc/hugegraph)

If an update is required but does not appear automatically, coordinate with Apache Community Development or ASF Infra according to the official process.

# References

1. https://community.apache.org/newcommitter.html (ASF official documentation)
2. https://infra.apache.org/new-committers-guide.html
3. https://www.apache.org/dev/pmc.html#newcommitter
4. https://linkis.apache.org/zh-CN/community/how-to-vote-a-committer-pmc
5. https://www.apache.org/licenses/contributor-agreements.html#submitting
6. https://www.apache.org/licenses/cla-faq.html#printer
7. https://linkis.apache.org/zh-CN/community/how-to-sign-apache-icla
8. https://github.com/apache/hugegraph/issues/1732 (HugeGraph ICLA related issue)
