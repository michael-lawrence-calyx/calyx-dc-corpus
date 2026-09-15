# Calyx Data Center Corpus

Public instrument register. One file per provision. Plain text, versioned in git.

## What is in here

The **register**: what instruments exist, where to find them, what section governs what,
and when each was last read. Over public records, so publishing it costs nothing and
makes the work findable.

## What is NOT in here

Marked provisions with origin/state/freshness assessments. Draft-to-draft diffs.
Cross-jurisdiction comparisons. Parcel-level constraint sets. Account numbers, tax lots,
ledgers. Client work. Those live in `calyx-corpus-private`.

Findings publish. The marked corpus does not.

## Layout

    entries/<state>/<jurisdiction>/<slug>.json   one provision per file
    sources/<state>/<jurisdiction>/SOURCES.md    where each document lives
    schema/entry.schema.json                     the contract
    build.py                                     entries -> docs/index.json
    docs/                                        the query engine (GitHub Pages)

## Two fields that look similar and are not

- **`notes`** — context. What the provision relates to, how it applies, what it connects to.
- **`confidence_note`** — what this entry does NOT establish, and where we are uncertain.

They are separate so you can query every entry where you flagged your own uncertainty.
`grep -l confidence_note entries -r` is your honest-limits report.

## Jurisdictions are a controlled list

`jurisdiction` is a **key** from `schema/jurisdictions.json`, never a display name.
`us-az-maricopa-county`, not "Maricopa County" or "Maricopa Co."
Adding a jurisdiction means adding it to that file first. The build fails otherwise.

Entry files live at `entries/<STATE>/<jurisdiction-key>/<id>.json`. The validator
checks the path matches the key.

## Rules

1. **One provision per file.** Not one ordinance. If a section covers noise limits and
   study cadence, that is two entries.
2. **`text` is verbatim or empty.** Never paraphrase into that field. If you have not
   read the original, leave it empty and set `origin: RELAYED`.
3. **A human sets `origin` and `state`.** Agents may draft an entry. No agent commits one.
   The moment a machine assigns CONFIRMED the marks are worthless.
4. **Never edit an entry to correct a fact.** Add a new entry with a later `retrieved`
   date and set `supersedes` on it. Git keeps the history; the corpus keeps the record
   of what was believed when.
5. **`id` convention is permanent:** `<state>-<jurisdiction>-<instrument>-<topic>`,
   lowercase, hyphens only. Once an id appears in a `supersedes` chain it can never change.
6. **Every entry names where the source document lives.** Drive path or URL. An entry
   whose source cannot be retrieved is not an entry.

## Running it

    python3 build.py        # regenerates docs/index.json
    open docs/index.html    # or serve docs/ anywhere static

## Drive convention

Binaries do not go in git. Source PDFs live in Drive:

    /Calyx DC Corpus/<STATE>/<JURISDICTION>/<YYYY-MM-DD>-<slug>.pdf

Filename starts with the date the document was retrieved, not the date it was issued.
The entry's `source.file` field carries that exact path.
