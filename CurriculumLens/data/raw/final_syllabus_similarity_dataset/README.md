# Finalized Syllabus Similarity Dataset (Core Version)

## Decision

The selected source archive is `dataset_zip2.zip`. The canonical core dataset is the 900 manually authored syllabus-section pairs distributed across train, validation, and test splits. It is the best fit for the project's current three-class similarity classifier. The larger mixed-source files in the original archive are intentionally not merged into the core dataset at this stage.

## Files

- `final_dataset.csv` — all 900 examples, sorted by `pair_id`, with a `split` column.
- `train.csv` — 630 examples.
- `val.csv` — 137 examples.
- `test.csv` — 133 examples.
- `audit_report.md` — selection reasoning, checks, limitations, and guidance.

## Label counts

- `highly_similar`: 300
- `partially_similar`: 300
- `unrelated`: 300

## Input and target rules

Use **only** `text_a` and `text_b` as text features. The target is `label`.
Do **not** use `pair_id`, `batch_id`, course names, unit names, domains, topic families, `rationale`, `difficulty`, `data_origin`, or `split` as model features. These fields are for organization, auditing, and evaluation—not for predicting the label.

The labels represent three classes of syllabus-content overlap; they are not percentage scores. A model's predicted class probability must not be presented as a literal syllabus overlap percentage.

## Batch 9 note

The archive does not include a separate `syllabus_similarity_batch_09.csv` file, but all 100 `BATCH09` rows (`PAIR0801` through `PAIR0900`) are present in the 900-row split files. They are therefore preserved in this canonical dataset.

## Limitations

The core examples are synthetic and authored for this project. The structural checks are strong, and representative examples were spot-checked, but this does not prove every subjective `partially_similar` label is correct. Before presenting the model as reliable for real university syllabi, the team should review borderline labels and evaluate on real syllabi annotated by reviewers.
