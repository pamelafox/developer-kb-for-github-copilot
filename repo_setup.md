# Cocoarynth Trace repository setup

## Purpose

This document is the build specification for the fictional **Cocoarynth Trace** repository.

The repository must provide a realistic but approachable application, meaningful commit and pull request history, open engineering work, and a GitHub discussion. Together, those artifacts establish what the software currently does and why it was built that way.

The central implementation fact is:

> Cocoarynth Trace generates Origin Passport downloads as JSON. CSV export is proposed but not implemented.

## Repository identity

| Item | Value |
| --- | --- |
| Owner | Your primary GitHub account; a dedicated organization can be added later |
| Repository | `cocoarynth-trace` |
| Application | Cocoarynth Trace |
| Company | Cocoarynth |
| Visibility | Public or accessible to every event-provided GitHub account |
| Default branch | `main` |
| License | MIT |
| Primary language | TypeScript |

### Prototype account model

Use your primary GitHub account for all commits, issues, pull requests, comments, merges, and discussions. Artifact type, content, chronology, and state provide the useful project history; multiple actors are not required.

GitHub does not allow a pull request author to approve their own pull request, so approval is optional for the prototype. Your second account may add a review later if useful, but it is not needed for the knowledge retrieval flow.

When one discussion needs perspectives from several departments, post separate comments from your primary account and begin each comment with a bold role label such as **Sourcing**, **Quality**, **Production**, or **Engineering**.

Suggested repository description:

> Trace single-origin chocolate from cacao harvest to finished batch and generate shareable Origin Passports.

Suggested repository topics:

- `chocolate`
- `traceability`
- `supply-chain`
- `typescript`
- `react`

## Product description

Cocoarynth manufactures small-batch, single-origin chocolate. Cocoarynth Trace is an internal operations application that connects each finished chocolate batch to its cacao origin and production history.

The application is used by sourcing, production, quality, and wholesale operations staff. It allows a user to:

- Browse chocolate production batches.
- Search or filter batches by origin and status.
- View a batch's product, producer, origin, harvest, and certification information.
- View production events from roasting through packaging.
- View the wholesale shipment associated with a batch.
- Preview an immutable Origin Passport.
- Download the Origin Passport as JSON.

The app should feel like a compact operational tool, not a marketing site or online store.

## Recommended technical shape

Use a small TypeScript application with minimal infrastructure and a familiar structure. A recommended implementation is:

- React with Vite for the frontend.
- Express for the API.
- Shared TypeScript types for domain models.
- Vitest for unit and API tests.
- React Testing Library for focused component tests.
- ESLint and Prettier for static checks and formatting.
- In-memory fixture data loaded from TypeScript or JSON files.

Keep the implementation local and self-contained, using in-memory data without authentication, cloud infrastructure, queues, or external services.

Use one package manager consistently. Prefer `npm` unless the event environment standardizes another tool. Commit the lockfile.

Required maintainer commands:

```text
npm install
npm run dev
npm run build
npm run test
npm run lint
```

The app should run locally with one command. The frontend may proxy `/api` requests to the Express server during development.

### Attendee use

Attendees do not need to install Node.js, install dependencies, or run Cocoarynth Trace during the required session. The prepared local checkout exists so Copilot can inspect the README, application code, fixture data, and tests.

Running the application is optional. If organizers want to permit it on the Surface laptops, prepare and test the environment in advance:

- Install a supported Node.js LTS release for Windows. Use the native Windows Arm64 build on Arm-based Surface devices and the x64 build on Intel devices.
- Verify `node --version` and `npm --version` from the same terminal attendees will use.
- Run `npm ci` before imaging the laptops, or confirm that event network and policy settings allow npm package downloads.
- Confirm that PowerShell execution policy, endpoint protection, proxies, and port restrictions do not block the development command.
- Start the app with `npm run dev` and provide its localhost URL in the README.

Node.js itself runs well on current Surface hardware. The main event risks are software installation permissions and package-registry access, not device performance. Preinstalling Node.js LTS and dependencies makes optional execution straightforward, but none of it should be required to complete the session.

## Suggested repository structure

