from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class Standard:
    id: str
    grade: int
    subject: str
    description: str
    prerequisites: list[str]


@dataclass(frozen=True)
class StudentEvidence:
    student_id: str
    student_name: str
    subject: str
    grade: int
    standard_id: str
    mastery_score: float
    engagement_score: float
    preferred_modality: str


def load_standards(path: str | Path) -> list[Standard]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    standards: list[Standard] = []
    for s in payload.get("standards", []):
        standards.append(
            Standard(
                id=s["id"],
                grade=int(s["grade"]),
                subject=s["subject"],
                description=s["description"],
                prerequisites=s.get("prerequisites", []),
            )
        )
    return standards


def load_student_evidence(path: str | Path) -> list[StudentEvidence]:
    rows: list[StudentEvidence] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                StudentEvidence(
                    student_id=r["student_id"],
                    student_name=r["student_name"],
                    subject=r["subject"],
                    grade=int(r["grade"]),
                    standard_id=r["standard_id"],
                    mastery_score=float(r["mastery_score"]),
                    engagement_score=float(r["engagement_score"]),
                    preferred_modality=r["preferred_modality"],
                )
            )
    return rows


def modality_to_strategies(modality: str) -> list[str]:
    lookup = {
        "visual": [
            "Use annotated mentor texts and graphic organizers.",
            "Provide color-coded evidence tracking for comprehension questions.",
        ],
        "collaborative": [
            "Run partner think-alouds with sentence stems.",
            "Use small-group reciprocal teaching routines.",
        ],
        "independent": [
            "Assign short independent close-reading cycles with feedback.",
            "Use self-monitoring checklists for reading strategies.",
        ],
        "multisensory": [
            "Incorporate movement-based vocabulary and decoding routines.",
            "Blend oral rehearsal, writing, and visual cues in each lesson.",
        ],
    }
    return lookup.get(modality, ["Use mixed-modality mini-lessons and quick checks."])


def identify_remediation_needs(
    evidence: list[StudentEvidence],
    mastery_threshold: float,
) -> list[dict[str, Any]]:
    remediation = []
    for ev in evidence:
        if ev.mastery_score < mastery_threshold:
            urgency = round((mastery_threshold - ev.mastery_score) * (1.2 - ev.engagement_score), 4)
            remediation.append(
                {
                    "standard_id": ev.standard_id,
                    "mastery_score": ev.mastery_score,
                    "engagement_score": ev.engagement_score,
                    "urgency": urgency,
                    "differentiated_strategies": modality_to_strategies(ev.preferred_modality),
                    "assessment_suggestion": (
                        "Administer a 5-question targeted check for this standard and review errors with student conferencing."
                    ),
                }
            )

    return sorted(remediation, key=lambda x: x["urgency"], reverse=True)


def predict_next_grade_readiness(student_rows: list[StudentEvidence]) -> float:
    """
    Baseline predictor in [0,1].
    Weighted toward mastery with engagement as a multiplier.
    """
    mastery_avg = mean(r.mastery_score for r in student_rows)
    engagement_avg = mean(r.engagement_score for r in student_rows)
    score = 0.75 * mastery_avg + 0.25 * engagement_avg
    return round(max(0.0, min(1.0, score)), 4)


def build_individual_plan(
    student_id: str,
    student_name: str,
    grade: int,
    subject: str,
    remediation: list[dict[str, Any]],
    readiness_prediction: float,
) -> dict[str, Any]:
    weekly_focus = []
    top_targets = remediation[:4]

    for i, target in enumerate(top_targets, start=1):
        weekly_focus.append(
            {
                "week": i,
                "standard_id": target["standard_id"],
                "goal": f"Increase mastery on {target['standard_id']} through targeted intervention.",
                "lesson_strategies": target["differentiated_strategies"],
                "assessment": target["assessment_suggestion"],
            }
        )

    return {
        "student_id": student_id,
        "student_name": student_name,
        "grade": grade,
        "subject": subject,
        "predicted_next_grade_readiness": readiness_prediction,
        "remediation_targets": remediation,
        "individualized_4_week_plan": weekly_focus,
        "notes": [
            "Prediction is a baseline estimate and should be validated with benchmark assessments.",
            "Teacher review is required before assigning interventions.",
        ],
    }


def group_by_student(rows: list[StudentEvidence], grade: int, subject: str) -> dict[str, list[StudentEvidence]]:
    grouped: dict[str, list[StudentEvidence]] = {}
    for row in rows:
        if row.grade != grade or row.subject.lower() != subject.lower():
            continue
        grouped.setdefault(row.student_id, []).append(row)
    return grouped


def generate_plans(
    standards: list[Standard],
    rows: list[StudentEvidence],
    grade: int,
    subject: str,
    mastery_threshold: float = 0.7,
    debug: bool = False,
) -> dict[str, Any]:
    matching_standards = [s for s in standards if s.grade == grade and s.subject.lower() == subject.lower()]
    if debug:
        print(
            f"[DEBUG] Loaded {len(standards)} total standards; "
            f"{len(matching_standards)} match grade={grade}, subject={subject}."
        )

    by_student = group_by_student(rows, grade, subject)
    if debug:
        print(f"[DEBUG] Found {len(by_student)} students in filtered evidence.")

    plans = []
    for student_id, student_rows in by_student.items():
        if not student_rows:
            continue

        remediation = identify_remediation_needs(student_rows, mastery_threshold)
        readiness = predict_next_grade_readiness(student_rows)
        first = student_rows[0]
        if debug:
            print(
                f"[DEBUG] Student {first.student_name} ({student_id}): "
                f"{len(remediation)} remediation targets, readiness={readiness}"
            )
        plans.append(
            build_individual_plan(
                student_id=student_id,
                student_name=first.student_name,
                grade=first.grade,
                subject=first.subject,
                remediation=remediation,
                readiness_prediction=readiness,
            )
        )

    return {
        "grade": grade,
        "subject": subject,
        "mastery_threshold": mastery_threshold,
        "student_plans": plans,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TEKS-aligned AI planning prototype")
    parser.add_argument("--standards", required=True, help="Path to standards JSON")
    parser.add_argument("--students", required=True, help="Path to student CSV")
    parser.add_argument("--subject", required=True, help="Subject, e.g. Reading")
    parser.add_argument("--grade", required=True, type=int, help="Current grade level")
    parser.add_argument("--next-grade", required=False, type=int, help="Reserved for expanded predictors")
    parser.add_argument("--output", required=True, help="Output path for generated plans JSON")
    parser.add_argument("--mastery-threshold", default=0.7, type=float)
    parser.add_argument("--debug", action="store_true", help="Print debug details during plan generation")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    standards = load_standards(args.standards)
    rows = load_student_evidence(args.students)
    report = generate_plans(
        standards=standards,
        rows=rows,
        grade=args.grade,
        subject=args.subject,
        mastery_threshold=args.mastery_threshold,
        debug=args.debug,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
