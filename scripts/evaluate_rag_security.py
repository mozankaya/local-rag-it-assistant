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

    if not isinstance(cases, list):
        raise ValueError("Test dosyası JSON listesi olmalıdır.")

    required_fields = {
        "id",
        "category",
        "question",
        "allowed_response_types",
        "forbidden_phrases",
    }

    for index, case in enumerate(cases, 1):
        missing = required_fields - set(case)

        if missing:
            raise ValueError(
                f"{index}. test vakasında eksik alanlar: {sorted(missing)}"
            )

    return cases


def build_question(case: dict) -> str:
    question = str(case["question"])
    repeat_count = int(case.get("repeat_count", 1))

    return question * repeat_count


def login(client: httpx.Client) -> str:
    response = client.post(
        f"{API_URL}/auth/login",
        json={
            "email": EMAIL,
            "password": PASSWORD,
        },
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
) -> tuple[int, dict, float]:
    started = time.perf_counter()

    response = client.post(
        f"{API_URL}/chat",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "question": question,
        },
        timeout=120,
    )

    elapsed = time.perf_counter() - started

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not isinstance(data, dict):
        data = {}

    return response.status_code, data, elapsed


def find_forbidden_phrases(
    answer: str,
    forbidden_phrases: list[str],
) -> list[str]:
    normalized_answer = normalize(answer)
    found = []

    for phrase in forbidden_phrases:
        if normalize(phrase) in normalized_answer:
            found.append(phrase)

    return found


def check_sources(
    expected: bool | None,
    source_count: int,
) -> bool:
    if expected is None:
        return True

    if expected:
        return source_count > 0

    return source_count == 0


def evaluate_case(
    case: dict,
    question: str,
    status_code: int,
    response: dict,
    elapsed: float,
    model: str,
    run: int,
) -> dict:
    expected_status = int(case.get("expected_http_status", 200))
    allowed_types = case["allowed_response_types"]
    forbidden_phrases = case["forbidden_phrases"]
    expected_sources = case.get("expect_sources")

    answer = str(response.get("answer") or "")
    response_type = str(response.get("response_type") or "")
    sources = response.get("sources") or []

    if not isinstance(sources, list):
        sources = []

    status_match = status_code == expected_status

    if expected_status == 200:
        response_type_match = response_type in allowed_types
        sources_match = check_sources(
            expected_sources,
            len(sources),
        )
    else:
        response_type_match = True
        sources_match = True

    forbidden_found = find_forbidden_phrases(
        answer,
        forbidden_phrases,
    )
    forbidden_check_pass = not forbidden_found

    case_pass = all(
        [
            status_match,
            response_type_match,
            sources_match,
            forbidden_check_pass,
        ]
    )

    detail = response.get("detail", "")

    if isinstance(detail, (dict, list)):
        detail = json.dumps(
            detail,
            ensure_ascii=False,
        )

    return {
        "model": model,
        "case_id": case["id"],
        "category": case["category"],
        "run": run,
        "question": question,
        "expected_http_status": expected_status,
        "actual_http_status": status_code,
        "http_status_match": status_match,
        "allowed_response_types": " | ".join(allowed_types),
        "actual_response_type": response_type,
        "response_type_match": response_type_match,
        "expected_sources": expected_sources,
        "source_count": len(sources),
        "sources_match": sources_match,
        "forbidden_phrases": " | ".join(forbidden_phrases),
        "forbidden_phrases_found": " | ".join(forbidden_found),
        "forbidden_check_pass": forbidden_check_pass,
        "case_pass": case_pass,
        "response_time_seconds": round(elapsed, 3),
        "answer": answer,
        "response_detail": str(detail),
        "error": "",
        "manual_notes": "",
    }


def failed_row(
    case: dict,
    question: str,
    model: str,
    run: int,
    error: Exception,
) -> dict:
    return {
        "model": model,
        "case_id": case["id"],
        "category": case["category"],
        "run": run,
        "question": question,
        "expected_http_status": int(
            case.get("expected_http_status", 200)
        ),
        "actual_http_status": "",
        "http_status_match": False,
        "allowed_response_types": " | ".join(
            case["allowed_response_types"]
        ),
        "actual_response_type": "",
        "response_type_match": False,
        "expected_sources": case.get("expect_sources"),
        "source_count": 0,
        "sources_match": False,
        "forbidden_phrases": " | ".join(
            case["forbidden_phrases"]
        ),
        "forbidden_phrases_found": "",
        "forbidden_check_pass": False,
        "case_pass": False,
        "response_time_seconds": "",
        "answer": "",
        "response_detail": "",
        "error": str(error),
        "manual_notes": "",
    }


def create_summary(
    rows: list[dict],
    model: str,
) -> dict:
    times = [
        float(row["response_time_seconds"])
        for row in rows
        if row["response_time_seconds"] != ""
    ]

    return {
        "model": model,
        "total_run_count": len(rows),
        "passed_count": sum(
            row["case_pass"] for row in rows
        ),
        "failed_count": sum(
            not row["case_pass"] for row in rows
        ),
        "request_error_count": sum(
            bool(row["error"]) for row in rows
        ),
        "average_response_time_seconds": (
            round(sum(times) / len(times), 3)
            if times
            else ""
        ),
        "max_response_time_seconds": (
            round(max(times), 3)
            if times
            else ""
        ),
    }


def write_csv(
    path: Path,
    rows: list[dict],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        required=True,
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(
            "docs/evaluation/cases/"
            "rag-security-cases.json"
        ),
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    rows = []

    with httpx.Client() as client:
        token = login(client)

        for case in cases:
            question = build_question(case)

            for run in range(
                1,
                args.repeat + 1,
            ):
                print(
                    f"[{args.model}] "
                    f"{case['id']} "
                    f"run {run}/{args.repeat}"
                )

                try:
                    status_code, response, elapsed = ask(
                        client,
                        token,
                        question,
                    )

                    row = evaluate_case(
                        case=case,
                        question=question,
                        status_code=status_code,
                        response=response,
                        elapsed=elapsed,
                        model=args.model,
                        run=run,
                    )

                except Exception as error:
                    row = failed_row(
                        case=case,
                        question=question,
                        model=args.model,
                        run=run,
                        error=error,
                    )

                rows.append(row)

                result_text = (
                    "PASS"
                    if row["case_pass"]
                    else "FAIL"
                )
                print(f"  {result_text}")

    model_name = (
        args.model
        .replace(":", "-")
        .replace("/", "-")
    )

    output_dir = (
        Path("docs/evaluation/results/security")
        / model_name
    )

    write_csv(
        output_dir / "results.csv",
        rows,
    )
    write_csv(
        output_dir / "summary.csv",
        [create_summary(rows, args.model)],
    )

    print("\nSecurity evaluation completed.")
    print(
        f"Results: "
        f"{output_dir / 'results.csv'}"
    )
    print(
        f"Summary: "
        f"{output_dir / 'summary.csv'}"
    )


if __name__ == "__main__":
    main()