```text
cocoarynth-trace/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── pull_request_template.md
├── public/
│   └── cocoarynth-logo.png
├── server/
│   ├── app.ts
│   ├── index.ts
│   ├── data/
│   │   ├── batches.ts
│   │   ├── origins.ts
│   │   └── shipments.ts
│   ├── routes/
│   │   ├── batches.ts
│   │   └── passports.ts
│   └── services/
│       └── originPassport.ts
├── shared/
│   └── types.ts
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── api.ts
│   ├── components/
│   │   ├── BatchFilters.tsx
│   │   ├── BatchTable.tsx
│   │   ├── OriginPassportPreview.tsx
│   │   └── ProductionTimeline.tsx
│   ├── pages/
│   │   ├── BatchDetailPage.tsx
│   │   └── BatchesPage.tsx
│   └── styles/
│       └── app.css
├── tests/
│   ├── app.test.ts
│   ├── originPassport.test.ts
│   └── passportRoute.test.ts
├── .gitignore
├── LICENSE
├── README.md
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── tsconfig.json
├── tsconfig.server.json
└── vite.config.ts
```

The exact paths may change to match the chosen scaffold, but the domain model, passport service, HTTP route, user interface, and tests should remain easy to locate.

## Visual direction

Use the supplied Cocoarynth logo and derive the interface from its maze-like cacao pod motif.

- Present the logo prominently in the application header.
- Use the logo's dark cocoa, coral, warm yellow, and leaf-green colors as restrained accents.
- Keep the main workspace light, readable, and suitable for an operations dashboard.
- Use paths, lines, or timeline connectors to echo traceability and the labyrinth concept.
- Keep cards at an 8px radius or less.
- Avoid a marketing hero, decorative gradients, or excessive chocolate imagery.
- Make the batch table and detail view usable at common laptop widths.
- Include clear empty, loading, and error states.

The logo file should be copied into the new repository as `public/cocoarynth-logo.png` or an equivalent asset path.

## Domain model

Keep the model explicit and small enough to understand in one conversation.

### Origin

Required fields:

- `id`
- `country`
- `region`
- `producerName`
- `harvestYear`
- `certificationStatus`

Internal fixture records may also contain confidential fields to demonstrate deliberate omission from exports:

- `producerContactName`
- `producerContactEmail`
- `pricePerKilogram`

These confidential fields must never appear in an Origin Passport response.

### Product

Required fields:

- `id`
- `name`
- `cacaoPercentage`
- `originId`

### Production batch

Required fields:

- `id`
- `batchNumber`
- `productId`
- `productionDate`
- `status`
- `productionEvents`
- `internalQualityNotes`

Recommended statuses:

- `in-production`
- `quality-review`
- `ready`
- `shipped`

### Production event

Required fields:

- `stage`
- `completedAt`
- `operatorName`
- `notes`

Recommended stages:

- `roasting`
- `grinding`
- `conching`
- `tempering`
- `packaging`

Operator names and event notes are internal and must not be included in the Origin Passport.

### Shipment

Required fields:

- `id`
- `batchId`
- `customerName`
- `shippedAt`
- `destination`

Use varied fictional wholesale customers in fixture data.

### Origin Passport

Required exported fields:

- `passportId`
- `productName`
- `batchNumber`
- `country`
- `region`
- `producerName`
- `harvestYear`
- `cacaoPercentage`
- `certificationStatus`
- `productionDate`
- `shipmentDate`
- `generatedAt`

The service should create a new plain object containing only approved fields. Do not serialize the entire batch, origin, or shipment object and then remove selected properties.

## Fixture data

Include four products representing different single origins:

| Product | Suggested producer | Certification |
| --- | --- | --- |
| Ecuador Esmeraldas 72% | Río Verde Cacao Cooperative | Organic verified |
| Ghana Suhum 68% | Asempanaye Growers Union | Fair trade verified |
| Peru Piura Blanco 70% | Valle Blanco Cooperative | Organic pending renewal |
| Madagascar Sambirano 74% | Ambanja Cacao Collective | Direct trade verified |

Include at least six production batches so the table, filters, and status displays feel credible. At least one Ecuador Esmeraldas batch should be shipped and have a complete Origin Passport.

Recommended featured batch:

| Field | Value |
| --- | --- |
| Batch number | `ESM-2026-042` |
| Product | Ecuador Esmeraldas 72% |
| Harvest year | `2026` |
| Production date | `2026-08-18` |
| Shipment date | `2026-08-26` |
| Status | `shipped` |

