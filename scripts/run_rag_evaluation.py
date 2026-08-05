from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path

import httpx

API_URL = os.getenv("RAG_API_BASE_URL", "http://127.0.0.1:8000")
EMAIL = os.getenv("RAG_LOGIN_EMAIL", "admin@izeltas.local")
PASSWORD = os.getenv("RAG_LOGIN_PASSWORD", "Admin123!")


def normalize(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def load_cases(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "id",
        "question",
        "expected_response_type",
        "expected_document_ids",
        "accepted_sections",
        "required_keywords",
    }

    if not isinstance(cases, list):
        raise ValueError("Test dosyası JSON listesi olmalıdır.")

    for index, case in enumerate(cases, 1):
        missing = required - set(case)
        if missing:
            raise ValueError(
                f"{index}. test vakasında eksik alanlar: {sorted(missing)}"
            )

    return cases


def login(client: httpx.Client) -> str:
    response = client.post(
        f"{API_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    response.raise_for_status()

    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("access_token bulunamadı.")

    return str(token)


def ask(
    client: httpx.Client,
    token: str,
    question: str,
) -> tuple[dict, float]:
    started = time.perf_counter()

    response = client.post(
        f"{API_URL}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": question},
        timeout=120,
    )
    elapsed = time.perf_counter() - started

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("Chat cevabı JSON nesnesi olmalıdır.")

    return data, elapsed


def values(sources: list[dict], field: str) -> list[str]:
    return [
        str(source[field]) for source in sources if source.get(field) not in (None, "")
    ]


def scores(sources: list[dict]) -> list[str]:
    result = []

    for source in sources:
        value = source.get("score", source.get("distance"))
        if value is not None:
            result.append(str(value))

    return result


def matches(expected: list[str], actual: list[str]) -> bool:
    if not expected:
        return not actual

    expected_set = {normalize(item) for item in expected}
    actual_set = {normalize(item) for item in actual}
    return bool(expected_set & actual_set)


def keyword_check(
    answer: str,
    keywords: list[str],
    minimum: int,
) -> tuple[bool, int]:
    if not keywords:
        return True, 0

    normalized_answer = normalize(answer)
    hits = sum(normalize(keyword) in normalized_answer for keyword in keywords)
    required = min(max(minimum, 1), len(keywords))

    return hits >= required, hits


def format_check(
    answer: str,
    response_type: str,
) -> tuple[bool, int, str]:
    if response_type != "rag_answer":
        return True, 0, ""

    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    bullets = [line for line in lines if line.startswith("- ")]
    problems = []

    if not 1 <= len(bullets) <= 3:
        problems.append("bullet_count")

    if len(lines) != len(bullets):
        problems.append("non_bullet_text")

    cleaned = [normalize(line.removeprefix("- ").rstrip(".!?")) for line in bullets]
    if len(cleaned) != len(set(cleaned)):
        problems.append("duplicate_bullets")

    return not problems, len(bullets), "|".join(problems)


def evaluate(
    case: dict,
    response: dict,
    elapsed: float,
    model: str,
    run: int,
) -> dict:
    answer = str(response.get("answer") or "")
    response_type = str(response.get("response_type") or "")
    sources = response.get("sources") or []
    sources = sources if isinstance(sources, list) else []

    actual_documents = values(sources, "document_id")
    actual_sections = values(sources, "section_title")

    expected_documents = case["expected_document_ids"]
    accepted_sections = case["accepted_sections"]
    required_keywords = case["required_keywords"]

    type_match = response_type == case["expected_response_type"]
    source_match = matches(expected_documents, actual_documents)
    section_match = matches(accepted_sections, actual_sections)

    keyword_match, keyword_hits = keyword_check(
        answer,
        required_keywords,
        int(case.get("min_keyword_hits", 1)),
    )
    format_match, bullet_count, format_problem = format_check(
        answer,
        response_type,
    )

    case_pass = all(
        [
            type_match,
            source_match,
            section_match,
            keyword_match,
            format_match,
        ]
    )

    return {
        "model": model,
        "case_id": case["id"],
        "run": run,
        "question": case["question"],
        "answer": answer,
        "expected_response_type": case["expected_response_type"],
        "response_type": response_type,
        "response_type_match": type_match,
        "expected_document_ids": " | ".join(expected_documents),
        "actual_document_ids": " | ".join(actual_documents),
        "source_match": source_match,
        "accepted_sections": " | ".join(accepted_sections),
        "actual_sections": " | ".join(actual_sections),
        "section_match": section_match,
        "source_scores": " | ".join(scores(sources)),
        "required_keywords": " | ".join(required_keywords),
        "keyword_match": keyword_match,
        "keyword_hit_count": keyword_hits,
        "answer_format_match": format_match,
        "bullet_count": bullet_count,
        "answer_format_problems": format_problem,
        "case_pass": case_pass,
        "response_time_seconds": round(elapsed, 3),
        "error": "",
        "manual_quality_score": "",
        "manual_notes": "",
    }


def failed_row(case: dict, model: str, run: int, error: Exception) -> dict:
    row = evaluate(
        case=case,
        response={"answer": "", "response_type": "", "sources": []},
        elapsed=0,
        model=model,
        run=run,
    )
    row["response_time_seconds"] = ""
    row["error"] = str(error)
    return row


def summary(rows: list[dict], model: str) -> dict:
    times = [
        float(row["response_time_seconds"])
        for row in rows
        if row["response_time_seconds"] != ""
    ]

    result = {
        "model": model,
        "total_run_count": len(rows),
        "case_pass_count": sum(row["case_pass"] for row in rows),
        "source_match_count": sum(row["source_match"] for row in rows),
        "section_match_count": sum(row["section_match"] for row in rows),
        "keyword_match_count": sum(row["keyword_match"] for row in rows),
        "response_type_match_count": sum(row["response_type_match"] for row in rows),
        "answer_format_match_count": sum(row["answer_format_match"] for row in rows),
        "request_error_count": sum(bool(row["error"]) for row in rows),
    }

    result["average_response_time_seconds"] = (
        round(sum(times) / len(times), 3) if times else ""
    )
    result["min_response_time_seconds"] = round(min(times), 3) if times else ""
    result["max_response_time_seconds"] = round(max(times), 3) if times else ""

    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("docs/evaluation/cases/evaluation-cases.json"),
    )
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    rows = []

    with httpx.Client() as client:
        token = login(client)

        for case in cases:
            for run in range(1, args.repeat + 1):
                print(f"[{args.model}] {case['id']} " f"run {run}/{args.repeat}")

                try:
                    response, elapsed = ask(
                        client,
                        token,
                        case["question"],
                    )
                    row = evaluate(
                        case,
                        response,
                        elapsed,
                        args.model,
                        run,
                    )
                except Exception as error:
                    row = failed_row(
                        case,
                        args.model,
                        run,
                        error,
                    )

                rows.append(row)

                if not row["case_pass"]:
                    print(f"  FAIL: {case['question']}")

    model_name = args.model.replace(":", "-").replace("/", "-")
    output_dir = Path("docs/evaluation/results") / model_name

    write_csv(output_dir / "results.csv", rows)
    write_csv(output_dir / "summary.csv", [summary(rows, args.model)])

    print("\nEvaluation completed.")
    print(f"Results: {output_dir / 'results.csv'}")
    print(f"Summary: {output_dir / 'summary.csv'}")


if __name__ == "__main__":
    main()