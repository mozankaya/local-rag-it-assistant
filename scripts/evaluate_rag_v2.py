import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


DEFAULT_API_BASE_URL = os.getenv("RAG_API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_LOGIN_EMAIL = os.getenv("RAG_LOGIN_EMAIL", "admin@izeltas.local")
DEFAULT_LOGIN_PASSWORD = os.getenv("RAG_LOGIN_PASSWORD", "Admin123!")


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def login(
    client: httpx.Client,
    api_base_url: str,
    email: str,
    password: str,
) -> str:
    response = client.post(
        f"{api_base_url}/auth/login",
        json={
            "email": email,
            "password": password,
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    token = data.get("access_token")

    if not token:
        raise RuntimeError("Login response does not contain access_token.")

    return str(token)


def ask_question(
    client: httpx.Client,
    api_base_url: str,
    token: str,
    question: str,
) -> tuple[dict[str, Any], float]:
    start_time = time.perf_counter()

    response = client.post(
        f"{api_base_url}/chat",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "question": question,
        },
        timeout=120,
    )

    elapsed_seconds = time.perf_counter() - start_time
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("Chat response must be a JSON object.")

    return data, elapsed_seconds


def load_test_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Evaluation file must contain a JSON array.")

    required_fields = {
        "id",
        "question",
        "expected_response_type",
        "expected_document_ids",
        "accepted_sections",
        "required_keywords",
    }

    for index, case in enumerate(data, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Test case {index} must be a JSON object.")

        missing = required_fields - set(case)
        if missing:
            raise ValueError(
                f"Test case {index} is missing fields: {sorted(missing)}"
            )

    return data


def get_source_document_ids(sources: list[dict[str, Any]]) -> list[str]:
    return [
        str(source.get("document_id") or "")
        for source in sources
        if source.get("document_id")
    ]


def get_source_sections(sources: list[dict[str, Any]]) -> list[str]:
    return [
        str(source.get("section_title") or "")
        for source in sources
        if source.get("section_title")
    ]


def get_source_scores(sources: list[dict[str, Any]]) -> list[str]:
    scores: list[str] = []

    for source in sources:
        score = (
            source.get("score")
            if source.get("score") is not None
            else source.get("distance")
        )

        if score is not None:
            scores.append(str(score))

    return scores


def evaluate_source_match(
    expected_document_ids: list[str],
    actual_document_ids: list[str],
) -> bool:
    if not expected_document_ids:
        return len(actual_document_ids) == 0

    expected = set(expected_document_ids)
    return any(document_id in expected for document_id in actual_document_ids)


def evaluate_section_match(
    accepted_sections: list[str],
    actual_sections: list[str],
) -> bool:
    if not accepted_sections:
        return len(actual_sections) == 0

    normalized_expected = {
        normalize_text(section)
        for section in accepted_sections
    }

    normalized_actual = {
        normalize_text(section)
        for section in actual_sections
    }

    return bool(normalized_expected & normalized_actual)


def get_keyword_hit_count(answer: str, keywords: list[str]) -> int:
    normalized_answer = normalize_text(answer)

    return sum(
        1
        for keyword in keywords
        if normalize_text(keyword) in normalized_answer
    )


def evaluate_keyword_match(
    answer: str,
    keywords: list[str],
    min_keyword_hits: int,
) -> tuple[bool, int]:
    if not keywords:
        return True, 0

    hit_count = get_keyword_hit_count(answer, keywords)
    required_hits = min(max(min_keyword_hits, 1), len(keywords))

    return hit_count >= required_hits, hit_count


def get_bullet_lines(answer: str) -> list[str]:
    return [
        line.strip()
        for line in str(answer or "").splitlines()
        if line.strip().startswith("- ")
    ]


def has_duplicate_bullets(bullet_lines: list[str]) -> bool:
    normalized = [
        normalize_text(line.removeprefix("- ").rstrip(".!?"))
        for line in bullet_lines
    ]

    return len(normalized) != len(set(normalized))


def evaluate_answer_format(
    answer: str,
    response_type: str,
) -> tuple[bool, int, str]:
    if response_type != "rag_answer":
        return True, 0, ""

    bullet_lines = get_bullet_lines(answer)
    problems: list[str] = []

    if not 1 <= len(bullet_lines) <= 3:
        problems.append("bullet_count_not_between_1_and_3")

    non_empty_lines = [
        line.strip()
        for line in str(answer or "").splitlines()
        if line.strip()
    ]

    if len(non_empty_lines) != len(bullet_lines):
        problems.append("contains_non_bullet_text")

    if has_duplicate_bullets(bullet_lines):
        problems.append("duplicate_bullets")

    normalized_answer = normalize_text(answer)

    forbidden_patterns = [
        "kaynak dokümana göre",
        "dokümanda belirtilmiştir",
        "meeting room support",
        "source text",
        "metadata",
        "document_id",
        "chunk",
        "kullanıcı şüpheli",
        "kullanıcının ",
    ]

    found_forbidden = [
        pattern
        for pattern in forbidden_patterns
        if pattern in normalized_answer
    ]

    if found_forbidden:
        problems.append(
            "forbidden_patterns:" + "|".join(found_forbidden)
        )

    return len(problems) == 0, len(bullet_lines), "|".join(problems)


def calculate_case_pass(
    response_type_match: bool,
    source_match: bool,
    section_match: bool,
    keyword_match: bool,
    answer_format_match: bool,
) -> bool:
    return all(
        [
            response_type_match,
            source_match,
            section_match,
            keyword_match,
            answer_format_match,
        ]
    )


def write_summary(results: list[dict[str, Any]], output_path: Path) -> Path:
    successful_results = [
        result for result in results
        if result["status"] == "success"
    ]

    response_times = [
        float(result["response_time_seconds"])
        for result in successful_results
        if result["response_time_seconds"] != ""
    ]

    metric_columns = [
        "case_pass",
        "source_match",
        "section_match",
        "keyword_match",
        "response_type_match",
        "answer_format_match",
    ]

    summary = {
        "total_run_count": len(results),
        "successful_request_count": len(successful_results),
        "request_error_count": len(results) - len(successful_results),
    }

    for column in metric_columns:
        summary[f"{column}_count"] = sum(
            1
            for result in successful_results
            if result[column] == "True"
        )

    summary.update(
        {
            "average_response_time_seconds": (
                round(sum(response_times) / len(response_times), 3)
                if response_times
                else ""
            ),
            "min_response_time_seconds": (
                round(min(response_times), 3)
                if response_times
                else ""
            ),
            "max_response_time_seconds": (
                round(max(response_times), 3)
                if response_times
                else ""
            ),
        }
    )

    summary_path = output_path.with_name(
        output_path.stem + "-summary.csv"
    )

    with summary_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(summary.keys()),
        )
        writer.writeheader()
        writer.writerow(summary)

    return summary_path


def evaluate(
    model_label: str,
    repeat_count: int,
    test_cases_path: Path,
    api_base_url: str,
    email: str,
    password: str,
    min_keyword_hits: int,
) -> tuple[Path, Path]:
    test_cases = load_test_cases(test_cases_path)

    with httpx.Client() as client:
        token = login(
            client=client,
            api_base_url=api_base_url,
            email=email,
            password=password,
        )

        results: list[dict[str, Any]] = []

        for test_case in test_cases:
            case_id = str(test_case["id"])
            question = str(test_case["question"])
            expected_response_type = str(
                test_case["expected_response_type"]
            )
            expected_document_ids = list(
                test_case["expected_document_ids"]
            )
            accepted_sections = list(
                test_case["accepted_sections"]
            )
            required_keywords = list(
                test_case["required_keywords"]
            )

            for run_index in range(1, repeat_count + 1):
                print(
                    f"Testing [{model_label}] "
                    f"{case_id} run {run_index}: {question}"
                )

                try:
                    response_data, elapsed_seconds = ask_question(
                        client=client,
                        api_base_url=api_base_url,
                        token=token,
                        question=question,
                    )

                    answer = str(response_data.get("answer") or "")
                    raw_sources = response_data.get("sources") or []
                    sources = (
                        raw_sources
                        if isinstance(raw_sources, list)
                        else []
                    )

                    response_type = str(
                        response_data.get("response_type") or ""
                    )

                    response_type_match = (
                        response_type == expected_response_type
                    )

                    actual_document_ids = get_source_document_ids(
                        sources
                    )
                    actual_sections = get_source_sections(sources)
                    source_scores = get_source_scores(sources)

                    source_match = evaluate_source_match(
                        expected_document_ids=expected_document_ids,
                        actual_document_ids=actual_document_ids,
                    )

                    section_match = evaluate_section_match(
                        accepted_sections=accepted_sections,
                        actual_sections=actual_sections,
                    )

                    keyword_match, keyword_hit_count = (
                        evaluate_keyword_match(
                            answer=answer,
                            keywords=required_keywords,
                            min_keyword_hits=min_keyword_hits,
                        )
                    )

                    (
                        answer_format_match,
                        bullet_count,
                        answer_format_problems,
                    ) = evaluate_answer_format(
                        answer=answer,
                        response_type=response_type,
                    )

                    case_pass = calculate_case_pass(
                        response_type_match=response_type_match,
                        source_match=source_match,
                        section_match=section_match,
                        keyword_match=keyword_match,
                        answer_format_match=answer_format_match,
                    )

                    results.append(
                        {
                            "model_label": model_label,
                            "case_id": case_id,
                            "run": run_index,
                            "question": question,
                            "answer": answer,
                            "response_type": response_type,
                            "expected_response_type": expected_response_type,
                            "response_type_match": str(
                                response_type_match
                            ),
                            "actual_document_ids": " | ".join(
                                actual_document_ids
                            ),
                            "expected_document_ids": " | ".join(
                                expected_document_ids
                            ),
                            "source_match": str(source_match),
                            "actual_sections": " | ".join(
                                actual_sections
                            ),
                            "accepted_sections": " | ".join(
                                accepted_sections
                            ),
                            "section_match": str(section_match),
                            "source_scores": " | ".join(source_scores),
                            "keyword_match": str(keyword_match),
                            "keyword_hit_count": keyword_hit_count,
                            "required_keywords": " | ".join(
                                required_keywords
                            ),
                            "answer_format_match": str(
                                answer_format_match
                            ),
                            "bullet_count": bullet_count,
                            "answer_format_problems": (
                                answer_format_problems
                            ),
                            "case_pass": str(case_pass),
                            "response_time_seconds": round(
                                elapsed_seconds,
                                3,
                            ),
                            "source_count": len(sources),
                            "answer_length": len(answer),
                            "status": "success",
                            "error": "",
                            "manual_quality_score": "",
                            "manual_notes": "",
                        }
                    )

                    if not case_pass:
                        print(
                            "  FAIL:",
                            {
                                "response_type": response_type_match,
                                "source": source_match,
                                "section": section_match,
                                "keyword": keyword_match,
                                "format": answer_format_match,
                            },
                        )

                except Exception as error:
                    results.append(
                        {
                            "model_label": model_label,
                            "case_id": case_id,
                            "run": run_index,
                            "question": question,
                            "answer": "",
                            "response_type": "",
                            "expected_response_type": expected_response_type,
                            "response_type_match": "False",
                            "actual_document_ids": "",
                            "expected_document_ids": " | ".join(
                                expected_document_ids
                            ),
                            "source_match": "False",
                            "actual_sections": "",
                            "accepted_sections": " | ".join(
                                accepted_sections
                            ),
                            "section_match": "False",
                            "source_scores": "",
                            "keyword_match": "False",
                            "keyword_hit_count": 0,
                            "required_keywords": " | ".join(
                                required_keywords
                            ),
                            "answer_format_match": "False",
                            "bullet_count": 0,
                            "answer_format_problems": "",
                            "case_pass": "False",
                            "response_time_seconds": "",
                            "source_count": "",
                            "answer_length": 0,
                            "status": "error",
                            "error": str(error),
                            "manual_quality_score": "",
                            "manual_notes": "",
                        }
                    )

                    print(f"  ERROR: {error}")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "docs" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model_label = (
        model_label.replace(":", "-").replace("/", "-")
    )

    output_path = output_dir / (
        f"rag-evaluation-{safe_model_label}-{timestamp}.csv"
    )

    fieldnames = [
        "model_label",
        "case_id",
        "run",
        "question",
        "answer",
        "response_type",
        "expected_response_type",
        "response_type_match",
        "actual_document_ids",
        "expected_document_ids",
        "source_match",
        "actual_sections",
        "accepted_sections",
        "section_match",
        "source_scores",
        "keyword_match",
        "keyword_hit_count",
        "required_keywords",
        "answer_format_match",
        "bullet_count",
        "answer_format_problems",
        "case_pass",
        "response_time_seconds",
        "source_count",
        "answer_length",
        "status",
        "error",
        "manual_quality_score",
        "manual_notes",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    summary_path = write_summary(results, output_path)

    return output_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the İZELTAŞ local RAG assistant."
    )

    parser.add_argument(
        "--model",
        dest="model_label",
        required=True,
        help=(
            "Label written to result files. "
            "This does not change the n8n/Ollama model."
        ),
    )
    parser.add_argument(
        "--cases",
        type=Path,
        required=True,
        help="Path to evaluation-cases.json.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--min-keyword-hits",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_LOGIN_EMAIL,
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_LOGIN_PASSWORD,
    )

    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1.")

    output_path, summary_path = evaluate(
        model_label=args.model_label,
        repeat_count=args.repeat,
        test_cases_path=args.cases,
        api_base_url=args.api_base_url.rstrip("/"),
        email=args.email,
        password=args.password,
        min_keyword_hits=args.min_keyword_hits,
    )

    print("\nEvaluation completed.")
    print(f"Result file: {output_path}")
    print(f"Summary file: {summary_path}")


if __name__ == "__main__":
    main()
