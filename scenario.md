# Cocoarynth Trace scenario

## Scenario summary

Cocoarynth is a fictional bean-to-bar chocolate company specializing in single-origin chocolate. It works directly with cacao producers and keeps detailed records about each origin lot and production batch.

The company's engineering team maintains **Cocoarynth Trace**, an internal web application that follows cacao from its producer through fermentation, roasting, tempering, packaging, and wholesale delivery. The application can generate an **Origin Passport** containing traceability information for a finished chocolate batch.

Cocoarynth is preparing a pilot with the fictional retailer **Mapayça Markets**. The retailer wants to import Cocoarynth's traceability data into its inventory system. Cocoarynth Trace already exports Origin Passports as JSON, but Mapayça Markets accepts only CSV files. CSV export support has been proposed but is not yet implemented.

Attendees investigate whether Cocoarynth is ready for the pilot. The answer requires evidence from both GitHub and uploaded organizational documents:

- GitHub shows what the application currently implements and what engineering work remains.
- The uploaded documents explain the retailer's requirements and the company's data-sharing rules.

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

**Suggested repository name:** `cocoarynth-trace`

Cocoarynth Trace is a small web application used by sourcing, production, quality, and wholesale operations staff. Its primary purpose is to connect each finished chocolate batch to its origin and production history.

The application should be complete enough to feel credible but small enough for attendees to understand quickly. It does not need to model every part of chocolate manufacturing.

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

This gap is deliberately concrete. Attendees can see JSON behavior in the code, discover the planned CSV work in GitHub, and find the retailer's CSV requirement in an uploaded document.

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

The code should make the current behavior easy to verify. Suggested implementation surfaces include:

- An Origin Passport model or schema.
- A service that assembles passport data from a batch.
- A JSON serializer or export function.
- An HTTP endpoint that returns `application/json`.
- A download button labeled **Download JSON**.
- Tests confirming the JSON filename, content type, and fields.

The repository should not contain the pilot requirements or policy documents. Otherwise, attendees could answer document questions through local file access instead of the knowledge base.

### Merged pull request

**Suggested title:** `Add downloadable Origin Passports for production batches`

The pull request introduces the current JSON export. Its description explains that JSON was chosen because Cocoarynth's first integration was an internal API prototype. It adds the passport schema, download endpoint, user interface action, and tests.

Useful implementation evidence in the pull request:

- The endpoint returns JSON.
- The downloaded filename ends in `.json`.
- The export is an immutable snapshot of the batch at generation time.
- Confidential supplier fields are omitted.

The pull request predates the Mapayça Markets pilot and should not mention a CSV requirement.

### Open issue

**Suggested title:** `Support CSV downloads for Origin Passports`

The issue requests a second export format using the existing Origin Passport data. Suggested acceptance criteria:

- Add CSV as an export option without removing JSON.
- Use stable, documented column headers.
- Format dates as `YYYY-MM-DD`.
- Escape commas, quotes, and line breaks correctly.
- Return `text/csv` with a `.csv` filename.
- Add tests for serialization and download behavior.

The issue should be clearly open and unimplemented. It may mention interest from wholesale operations, but it should not duplicate the full pilot requirements document.

### GitHub discussion

**Suggested title:** `Which origin details should we share with wholesale partners?`

The discussion records a cross-functional decision about exportable fields. Participants agree to include traceability facts such as producer name, growing region, harvest year, certification status, and production dates. They agree to exclude negotiated prices, producer contact details, internal quality notes, and employee comments.

This gives attendees useful rationale that cannot be inferred confidently from code alone while keeping the file-format requirement in the document corpus.

### Optional additional issue

**Suggested title:** `Document the Origin Passport schema for integration partners`

This issue can provide realistic background without becoming another pilot blocker. It should be labeled as documentation work and explicitly state that it does not block the limited pilot if the required CSV headers are supplied in the pilot handoff.

## Uploaded document corpus

