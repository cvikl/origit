# Article 14 CRA — Notification Templates

Templates for the **early-warning** (Art. 14(2)(a), within 24 hours) and the **72-hour full notification**
(Art. 14(2)(b)–(c)), pre-populated from an `origit taint` result.

Placeholders enclosed in `{{ }}` are filled automatically from the taint JSON.  
Placeholders enclosed in `[[ ]]` require manual input that is outside the provenance record.

---

## How to obtain the taint result

```bash
origit taint <needle> --json > taint.json
```

where `<needle>` is the package spec (`fast-pay-utils@2.1.0`), a file path, or a SHA-256 hash.

---

## Early Warning (Art. 14(2)(a)) — within 24 hours of awareness

> *Confirm the vulnerability exists and the product is affected. Indicate which EU member states the
> product is available in.*

---

**SUBJECT:** Early Warning — actively exploited vulnerability / security incident affecting `[[ PRODUCT NAME ]]`

**Filed by:** [[ MANUFACTURER LEGAL NAME ]]  
**Filing date:** [[ DATE OF FILING ]]  
**Reference:** `{{ needle }}` (taint query needle)

---

### 1. Confirmation that the product is affected

An `origit taint` query for `{{ needle }}` returns **{{ affected | length }} affected commit(s)** across
**{{ sessions | length }} session(s)**.  Affected commit SHAs:

{% for commit in affected %}
- `{{ commit.sha }}` — {{ commit.subject }}
{% endfor %}

The presence of a `added_deps` or `read:pkg` match for `{{ needle }}` in the provenance record confirms
that the product incorporated the affected component.

### 2. Awareness timestamp (start of Art. 14 clock)

| Field | Value |
|---|---|
| First-read session | `{{ first_read.session }}` |
| First-read commit | `{{ first_read.commit }}` |
| First-read timestamp (UTC) | `{{ first_read.at }}` |

**24-hour filing deadline:** `{{ first_read.at | add_hours(24) }}`  
**72-hour filing deadline:** `{{ first_read.at | add_hours(72) }}`

### 3. EU member states where the product is available

[[ List every EU member state in which the product is placed on the market or made available.
   This information is not held in the provenance record and must be supplied separately. ]]

---

## 72-Hour Full Notification (Art. 14(2)(b)–(c)) — within 72 hours of awareness

> *General information about the product. General nature of the exploit and the vulnerability.
> Any corrective or mitigating measures already taken. Any measures users can take themselves.*

---

**SUBJECT:** 72-Hour Notification — `{{ needle }}` — `[[ PRODUCT NAME ]]`

**Filed by:** [[ MANUFACTURER LEGAL NAME ]]  
**Filing date:** [[ DATE OF FILING ]]  
**Awareness timestamp (clock start):** `{{ first_read.at }}`  
**Reference:** `{{ needle }}`

---

### 1. General information about the product

| Field | Value |
|---|---|
| Product name | [[ PRODUCT NAME ]] |
| Product version(s) affected | [[ VERSION(S) ]] |
| Product category | [[ E.G. PAYMENT PROCESSING API / WEB APPLICATION / … ]] |
| Repository | [[ REPOSITORY URL ]] |

*Note: actor kind recorded in provenance: `{{ affected[0].actor }}`.*

### 2. Which parts of the product were affected

The following **{{ files_written | length }} file(s)** were written by tainted sessions and are
considered affected. This list is derived directly from `wrote[]` fields of all affected records.

| File | Tainted commit(s) |
|---|---|
{% for file in files_written %}
| `{{ file }}` | {% for c in affected if file in c.wrote %}`{{ c.sha[:7] }}`{% if not loop.last %}, {% endif %}{% endfor %} |
{% endfor %}

Taint propagation path for each commit (the `matched` field from the taint result):

{% for commit in affected %}
**`{{ commit.sha[:7] }}`** — {{ commit.subject }}

{% for m in commit.matched %}
- `{{ m }}`
{% endfor %}
{% endfor %}

### 3. General nature of the exploit and the vulnerability

**Nature:** Supply-chain compromise via dependency `{{ needle }}`.

The provenance record shows that a Bob IDE session (`{{ first_read.session }}`) read `{{ needle }}`
at `{{ first_read.at }}` and subsequently wrote the files listed in §2 within the same session.
The agent read the compromised component before producing those files; the causal link is encoded in
the taint propagation chain above.

**CVE / advisory reference:** [[ INSERT CVE ID OR ADVISORY URL IF AVAILABLE ]]  
**Description of malicious behaviour:** [[ DESCRIBE WHAT THE COMPROMISED COMPONENT DOES — e.g. exfiltrates
   environment variables, injects backdoor endpoint. This requires external threat-intelligence input. ]]

### 4. Corrective and mitigating measures already taken

| Measure | Detail |
|---|---|
| Safe rollback target identified | `{{ rollback_commit }}` |
| Rollback removes all tainted commits | Yes — {{ affected | length }} commit(s) listed in §2 |
| Tainted dependency removed from lockfile | [[ YES / NO / IN PROGRESS ]] |
| Replacement dependency or version | [[ NAME@VERSION OR N/A ]] |
| Redeployment of clean build completed | [[ YES / NO / IN PROGRESS — DATE ]] |
| Internal incident ticket | [[ TICKET ID ]] |

Approver(s) who signed off tainted commits:
{% for a in approvers %}
- `{{ a }}`
{% endfor %}
{% if not approvers %}
- *(no approver recorded in taint result)*
{% endif %}

### 5. Measures users can take

[[ Describe any action end-users or downstream integrators should take. Examples: rotate credentials
   that may have been exposed, redeploy from a clean build, pin to a known-good dependency version.
   This information is not held in the provenance record and must be supplied by the security team. ]]

---

## Origit taint fields → template placeholder mapping

| Template placeholder | Taint result field | Notes |
|---|---|---|
| `{{ needle }}` | `needle` | The query string used |
| `{{ affected }}` | `affected[]` | List of affected commit objects |
| `{{ affected[].sha }}` | `affected[].sha` | Full 40-hex commit SHA |
| `{{ affected[].subject }}` | `affected[].subject` | Git commit subject line |
| `{{ affected[].actor }}` | `affected[].actor` | `bob-ide` \| `human` |
| `{{ affected[].wrote }}` | `affected[].wrote` | Sorted list of files written |
| `{{ affected[].matched }}` | `affected[].matched` | Match/propagation labels |
| `{{ affected[].approver }}` | `affected[].approver` | Approver identity or null |
| `{{ sessions }}` | `sessions[]` | Sorted unique session ids |
| `{{ files_written }}` | `files_written[]` | Sorted union of all `wrote` |
| `{{ approvers }}` | `approvers[]` | Sorted unique non-null approvers |
| `{{ first_read.session }}` | `first_read.session` | Session id of oldest affected commit |
| `{{ first_read.at }}` | `first_read.at` | ISO-8601 UTC — **starts the Art. 14 clock** |
| `{{ first_read.commit }}` | `first_read.commit` | SHA of oldest affected commit |
| `{{ rollback_commit }}` | `rollback_commit` | SHA of nearest clean ancestor |
| `[[ … ]]` | — | Manual input required; not in provenance |