Use fixed dates and IDs so tests and demonstrations are deterministic.

## Application behavior

### Batch list

The default page should show:

- Batch number
- Product
- Country and region
- Production date
- Status
- Shipment status

Provide simple text search plus origin and status filters. Selecting a row opens the batch detail view.

### Batch detail

The detail view should show:

- Product and batch identity
- Origin and producer details
- Harvest and certification details
- Production timeline
- Shipment details when available
- Origin Passport preview when the batch is shipped
- A **Download JSON** button

### API endpoints

Suggested endpoints:

```text
GET /api/batches
GET /api/batches/:batchId
GET /api/batches/:batchId/passport
```

`GET /api/batches/:batchId/passport` must:

- Return `404` for an unknown batch.
- Return `409` or another clearly documented client error when a batch has not shipped and cannot have a final passport.
- Assemble the passport through the dedicated service.
- Return JSON with `Content-Type: application/json`.
- Set `Content-Disposition` to an attachment filename ending in `.json`.
- Exclude internal, personal, and commercial fields.

Suggested filename:

```text
origin-passport-ESM-2026-042.json
```

### Immutable snapshot concept

Treat an Origin Passport as a generated snapshot of approved data. The repository can implement this by assembling a detached plain object at request time. It does not need persistent snapshot storage for this project.

The merged pull request and GitHub discussion should explain the product intent: a generated passport represents the approved facts associated with a shipment and must not expose mutable internal objects.

Prefer this simple snapshot model over production-grade event storage.

## Required tests

Tests are part of the evidence attendees may inspect. Use descriptive names.

### Origin Passport service tests

- Builds a passport for a shipped batch.
- Includes every approved exported field.
- Uses stable IDs and fixed date values.
- Does not include producer contact details.
- Does not include negotiated prices.
- Does not include internal quality notes.
- Does not include production operator names or event notes.

### Passport route tests

- Returns `application/json`.
- Returns a `.json` attachment filename.
- Returns the expected passport body.
- Returns an error for an unknown batch.
- Returns an error for an unshipped batch.

### Frontend tests

- Displays batch records.
- Opens a batch detail view.
- Shows the production timeline.
- Shows **Download JSON** for an eligible batch.
- Does not show the download action for an ineligible batch.

Keep the `main` test suite passing and scoped to implemented behavior. The open issue represents the planned CSV work.

## README requirements

The attendee-visible README should include:

1. A short description of Cocoarynth and Cocoarynth Trace.
2. A screenshot or concise feature list.
3. Local setup instructions.
4. Available scripts.
5. A high-level architecture summary.
6. A short explanation of Origin Passports as JSON snapshots.
7. A statement that all companies, people, products, and records are fictional.

Keep the README focused on the current application and its JSON Origin Passport behavior.

Suggested opening:

> Cocoarynth Trace is an internal operations application for following single-origin chocolate from cacao harvest through production and wholesale shipment. It generates an Origin Passport that captures approved traceability details for each shipped batch.

## GitHub labels

Create a small, realistic label set:

| Label | Purpose |
| --- | --- |
| `feature` | Product capability |
| `integration` | External data exchange |
| `origin-passport` | Origin Passport work |
| `documentation` | Documentation work |
| `good first issue` | Optional approachable task |
| `priority:high` | Important planned work |
| `status:planned` | Accepted but not started |

Apply `feature`, `integration`, `origin-passport`, `priority:high`, and `status:planned` to the CSV issue.

## Required GitHub history

The repository should not appear as one generated commit. Build a concise history that supports investigation.

### Suggested commit sequence

1. `Initialize Cocoarynth Trace application`
2. `Add batch and origin fixture data`
3. `Add batch list and production timeline`
4. `Add Origin Passport domain model`
5. `Add JSON Origin Passport download endpoint`
6. `Add Origin Passport preview and download action`
7. `Test exported fields and confidential data exclusions`
8. `Add project documentation and contribution templates`

Commits 4 through 7 should be made on a feature branch and merged through the required pull request. Earlier commits may establish the baseline application directly on `main`.

Use your normal Git identity for every commit. The commit messages and sequence supply the project history without fictional author metadata.

## Required merged pull request

