# Cocoarynth Trace scenario

This instructor-facing guide records the workshop narrative, evidence boundaries, and corpus design. The live [`pamelafox/cocoarynth-trace`](https://github.com/pamelafox/cocoarynth-trace) repository is the source of truth for application code and GitHub artifacts; the files under [documents](documents) are the source of truth for indexed organizational content.

## Contents

- [Scenario summary](#scenario-summary)
- [Fictional company](#fictional-company)
- [Application and repository](#application-and-repository)
- [Pilot customer](#pilot-customer)
- [Evidence design](#evidence-design)
- [Seeded GitHub artifacts](#seeded-github-artifacts)
- [Indexed document corpora](#indexed-document-corpora)
- [Foundry IQ topology](#foundry-iq-topology)
- [Current names](#current-names)

## Scenario summary

Cocoarynth is a fictional bean-to-bar chocolate company specializing in single-origin chocolate. It works directly with cacao producers and keeps detailed records about each origin lot and production batch.

The company's engineering team maintains **Cocoarynth Trace**, an internal web application that follows cacao from its producer through fermentation, roasting, tempering, packaging, and wholesale delivery. The application can generate an **Origin Passport** containing traceability information for a finished chocolate batch.

Cocoarynth is preparing a pilot with the fictional retailer **Mapayça Markets**. The retailer wants to import Cocoarynth's traceability data into its inventory system. Cocoarynth Trace already exports Origin Passports as JSON, but Mapayça Markets accepts only CSV files. CSV export support has been proposed but is not yet implemented.

Attendees investigate whether Cocoarynth is ready for the pilot. The answer requires evidence from both GitHub and indexed organizational documents:

- GitHub shows what the application currently implements and what engineering work remains.
- The indexed documents explain the retailer's requirements, architecture and policy constraints, support process, and company engineering practices.

The intended conclusion is:

> Cocoarynth is not yet ready to support the Mapayça Markets traceability import. The Origin Passport contains most of the required data, but Cocoarynth Trace exports only JSON and the retailer requires CSV. CSV export support remains open engineering work.

## Fictional company

**Name:** Cocoarynth

**Business:** Cocoarynth manufactures small-batch, single-origin chocolate. Each product highlights cacao from one producer, cooperative, or growing region. The company emphasizes transparent sourcing, careful production records, and direct relationships with cacao producers.

**Brand concept:** The name combines cocoa with a labyrinth. The visual identity uses a cacao pod formed from maze-like paths. This reflects both the complex journey from cacao farm to chocolate bar and the company's goal of making that journey traceable.

**Example products:**

- Ecuador Esmeraldas 72%
- Ghana Suhum 68%
- Peru Piura Blanco 70%
- Madagascar Sambirano 74%

## Application and repository

**Application name:** Cocoarynth Trace

**Repository:** [`pamelafox/cocoarynth-trace`](https://github.com/pamelafox/cocoarynth-trace)

Cocoarynth Trace is a small web application used by sourcing, production, quality, and wholesale operations staff. Its primary purpose is to connect each finished chocolate batch to its origin and production history.

The application is complete enough to feel credible but small enough for attendees to understand quickly. It does not model every part of chocolate manufacturing.

### Core application capabilities

- List production batches.
- View the cacao origin, producer, harvest, and certifications for a batch.
- View a timeline of production stages such as roasting, grinding, conching, tempering, and packaging.
- Associate finished batches with wholesale shipments.
- Generate and download an Origin Passport for one batch.
- Display the fields included in the generated passport.

### Origin Passport

An Origin Passport is a machine-readable snapshot of a chocolate batch's traceability data. It allows a wholesale customer to connect a delivered product to its cacao origin and production history.

The existing JSON export includes:

- Origin Passport ID
- Product name
- Batch number
- Country and growing region
- Producer or cooperative name
- Harvest year
- Cacao percentage
- Certification status
- Production date
- Shipment date

The export intentionally excludes confidential information such as negotiated cacao prices, producer contact details, internal quality notes, and employee comments.

### Current implementation gap

Cocoarynth Trace generates Origin Passports only as JSON files. The export code serializes a passport object and returns it with an `application/json` content type and a `.json` filename.

Mapayça Markets' inventory import accepts only CSV files. It requires one header row and one data row per exported batch. Renaming a JSON file to use a `.csv` extension would not satisfy the requirement; the application must serialize the data as valid CSV and return the appropriate content type and filename.

The missing capability is therefore:

> Add CSV as a supported Origin Passport export format.

This gap is deliberately concrete. Attendees can see JSON behavior in the code, discover the planned CSV work in GitHub, and find the retailer's CSV requirement in an indexed document.

## Pilot customer

**Name:** Mapayça Markets

Mapayça Markets is a fictional specialty grocery retailer launching a trial program for products with verifiable sourcing information. The retailer plans to carry Cocoarynth's Ecuador Esmeraldas 72% bar in a limited group of stores.

The retailer's inventory system imports traceability records from CSV files. For the pilot, each Cocoarynth shipment must be accompanied by an Origin Passport export that can be imported without manual conversion.

### Pilot requirements

- The export must use CSV format.
- The first row must contain stable column headers.
- Each row must identify the product and production batch.
- The export must include origin, producer, harvest year, cacao percentage, certification status, production date, and shipment date.
- Dates must use ISO `YYYY-MM-DD` format.
- The export must not include supplier pricing or personal contact information.
- The initial pilot may use one row per file; bulk export is not required.

Keeping bulk export outside the required pilot prevents two different missing features from competing with the central JSON-versus-CSV gap.

## Evidence design

The scenario is designed so that no single source provides the complete answer.

| Source | What it establishes | What it does not establish |
| --- | --- | --- |
| Local repository | The application generates JSON Origin Passports and which fields it includes | Whether Mapayça Markets requires CSV |
| Merged pull request | Why JSON was selected for the original export and how the feature was implemented | The final requirements of the later retailer pilot |
| Open issue | CSV support is planned but unfinished | Which customer requires it or whether it blocks the pilot |
| GitHub discussion | Which fields are safe and useful to share with retailers | The retailer's required file format |
| Pilot requirements document | Mapayça Markets requires CSV and specifies its schema | Whether the application currently supports CSV |
| Data-sharing policy | Which supplier and production fields may be exported | Whether the implementation follows the policy |
| Architecture decision | Why Origin Passports are immutable snapshots | Whether the pilot can launch now |

## Seeded GitHub artifacts

### Repository code

The code makes the current behavior easy to verify through:

- An Origin Passport model or schema.
- A service that assembles passport data from a batch.
- A JSON serializer or export function.
- An HTTP endpoint that returns `application/json`.
- A download button labeled **Download JSON**.
- Tests confirming the JSON filename, content type, and fields.

The repository does not contain the pilot requirements or policy documents. This prevents attendees from answering document questions through local file access instead of the knowledge base.

### Merged pull request

**PR #1:** [`Add downloadable Origin Passports for production batches`](https://github.com/pamelafox/cocoarynth-trace/pull/1)

The pull request introduces the current JSON export. Its description explains that JSON was chosen because Cocoarynth's first integration was an internal API prototype. It adds the passport schema, download endpoint, user interface action, and tests.

Useful implementation evidence in the pull request:

- The endpoint returns JSON.
- The downloaded filename ends in `.json`.
- The export uses an allowlisted Origin Passport object rather than serializing internal records.
- Confidential supplier fields are omitted.

The pull request predates the Mapayça Markets pilot and does not mention a CSV requirement.

The indexed architecture decision, rather than the transport implementation alone, is authoritative for retained snapshot identity, versioning, and historical stability.

### Open issue

**Issue #3:** [`Support CSV downloads for Origin Passports`](https://github.com/pamelafox/cocoarynth-trace/issues/3)

The issue requests a second export format using the existing Origin Passport data. Its acceptance criteria include:

- Add CSV as an export option without removing JSON.
- Use stable, documented column headers.
- Format dates as `YYYY-MM-DD`.
- Escape commas, quotes, and line breaks correctly.
- Return `text/csv` with a `.csv` filename.
- Add tests for serialization and download behavior.

The issue is open and unimplemented. It mentions interest from wholesale operations but does not duplicate the full pilot requirements document.

### GitHub discussion

**Discussion #2:** [`Which origin details should we share with wholesale partners?`](https://github.com/pamelafox/cocoarynth-trace/discussions/2)

The discussion records a cross-functional decision about exportable fields. Participants agree to include traceability facts such as producer name, growing region, harvest year, certification status, and production dates. They agree to exclude negotiated prices, producer contact details, internal quality notes, and employee comments.

This gives attendees useful rationale that cannot be inferred confidently from code alone while keeping the file-format requirement in the document corpus.

### Additional issue

**Issue #4:** [`Document the Origin Passport schema for integration partners`](https://github.com/pamelafox/cocoarynth-trace/issues/4)

This documentation issue provides realistic background without becoming another pilot blocker. It states that a temporary field list can support early integrations while the reference is prepared.

## Indexed document corpora

Deployment pre-ingests two four-document corpora from separate Blob containers. The HTML files under [documents/source](documents/source) are the editable sources for the project-requirement PDFs.

### Project requirements

#### 1. Mapayça Markets traceability pilot requirements

This is the only authoritative source for the retailer's integration requirements. It includes:

- Pilot purpose and scope
- Covered product and stores
- Required CSV file format
- Required column names and meanings
- ISO date requirement
- Prohibited confidential fields
- Pilot acceptance criteria
- A statement that JSON uploads are rejected by the retailer's system

This document establishes why the current JSON implementation is insufficient.

#### 2. ADR: Immutable Origin Passport snapshots

This architecture decision explains that an issued passport retains the approved values captured at generation. Later internal corrections do not rewrite it; an authorized user generates a new version that references the retained, superseded passport.

The decision provides the answer to “Why was this feature built this way?” but does not prescribe JSON or CSV as the permanent format.

#### 3. Wholesale traceability data-sharing policy

This policy classifies fields into three groups:

- Required traceability fields that may be shared
- Internal fields that must not be shared
- Personal or commercial information that requires separate approval

It confirms that the fields planned for the CSV export are permitted while pricing, personal contact details, and internal notes are prohibited.

#### 4. Origin Passport support runbook

This document describes how operations staff verify a passport, regenerate an incorrect export, and escalate import failures. It covers checking file type and headers when a retailer reports a failed import.

The runbook adds retrieval variety but does not contain the full answer to pilot readiness.

### Engineering practices

The second corpus contains four current company guides:

1. **API Design and Export Contracts Guide** establishes API compatibility, CSV serialization, validation, error, testing, and observability practices.
2. **Engineering Culture Presentation** establishes review, testing, rollout, monitoring, and evidence standards.
3. **Product UI and Accessibility Guide** establishes interaction, keyboard, status, error, and accessibility requirements.
4. **React and TypeScript Engineering Guide** establishes frontend implementation and testing practices.

These guides provide implementation standards, not product requirements or claims about the current application.

## Foundry IQ topology

Deployment creates three knowledge bases over two Search Index knowledge sources:

| Knowledge base | Reasoning | Sources |
| --- | --- | --- |
| `cocoarynth-kb-docs` | Minimal | `cocoarynth-documents-index` |
| `cocoarynth-kb-engineering-practices` | Minimal | `cocoarynth-engineering-practices-index` |
| `cocoarynth-kb-all` | Low | Both indexes |

The first two support corpus-specific MCP calls. The combined knowledge base lets Foundry IQ plan retrieval across both indexes, but it is not guaranteed to query both for every question.

## Current names

| Item | Name |
| --- | --- |
| Company | Cocoarynth |
| Application | Cocoarynth Trace |
| Repository | `pamelafox/cocoarynth-trace` |
| Export | Origin Passport |
| Pilot retailer | Mapayça Markets |
| Pilot product | Ecuador Esmeraldas 72% |
| Merged pull request | `Add downloadable Origin Passports for production batches` |
| Blocking issue | `Support CSV downloads for Origin Passports` |
| Discussion | `Which origin details should we share with wholesale partners?` |
| Requirements document | `Mapayça Markets Traceability Pilot Requirements` |
| Architecture document | `ADR: Immutable Origin Passport Snapshots` |
| Policy document | `Wholesale Traceability Data-Sharing Policy` |
| Runbook | `Origin Passport Support Runbook` |