The corpus should contain three required documents and one optional document. Each should be short, text-rich, and written in a distinct organizational voice.

### 1. Mapayça Markets traceability pilot requirements

This is the only authoritative source for the retailer's integration requirements. It should include:

- Pilot purpose and scope
- Covered product and stores
- Required CSV file format
- Required column names and meanings
- ISO date requirement
- Prohibited confidential fields
- Pilot acceptance criteria
- A statement that JSON uploads are rejected by the retailer's system

This document establishes why the current JSON implementation is insufficient.

### 2. ADR: Immutable Origin Passport snapshots

This architecture decision explains that an exported passport represents the facts approved at the time of shipment. Previously generated passports do not change when internal records are later corrected. A new version must be generated instead.

The decision provides the answer to “Why was this feature built this way?” but does not prescribe JSON or CSV as the permanent format.

### 3. Wholesale traceability data-sharing policy

This policy classifies fields into three groups:

- Required traceability fields that may be shared
- Internal fields that must not be shared
- Personal or commercial information that requires separate approval

It should confirm that the fields planned for the CSV export are permitted while pricing, personal contact details, and internal notes are prohibited.

### 4. Origin Passport support runbook (optional)

This document describes how operations staff verify a passport, regenerate an incorrect export, and escalate import failures. It can mention checking file type and headers when a retailer reports a failed import.

The runbook adds retrieval variety but should not contain the full answer to pilot readiness.

## Workshop progression

The same scenario develops as attendees gain access to more context.

### Opening: Local repository only

Attendees begin with Cocoarynth Trace checked out locally. They can inspect the README and application code but cannot access the organizational document corpus.

Suggested prompt:

> Explain what this project does, identify its main components, and describe how it exports an Origin Passport.

Expected discovery:

- The application tracks chocolate batches and generates Origin Passports.
- The export endpoint and download action produce JSON.
- The exported data includes origin and production details.

Attendees cannot yet know whether JSON is acceptable to the pilot customer.

### Opening: GitHub MCP connected

Attendees add the hosted GitHub MCP server and investigate live issues, pull requests, and discussions.

Suggested prompt:

> Why was the Origin Passport export built this way, and what related work remains open?

Expected discovery:

- The original feature used JSON because it began as an internal API integration.
- An open issue proposes CSV downloads.
- A discussion explains why some fields are included and others are excluded.
- GitHub alone does not establish whether CSV is required for the pilot.

### Section 1: Documents-only knowledge base

Attendees upload the pilot requirements, architecture decision, and data-sharing policy. They inspect chunks and test document retrieval in the web interface.

Suggested retrieval questions:

- “What file format does Mapayça Markets require?”
- “Which fields must the pilot export include?”
- “Which information must Cocoarynth exclude from wholesale exports?”
- “Why are Origin Passports immutable snapshots?”

Expected discovery:

- Mapayça Markets requires CSV and rejects JSON uploads.
- The required schema and date format are stated explicitly.
- The policy permits the required traceability fields and prohibits confidential ones.
- The documents do not prove what the current code implements.

### Section 2: Separate GitHub and document integrations

Copilot has access to GitHub MCP and the documents-only knowledge base as separate integrations. Copilot must coordinate calls to both.

Primary prompt:

> Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker and cite both the pilot requirements and implementation evidence.

Expected answer:

- No, the pilot cannot be supported without additional work.
- Mapayça Markets requires CSV.
- The current application exports JSON.
- The open CSV-support issue tracks the missing implementation.
- The existing exported fields largely align with the pilot and data-sharing policy.

Attendees should inspect which tools Copilot calls and distinguish requirements evidence from implementation evidence.

### Section 3: Combined knowledge base

Attendees create a combined knowledge base containing the uploaded file source and GitHub MCP knowledge source. They disable the separate integrations, start a fresh session, and repeat the primary prompt.

Suggested comparison prompt:

> Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker and cite both the pilot requirements and implementation evidence.

