# TEKS AI Learning Gap Planner (Reading Prototype)

This repository contains a prototype program that can help schools:

1. Analyze student reading data against TEKS learning standards.
2. Identify remediation targets by student and by standard.
3. Recommend differentiated lessons using engagement history.
4. Suggest targeted assessments for weak standards.
5. Predict readiness for next-grade standards.
6. Produce individualized learning plans.

## Why this is useful

The goal is to support a teacher workflow where raw student performance data is converted into clear, actionable plans that close learning gaps.

## Prototype architecture

- **Standards knowledge base**: TEKS-like standards model (`grade`, `subject`, `id`, `description`, prerequisites).
- **Student evidence ingestion**: Reading scores and engagement metrics.
- **Gap analysis engine**: Compares mastery against a configurable mastery threshold.
- **Differentiation engine**: Selects lesson strategies based on engagement profile.
- **Assessment recommender**: Flags standards that require quick checks.
- **Predictive model (baseline)**: Uses current mastery and engagement to estimate next-grade readiness.
- **Plan generator**: Produces student-level individualized plans in JSON.

## Quick start (run the program)

1. From the repo root, run:

```bash
python3 src/teks_ai_planner.py \
  --standards data/sample_teks.json \
  --students data/sample_students_reading.csv \
  --subject Reading \
  --grade 3 \
  --next-grade 4 \
  --output output/plans.json
```

2. Inspect the generated plan file:

```bash
python3 -m json.tool output/plans.json | head -n 60
```

## Debugging guide

### 1) Verify CLI arguments

Print all available options:

```bash
python3 src/teks_ai_planner.py --help
```

### 2) Run with debug logs

Use `--debug` to print processing details (matching standards, number of students, remediation counts, readiness scores):

```bash
python3 src/teks_ai_planner.py \
  --standards data/sample_teks.json \
  --students data/sample_students_reading.csv \
  --subject Reading \
  --grade 3 \
  --next-grade 4 \
  --output output/plans.json \
  --debug
```

### 3) Common failure checks

- **No students in output**: Confirm `subject` and `grade` match rows in CSV exactly (`Reading`, `3`).
- **Empty remediation targets**: This means student mastery is above `--mastery-threshold`. Try a higher threshold (for example `--mastery-threshold 0.75`).
- **File errors**: Ensure JSON/CSV paths are correct and run from repo root.

### 4) Run tests while debugging

```bash
python3 -m unittest discover -s tests -v
```

## Inputs

### Standards JSON schema

```json
{
  "standards": [
    {
      "id": "3.6A",
      "grade": 3,
      "subject": "Reading",
      "description": "...",
      "prerequisites": []
    }
  ]
}
```

### Student CSV schema

Required columns:

- `student_id`
- `student_name`
- `subject`
- `grade`
- `standard_id`
- `mastery_score` (0.0-1.0)
- `engagement_score` (0.0-1.0)
- `preferred_modality` (e.g. `visual`, `collaborative`, `independent`, `multisensory`)

## Output

The output is a JSON object with one plan per student including:

- remediation standards ranked by urgency,
- differentiated lesson recommendations,
- suggested targeted assessments,
- predicted next-grade readiness,
- an individualized 4-week action plan.

## Suggested next steps for production

- Replace baseline predictor with a trained model using historical district data.
- Add explainability artifacts for each prediction.
- Integrate attendance, benchmark growth, and intervention fidelity data.
- Add teacher-facing UI and approval workflow before plans are assigned.
- Add role-based access controls and FERPA-compliant data handling.