Create and merge a feature branch through a pull request so GitHub MCP can retrieve both the PR narrative and its changed files.

**Title:** `Add downloadable Origin Passports for production batches`

**Suggested body:**

```markdown
## Summary

Adds downloadable Origin Passports for shipped production batches. The passport captures approved origin, product, certification, production, and shipment details as a JSON snapshot.

JSON matches the internal catalog integration that motivated the first version of this feature and keeps the payload easy for our existing services to consume.

## Changes

- Add the Origin Passport schema and assembly service
- Add a JSON download endpoint for shipped batches
- Add a passport preview and download action to the batch detail page
- Exclude supplier contacts, commercial terms, and internal production notes
- Add service, route, and user interface tests

## Validation

- Unit and API tests pass
- Production build succeeds
- Verified the downloaded filename and content type
- Verified that confidential fields are absent from the response
```

The pull request should:

- Contain real code changes rather than only narrative.
- Be merged, not left open.
- Predate the CSV issue.

## Required open issue

**Title:** `Support CSV downloads for Origin Passports`

**Suggested body:**

```markdown
## Problem

Origin Passports can currently be downloaded only as JSON. Wholesale operations has asked us to support CSV for partners whose inventory tools use tabular imports.

CSV should be an additional format. Existing JSON downloads must continue to work.

## Acceptance criteria

- Add CSV as an Origin Passport download option
- Use stable, documented column headers
- Format dates as `YYYY-MM-DD`
- Escape commas, quotes, and line breaks correctly
- Return `text/csv` with a `.csv` attachment filename
- Preserve the current allowlist of exported fields
- Add serializer, route, and user interface tests

## Notes

Build the CSV output from the existing Origin Passport model rather than directly from internal batch and supplier records.
```

Issue requirements:

- Leave it open.
- Keep it in planned status without an active pull request or implementation branch.
- Add the required labels.
- Add one short comment confirming that JSON must remain supported.

## Optional open documentation issue

**Title:** `Document the Origin Passport schema for integration partners`

The body should request a stable field reference for integration partners. Mark it as documentation work and state that a temporary field list can be supplied for early integrations. This prevents attendees from mistaking it for the central implementation blocker.

Suggested labels:

- `documentation`
- `origin-passport`
- `good first issue`

## Required GitHub discussion

Enable GitHub Discussions for the repository or organization.

**Category:** Design discussion or General

**Title:** `Which origin details should we share with wholesale partners?`

**Suggested opening post:**

```markdown
As Origin Passports move beyond internal systems, we need a stable boundary between useful traceability data and confidential operational data.

Which fields should be part of the partner-facing passport, and which should remain internal?

The current proposal includes product name, batch number, country, region, producer or cooperative name, harvest year, cacao percentage, certification status, production date, and shipment date.
```

Post these as separate role-labeled replies from your primary account:

1. **Sourcing:** Producer or cooperative name and growing region are essential to the single-origin claim. Personal contact details and negotiated prices must remain internal.
2. **Quality:** Certification status may be shared, but internal quality notes and corrective actions should not be exported automatically.
3. **Production:** Production and shipment dates are useful. Operator names and event notes are internal details.
4. **Engineering summary:** Use an explicit allowlist for the Origin Passport rather than serializing internal records. The agreed fields match the current passport model.

The discussion should reach a clear conclusion about the fields appropriate for partner-facing passports.

## Optional closed issue for realism

Create one closed issue tied to the merged Origin Passport work:

**Title:** `Exclude supplier contact fields from passport response`

The issue can document a pre-merge review finding that was resolved by the Origin Passport allowlist. Close it through the merged pull request or a referenced commit. This reinforces why the export model is deliberately separate from internal records.

Do not add numerous unrelated issues. A small, coherent evidence set will be easier to explore.

## GitHub artifact chronology

Use a believable order so the story can be reconstructed:

1. Create the baseline application and fixture data.
2. Open the Origin Passport pull request.
3. Start the field-sharing discussion while the pull request is open.
4. Incorporate the explicit export allowlist and tests.
5. Approve and merge the Origin Passport pull request.
6. Open the CSV-support issue later as a new integration need.
7. Optionally open the schema documentation issue.

Dates can be recent fictional project dates, but their ordering must remain clear.

## Evidence map

