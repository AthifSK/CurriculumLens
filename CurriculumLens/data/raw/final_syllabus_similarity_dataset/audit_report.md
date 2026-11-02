# Dataset Selection and Audit Report

## Recommendation

**Select `dataset_zip2.zip` as the primary dataset package**, using its 900-row core train/validation/test split as the frozen dataset for the current three-class classifier. Do not train the first model on all available mixed-source rows by default. Keep the larger generated pairs as a separate augmentation experiment and use separate tests to measure whether augmentation helps.

## Why this one

| Candidate archive | Contents observed | Strength | Main drawback for the immediate step |
|---|---|---|---|
| `dataset.zip` | 2,016 courses, 9,089 modules, 3,832 course pairs with ground-truth labels | Large generated course/module set, concept tags, aligned modules, seen/unseen splits | Course-pair labels use five categories (`distinct`, `low overlap`, `partial overlap`, `high overlap`, `near-duplicate`), so converting to the project's three labels requires an explicit mapping; it is a less direct starting point |
| `dataset_zip2.zip` | 900 core labelled section pairs (630/137/133); also contains derived mixed-source files: 8,441 train rows, 971 validation rows and separate evaluation sets | Direct match to desired three labels, balanced classes, already split, varied topics, and distinct external/seen/unseen evaluation sets | All core examples are synthetic; larger mixed-source files need a controlled augmentation experiment rather than automatic merging |
| `files.zip` | 84 courses, 540 topics, 1,840 course-pair labels, 658 aligned-topic records, 24 novelty-labelled proposed courses | Best dedicated structure for later course-level novelty analysis and evidence/explanation checks | Too small and label-skewed to be the sole training dataset for the current classifier: `none`=1,530, `low`=213, `moderate`=83, `high`=14 in its full pair-label table; only 24 proposed-course novelty labels |

## Core dataset audit

- Total rows: **900**.
- Schema: **17 columns** (the original 16 columns plus `split`).
- Split sizes: **{'train': 630, 'test': 133, 'val': 137}**.
- Label counts: **{'highly_similar': 300, 'unrelated': 300, 'partially_similar': 300}**.
- `data_origin` counts: **{'synthetic': 900}**.
- Batch counts: **{'BATCH01': 100, 'BATCH02': 100, 'BATCH03': 100, 'BATCH04': 100, 'BATCH05': 100, 'BATCH06': 100, 'BATCH07': 100, 'BATCH08': 100, 'BATCH09': 100}**; each batch has 100 rows.
- Missing/blank cells: **0**.
- Empty `text_a` or `text_b`: **0**.
- Duplicate pair IDs: **0**.
- Duplicate normalized text pairs: **0**.
- Exact normalized text pairs shared across splits: **{'train-val': 0, 'train-test': 0, 'val-test': 0}** (none).
- Topic-family values shared across train/validation/test: **{'train-val': 0, 'train-test': 0, 'val-test': 0}** (none, considering both A and B sides).
- The 900-row dataset is exactly class-balanced, with 300 rows per class.

## Important batch-file discrepancy

The archive has separate batch files only for BATCH01–BATCH08 (800 rows). However, the train/validation/test files together contain all 900 IDs and include 100 rows labelled `BATCH09`, IDs `PAIR0801`–`PAIR0900`. This package preserves those rows from the split files. Do not generate a second Batch 9 and append it without checking for duplicate IDs/content first.

## Label quality and leakage considerations

The structural checks found no missing data, exact pair duplicates, pair-ID collisions, or text-side/topic-family overlap between the three splits. Representative rows from all three classes were spot-checked and looked coherent. This is not a full expert annotation audit: in particular, `partially_similar` is a judgement-based class and should get a dedicated borderline-label review before claiming strong real-world accuracy.

The train/validation/test split is topic-family-disjoint, which is useful for checking performance on topic families not seen during training. Course names can recur across splits, so **the model must use only `text_a` and `text_b`**. Do not feed course names, unit names, topic-family labels, domains, rationales, batch IDs or other metadata to the classifier.

## How to use the other files later

1. First establish a reproducible baseline on this 900-row core dataset.
2. Evaluate it without tuning on `test.csv`.
3. Only then test controlled augmentation with `combined_train.csv` and evaluate separately on `test_theirs_seen.csv` and `test_theirs_unseen.csv`. Those pairs are derived from a different synthetic generator, and their class mapping is based on module alignments, so performance should be reported by source, not only as a single blended score.
4. Keep `files.zip`'s topic alignments and novelty labels as a separate resource for the later novelty/explanation component; do not casually mix its four-level course-pair labels into the current three-class targets.

## Real-world limitation

All three submitted archives are synthetic. The selected dataset is a good controlled benchmark for building the prototype, but it cannot by itself validate performance on real university syllabi. For that, collect permitted real syllabi and get independent reviewers to annotate overlap and novelty.
