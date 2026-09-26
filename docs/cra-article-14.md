# EU Cyber Resilience Act — Article 14 reporting (Bernard's research note)

Converted from Bernard's PDF, 25 Sep 2026. Bernard: please tidy into Markdown tables.

```
                                      EU Cyber Resilience Act
                                      Article 14 reporting requirements


Note: The objective of this document is to lay out exactly what Article 14 of the EU Cyber Resilience Act
requires, so that as you build, you have a clear picture of what the product ultimately needs to help a company
answer. Where I think something is worth flagging from a compliance angle, I have noted it.

*What Article 14 actually requires*

Article 14 came into force on 11 September 2026. It applies to any manufacturer selling software products in
the EU. When a manufacturer becomes aware of an actively exploited vulnerability in their product, or a severe
security incident affecting it, three reporting obligations are triggered in sequence.

             Step                    Deadline                          What must be submitted

                                Within 24 hours of             Confirm the vulnerability exists and the
        Early warning            becoming aware             product is affected. Indicate which EU member
                                                                   states the product is available in.

                                Within 72 hours of         General information about the product. General
              Full               becoming aware            nature of the exploit and the vulnerability. Any
          notification                                        corrective or mitigating measures already
                                                                 taken. Any measures users can take
                                                                             themselves.

                              Within 14 days of a fix        A description of the vulnerability, its severity
         Final report            being available             and impact. Information about any malicious
                                                            actor if available. Details of the security update
                                                                     or corrective measures applied.



The clock starts the moment the manufacturer becomes aware. The law uses the phrase 'without undue delay
and in any event within' for each deadline, meaning there is no grace period built in.

Separately, Article 14(3) also requires reporting severe security incidents. Article 14(5) defines severe as
incidents that negatively affect the availability, authenticity, integrity or confidentiality of data or
functions, or that lead to the introduction or execution of malicious code in the product or in a user's
systems. A supply chain attack via a compromised library would likely qualify under this definition.

Manufacturers must also notify impacted users under Article 14(8), in a structured, machine-readable format
where appropriate.


*The questions a regulator will ask*

When a manufacturer files the 24-hour early warning, the regulator's follow-up questions will be driven by
what the 72-hour notification needs to contain. From a compliance perspective, these are the questions the
product will need to help answer quickly.
                                 Question                                           Required by

                   Which of your products are affected?                    Art. 14(2)(a) — early warning

          When did you first become aware of the vulnerability?            Art. 14(2)(a) — starts the clock

          What is the nature of the exploit and the vulnerability?            Art. 14(2)(b) — 72-hour
                                                                                     notification

                 Which parts of the product were affected?                    Art. 14(2)(b) — 72-hour
                                                                                     notification

         What corrective or mitigating measures have you taken?                 Art. 14(2)(b) and (c)

                 What can users do to protect themselves?                   Art. 14(2)(b) and Art. 14(8)

          How severe is the vulnerability and what is its impact?            Art. 14(2)(c) — final report

         Is there any information about who carried out the attack?          Art. 14(2)(c) — final report

*A few observations from a compliance angle*

    1. The 24-hour clock and what 'becoming aware' means
       The law says the clock starts when the manufacturer becomes aware of the vulnerability. In
       practice, a company might learn of a security advisory affecting a library they used at 9am. They then
       need to spend time figuring out whether their product is actually affected before they can file the early
       warning. The faster that question can be answered, the more of the 24 hours remains for filing the actual
       report rather than doing the investigation.

    2. What the 72-hour notification requires
       The 72-hour notification must describe the general nature of the exploit and the vulnerability. In a
       supply chain scenario where a library was compromised, understanding what the agent did after reading
       that library seems directly relevant to characterising the nature and scope of the vulnerability.

    3. Machine-readable user notification
       Article 14(8) says impacted users must be notified in a structured, machine-readable format where
       appropriate. The law does not prescribe a specific format. This may be worth keeping in mind when
       thinking about what Origit's output looks like, but I would not read too much into it at this stage.

    4. Severe incident vs. actively exploited vulnerability
       Article 14 covers two separate triggers: actively exploited vulnerabilities (paragraphs 1 and 2) and
       severe security incidents (paragraphs 3 and 4). A supply chain attack via a malicious library could
       potentially qualify under both.

        Article 14(5)(b) defines a severe incident as one that leads or is capable of leading to the introduction
        or execution of malicious code. Whether a specific scenario qualifies is ultimately a legal judgement
        call, but this definition seems broad enough to cover the supply chain attack scenario. The reporting
        timelines are the same either way.

Note: the question at the centre of Article 14 compliance in an agentic development context is 'which code did
an agent produce after reading a compromised input.' That is the question the regulator will ask, and it is the
question Origit is seemingly designed to answer. (Legal Hook + Regulatory Pressure)
```