Attendees compare:

- Which sources were selected
- Whether both the CSV requirement and JSON implementation were retrieved
- How supporting evidence is attributed
- Whether the answer expresses uncertainty appropriately
- How retrieval through one combined endpoint differs from client-side coordination of two integrations

The exercise must not claim that the combined knowledge base always produces a better answer or always invokes every source.

### Closing and optional extension

The closing returns to the new-teammate analogy: code shows what exists, but planning and policy documents explain what the organization needs and why.

An optional take-home task can ask attendees to draft a small implementation plan for the CSV issue using evidence from the combined knowledge base. The required workshop remains read-only and does not require attendees to modify the shared repository.

## Answer guide

### Primary conclusion

Cocoarynth Trace is not ready for the Mapayça Markets traceability import because it produces JSON Origin Passports and the retailer accepts only CSV.

### Supporting conclusions

- The application already assembles most or all required traceability fields.
- The current endpoint, filename, user interface, and tests demonstrate JSON-only behavior.
- The original JSON choice was reasonable for the internal integration for which it was built.
- The retailer's later pilot introduced a CSV requirement.
- An open GitHub issue tracks CSV support, so the missing work is known but incomplete.
- The proposed CSV fields are compatible with Cocoarynth's data-sharing policy.
- Confidential fields must remain excluded from the new format.
- Bulk export is not required for the initial pilot and is not a blocker.

### Evidence required for a complete answer

A complete answer should cite at least:

1. The Mapayça Markets pilot requirements for the CSV requirement.
2. Repository code or the merged Origin Passport pull request for current JSON behavior.
3. The open CSV-support issue for the remaining engineering work.

The data-sharing policy or GitHub discussion strengthens the answer by confirming that the proposed field set is appropriate.

### Common incomplete answers

- “The pilot is ready because the required fields exist.” This misses the incompatible file format.
- “The pilot is blocked because a CSV issue is open.” This does not establish that the customer actually requires CSV.
- “Rename the JSON file to `.csv`.” This does not produce valid CSV content.
- “Bulk export must be implemented first.” The initial pilot explicitly permits one row per file.
- “JSON should be accepted because it is machine-readable.” The retailer's documented importer accepts only CSV.

## Corpus authoring guardrails

- Keep the scenario entirely fictional and use no sensitive or real customer information.
- Use the same product, batch, field, and stakeholder names across code, GitHub artifacts, and documents.
- Put implementation facts in GitHub and business requirements in uploaded documents.
- Avoid copying the full CSV requirement into an issue or pull request.
- Avoid placing the uploaded documents in the attendee's local repository.
- Include enough overlap in terminology for retrieval to connect “Origin Passport,” “Mapayça Markets,” “CSV,” and “traceability import.”
- Include at least one explicit negative statement, such as “The importer does not accept JSON,” to make the expected conclusion reliable.
- Keep documents short enough to ingest predictably during the lab but detailed enough to produce multiple meaningful chunks.
- Use stable fictional document URLs or maintain an explicit mapping from uploaded filenames to source links for citations.
- Ensure every expected conclusion in the answer guide maps to a specific artifact.

## Suggested names

| Item | Suggested name |
| --- | --- |
| Company | Cocoarynth |
| Application | Cocoarynth Trace |
| Repository | `cocoarynth-trace` |
| Export | Origin Passport |
| Pilot retailer | Mapayça Markets |
| Pilot product | Ecuador Esmeraldas 72% |
| Merged pull request | `Add downloadable Origin Passports for production batches` |
| Blocking issue | `Support CSV downloads for Origin Passports` |
| Discussion | `Which origin details should we share with wholesale partners?` |
| Requirements document | `Mapayça Markets Traceability Pilot Requirements` |
| Architecture document | `ADR: Immutable Origin Passport Snapshots` |
| Policy document | `Wholesale Traceability Data-Sharing Policy` |
| Optional runbook | `Origin Passport Support Runbook` |
