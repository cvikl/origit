You are drafting the **EU Cyber Resilience Act Article 14 early warning** (Art. 14(4)(a), within 24 hours of awareness) for the manufacturer of the software product "{{product}}", from the Origit taint result below. The trigger is a severe incident under Art. 14(5)(b): a compromised third-party component ("{{needle}}") introduced into the product by an AI coding agent. Use only facts present in the inputs; where the early warning requires something the inputs do not contain (member states, contact person, product version), leave a clearly marked `[TODO: …]` placeholder. Do not invent dates, identifiers or impact.

Awareness time (now): {{now}}

## Origit taint result (sealed records; which commits/sessions/files are downstream of the compromised input)
```json
{{taint}}
```

## Advisory for the component (if available)
{{advisory}}

## Output
Reply with **only** a JSON object:
```json
{
  "title": "Early warning notification — Art. 14(4)(a) CRA",
  "to": ["ENISA single reporting platform", "[TODO: national CSIRT of the member state of establishment]"],
  "manufacturer": "[TODO: legal entity]",
  "product": "{{product}} [TODO: version(s) affected]",
  "awareness_at": "{{now}}",
  "deadline_early_warning": "<awareness + 24h, ISO-8601>",
  "deadline_notification": "<awareness + 72h, ISO-8601>",
  "incident_type": "severe security incident — introduction of malicious code (Art. 14(5)(b))",
  "malicious_acts_suspected": true,
  "affected_components": ["<files from taint.files_written>"],
  "affected_commits": ["<sha: subject>"],
  "agent_sessions": ["<session ids>"],
  "first_exposure": "<taint.first_read.at, session>",
  "approved_by": "<taint.approvers>",
  "member_states": "[TODO: where the product is made available]",
  "corrective_measures_taken": ["roll back to <taint.rollback_commit>", "remove dependency {{needle}}", "rotate secrets exposed to the build environment"],
  "user_measures": ["<one or two concrete measures users can take>"],
  "narrative": "<6–10 sentences, plain language, suitable to paste into the ENISA form: what happened, how it was detected (Origit records + taint query), what is affected, what has been done, what follows in the 72-hour notification>"
}
```
