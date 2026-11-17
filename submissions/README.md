# Benchmark submissions

One folder per student. Submit by **pull request** — never commit to `main` directly.

## How to submit

1. Create a branch: `git checkout -b benchmark/<your-folder-name>`
2. Put your labels in **your own folder** as one JSONL file:

   ```
   submissions/<your-folder>/benchmark_<lastname>.jsonl
   ```

   Every line is one record matching `tests/benchmark/benchmark_schema.json` —
   all 6 fields for each of your 10 assigned accessions (see
   `docs/accession_assignments.md`), each label carrying a **verbatim quote**
   and the **source step** where you found it.

3. Validate locally before pushing:

   ```
   python tests/run_benchmark.py submissions/<your-folder>/benchmark_<lastname>.jsonl
   ```

4. Open a PR titled `Benchmark: <Your Name> (<n> records)`. CI runs the same
   harness on your file and posts the score report on the PR.

## Reading your CI result

- **Malformed records** (bad JSON, missing fields) — fix and push again. This
  part must pass.
- **Extraction disagreements** (e.g., `false_assertion` lines) — these are
  **not automatically your error**. Your labels are the ground truth; a
  disagreement may mean the extraction engine is wrong, which is exactly what
  this benchmark exists to catch. If your quote and source step support your
  label, keep it and note the disagreement in your PR description — those are
  the most valuable records you can contribute.

## Rules

- Label independently. In particular, do **not** discuss the two calibration
  accessions (they're how we measure inter-annotator agreement).
- Quotes must be verbatim from the source page; no paraphrases.
- When the metadata doesn't state a field, the honest label is the abstention
  state per the assignment — never a guess.
- All deliverables use docs/STUDENT_RESPONSE_FORMS.md — commit labels before your first harness run.

## Folders

| Folder | Student |
|---|---|
| ben-nance/ | Ben Nance |
| andrew-martin/ | Andrew Martin |
| josiah-duvalin/ | Josiah Duvalin |
| micah-kelley/ | Micah Kelley |
| nathanael-williams/ | Nathanael Williams |
| oliver-pham/ | Oliver Pham |
