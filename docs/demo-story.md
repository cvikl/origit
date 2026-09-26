# Demo story (Bernard, revised 26 Sep 2026)

Converted from 'Revised Demo Story.pdf'. Source of truth for the video narrative.

Context (The Demo company)

A fintech company sells payment infrastructure software to clients across the EU. Under the EU Cyber
Resilience Act, selling software in the EU makes them a manufacturer. Article 14 of that Act came into
force on 11 September 2026. It requires manufacturers to report severe security incidents affecting their
products to ENISA, the EU's cybersecurity agency, within strict deadlines.

They use IBM Bob to build features. Bob is an AI coding agent. He reads documentation, makes
decisions, writes code, and saves progress to the codebase in commits. A commit is a saved checkpoint
(the system keeps a permanent record of what changed and when).

The company also uses Origit. Every time Bob makes a commit, Origit captures an additional record
alongside the standard git entry: which session Bob was running, when the commit happened, what files
Bob read before making changes, what files he wrote, which libraries he added, and who reviewed and
approved the session. That record is sealed with a SHA-256 hash at the time of the commit. The hash
means that if anyone alters the record later, the alteration is immediately detectable (the hash will no
longer match the data.)


Day 1 (The build)

Bob is tasked with building a payment export feature. He works across three sessions.

In session 42, Bob reads the documentation for a library called fast-pay-utils and decides it does what
is needed. He adds fast-pay-utils version 2.1.0 to the project as a dependency. Sessions 43 and 44
continue building on top of it. All tests pass. The team reviews and approves the sessions. The feature
ships.

        Origit has recorded the following: sessions 42, 43, and 44 each have a commit record.
        The first read of fast-pay-utils is timestamped 2026-09-24 09:14 UTC in session 42. The
        files written across those sessions are src/payout-export.ts and src/payment-utils.ts. The
        approver is Human/Bernard.

Nothing looks wrong at this point. The library behaves as documented. The tests pass. This is how
supply chain attacks work. The attacker gained access to the fast-pay-utils publishing account and
pushed a version containing hidden code. That code only activates under specific conditions that do not
appear in a standard test environment. The library was designed to pass tests. That is the attack.

Day 3 (The incident)

A security advisory is published. It states that fast-pay-utils version 2.1.0 has been compromised and
contains code designed to exfiltrate payment data.

The moment the team reads this advisory, the Article 14 clock starts. The law uses the phrase "without
undue delay and in any event within" for each deadline, measured from the moment the manufacturer
becomes aware. There is no grace period.

        Why Article 14 applies: Article 14(3) requires manufacturers to notify ENISA of any
        severe security incident having an impact on the security of the product. Article 14(5)(b)
        defines a severe incident as one that has led or is capable of leading to the introduction or
        execution of malicious code in a product. A compromised library introduced into a
        payment product by an AI agent meets that definition. The reporting obligation is
        triggered.
Three deadlines now run from the same moment:

    §   Within 24 hours: An early warning to ENISA and the designated national CSIRT. At this stage
        the team must confirm the product is affected and that the incident appears to involve malicious
        acts. This is set out in Article 14(4)(a).

    §   Within 72 hours: A full incident notification. This must cover the general nature of the incident,
        an initial assessment of severity and impact, and any corrective or mitigating measures already
        taken or available to users. This is Article 14(4)(b).

    §   Within one month of a fix being available: A final report. This must include a detailed
        description of the vulnerability, its severity and impact, the likely root cause, and details of the
        corrective measures applied. This is Article 14(4)(c).

Without Origit, the team spends most of the 24-hour window on investigation. In a codebase where
Bob has run many sessions across hundreds of commits, tracing which code was written after the library
was read requires searching the full commit history manually. In a real production environment with
multiple active agents, this takes hours to days. The legal window closes before most teams have an
answer.

The response

With Origit, the team runs one command:

                                        origit taint fast-pay-utils

The command searches every Origit record for sessions where fast-pay-utils appears in the
dependencies added or files read. It returns in seconds:

                                3 commits affected
                                Sessions: #42, #43, #44
                                Files: src/payout-export.ts, src/payment-utils.ts
                                Approver: bernard (2026-09-26 14:02 UTC)
                                First read: session #42, 2026-09-24 09:14 UTC
                                Roll back to: commit e19b...770

The team now has everything the three Article 14 deadlines require.

    §   For the 24-hour early warning: they can confirm the product is affected, confirm the incident
        involves malicious code, and file before the window closes.

    §   For the 72-hour notification: the affected files are known, the corrective measure is identified
        (roll back to commit e19b...770 and remove the dependency), and the nature of the incident is
        documented (a compromised third-party library introduced by an AI agent during session 42.)

    §   For the final report: the full session records from sessions 42, 43, and 44 provide the complete
        picture. The hashed Origit records prove the data was captured at commit time and not
        reconstructed after the fact.

Bob then reads the Origit record and drafts the Article 14 incident notification from it. The record
contains every field the notification requires.
The before and after

    1. Manual investigation in a multi-agent codebase after a malicious library is flagged: hours
       to days, frequently past the 24-hour legal deadline.

    2. Origit taint command: seconds. That is the measurable improvement. The difference is not
       convenience. It is whether the team meets a live legal obligation or misses it.


Key Insight:
Git tells you what changed. Origit tells you what the agent read before it changed it. When a library
turns out to be malicious, that difference is the 24 hours you have left to meet your legal obligation
instead of the 24 hours you spent trying to find the answer.