| Expected conclusion | Repository evidence |
| --- | --- |
| Cocoarynth Trace tracks chocolate batches | README, batch pages, API routes, fixtures |
| Origin Passports contain approved traceability fields | Shared type, passport service, tests |
| Current downloads use JSON | Route content type, `.json` filename, UI button, tests |
| JSON was selected for the original internal integration | Merged pull request description |
| CSV is recognized as planned work | Open CSV issue |
| CSV has not been implemented | Current code, UI, tests, open issue state |
| Confidential fields are intentionally excluded | Passport service, tests, pull request, discussion |

## Repository settings

Configure the repository before release:

- Enable Issues.
- Enable Discussions.
- Allow read access for every event-provided account.
- Protect `main` if practical, while ensuring attendees do not need write access.
- Keep the repository and all seeded artifacts read-only for attendees.
- Disable or avoid features that expose irrelevant generated content.
- Ensure the prototype owner's GitHub credential has read access to contents, issues, pull requests, and discussions.
- Confirm organization policy permits the hosted GitHub MCP server.
- Use only synthetic data and fictional identities.

If the repository is public, verify that no secrets or internal event credentials appear anywhere in its history.

## Readiness checks

### Local repository checks

- A fresh clone succeeds on the prepared event laptop.
- The README gives enough context for a first Copilot conversation.
- The application structure is understandable without running the app.
- Attendees can inspect the repository without Node.js or installed dependencies.
- No required exercise instructs attendees to start the application.
- The prepared checkout does not include `node_modules` unless optional app execution has been explicitly enabled and tested.
- `main` reflects the current JSON-only implementation.

### Maintainer application checks

- `npm ci` succeeds using the pinned Node.js LTS version.
- `npm run lint`, `npm run test`, and `npm run build` pass.
- `npm run dev` starts the application without external dependencies.
- The logo and all local assets render without network access.
- The featured Ecuador batch has a complete detail page and JSON passport.
- The JSON download has the expected content type and filename.
- Optional execution is tested on the actual Surface model and event image if it will be offered.

### GitHub artifact checks

- The merged Origin Passport pull request is discoverable by title and keyword.
- The open CSV issue is discoverable by `CSV`, `Origin Passport`, and `export` queries.
- The field-sharing discussion is readable using the prototype owner's GitHub credential.
- GitHub MCP can retrieve repository files, issue bodies and comments, pull request details and changed files, and discussion content.
- Tool output includes enough text to preserve the relevant evidence without relying on comments buried deep in a thread.
- All links returned by GitHub tools are accessible to attendees.

## Suggested validation prompts

Use these prompts during rehearsal with the same clients and permissions attendees will use.

### Local checkout only

> Explain what this project does, identify its main components, and describe how it exports an Origin Passport.

Expected result: the answer identifies JSON behavior from repository files without inventing a customer requirement.

### GitHub MCP only

> Why was the Origin Passport export built this way, and what related work remains open?

Expected result: the answer cites the merged pull request, open CSV issue, and field-sharing discussion.

## Completion checklist

- [ ] Create the `cocoarynth-trace` repository.
- [ ] Add the Cocoarynth logo.
- [ ] Scaffold the TypeScript frontend and API.
- [ ] Add deterministic origin, product, batch, event, and shipment fixtures.
- [ ] Implement the batch list and filters.
- [ ] Implement the batch detail and production timeline.
- [ ] Implement the Origin Passport model and allowlisted assembly service.
- [ ] Implement the JSON preview and download endpoint.
- [ ] Add tests proving JSON behavior and confidential-field exclusions.
- [ ] Add README, license, issue templates, and pull request template.
- [ ] Build the Origin Passport feature through a real merged pull request.
- [ ] Seed the field-sharing GitHub discussion and replies.
- [ ] Create and leave open the CSV-support issue.
- [ ] Optionally add the schema documentation and resolved privacy issues.
- [ ] Configure repository access, Discussions, labels, and the prototype owner's GitHub credential.
- [ ] Run all maintainer build and test checks.
- [ ] Decide whether optional app execution will be enabled on the Surface laptops.
- [ ] If enabled, preinstall and test Node.js LTS and dependencies on the event image.
- [ ] Rehearse GitHub MCP retrieval with the prototype owner's GitHub credential.
