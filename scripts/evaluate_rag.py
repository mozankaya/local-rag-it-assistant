import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import httpx


API_BASE_URL = "http://127.0.0.1:8000"

LOGIN_EMAIL = "admin@izeltas.local"
LOGIN_PASSWORD = "Admin123!"


TEST_CASES = [
    {
        "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
        "expected_document_id": "vpn-remote-access",
        "expected_keywords": ["internet", "vpn", "şifre"],
        "case_type": "rag",
    },
    {
        "question": "Şifremi unuttum, nasıl sıfırlayabilirim?",
        "expected_document_id": "password-and-account",
        "expected_keywords": ["şifre", "sıfırla"],
        "case_type": "rag",
    },
    {
        "question": "Outlook mail göndermiyor, ne yapmalıyım?",
        "expected_document_id": "email-outlook",
        "expected_keywords": ["outlook", "internet", "adres"],
        "case_type": "rag",
    },
    {
        "question": "Yazıcıdan çıktı alamıyorum, ne yapmalıyım?",
        "expected_document_id": "printer-support",
        "expected_keywords": ["yazıcı", "kağıt", "bağlantı"],
        "case_type": "rag",
    },
    {
        "question": "İnternet bağlantım yok, ne yapmalıyım?",
        "expected_document_id": "network-connection",
        "expected_keywords": ["internet", "ağ", "bağlantı"],
        "case_type": "rag",
    },
    {
        "question": "Donanım desteği talebi nasıl oluşturabilirim?",
        "expected_document_id": "hardware-support",
        "expected_keywords": ["donanım", "talep", "destek"],
        "case_type": "rag",
    },
    {
        "question": "Ekipman talebi nasıl oluşturabilirim?",
        "expected_document_id": "equipment-request",
        "expected_keywords": ["ekipman", "talep", "onay"],
        "case_type": "rag",
    },
    {
        "question": "Ortak klasöre erişemiyorum, ne yapmalıyım?",
        "expected_document_id": "shared-folder-access",
        "expected_keywords": ["ortak", "klasör", "vpn", "yetki"],
        "case_type": "rag",
    },
    {
        "question": "Ortak klasör için yetki talebi nasıl oluşturulur?",
        "expected_document_id": "shared-folder-access",
        "expected_keywords": ["klasör", "yetki", "yönetici", "onay"],
        "case_type": "rag",
    },
    {
        "question": "Yeni bir yazılım kurulumu için nasıl talep oluşturabilirim?",
        "expected_document_id": "software-access",
        "expected_keywords": ["yazılım", "kurulum", "lisans", "talep"],
        "case_type": "rag",
    },
    {
        "question": "Kurumsal uygulama yetkisi almak için ne yapmalıyım?",
        "expected_document_id": "software-access",
        "expected_keywords": ["uygulama", "yetki", "görev", "erişim"],
        "case_type": "rag",
    },
    {
        "question": "Çok faktörlü doğrulama bildirimi gelmiyor, ne yapmalıyım?",
        "expected_document_id": "security-and-mfa",
        "expected_keywords": ["doğrulama", "bildirim", "telefon", "kod"],
        "case_type": "rag",
    },
    {
        "question": "Şüpheli bir e-posta aldım, ne yapmalıyım?",
        "expected_document_id": "security-and-mfa",
        "expected_keywords": ["şüpheli", "e-posta", "bağlantı", "ek"],
        "case_type": "rag",
    },
    {
        "question": "Toplantı odasındaki ekran çalışmıyor, ne yapmalıyım?",
        "expected_document_id": "meeting-room-support",
        "expected_keywords": ["toplantı", "ekran", "giriş", "hdmi"],
        "case_type": "rag",
    },
    {
        "question": "Kamera veya mikrofon çalışmıyor, ne yapmalıyım?",
        "expected_document_id": "meeting-room-support",
        "expected_keywords": ["kamera", "mikrofon", "cihaz", "izin"],
        "case_type": "rag",
    },

    # Kaynak bulunmaması beklenen ama IT'ye yakın soru
    {
        "question": "SAP sevkiyat ekranı çalışmıyor, ne yapmalıyım?",
        "expected_document_id": "",
        "expected_keywords": ["kaynak", "bilgi", "IT"],
        "case_type": "no_relevant_source",
    },

    # Kapsam dışı soru
    {
        "question": "Bana yemek tarifi verir misin?",
        "expected_document_id": "",
        "expected_keywords": ["yardımcı olamam", "IT"],
        "case_type": "out_of_scope",
    },

    # Static cevap
    {
        "question": "Merhaba",
        "expected_document_id": "",
        "expected_keywords": ["merhaba", "yardımcı"],
        "case_type": "static",
    },
]


def login() -> str:
    response = httpx.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    return data["access_token"]


def ask_question(token: str, question: str) -> tuple[dict, float]:
    start_time = time.perf_counter()

    response = httpx.post(
        f"{API_BASE_URL}/chat",
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

    return response.json(), elapsed_seconds


def contains_expected_keywords(answer: str, keywords: list[str]) -> bool:
    normalized_answer = answer.lower()

    return any(keyword.lower() in normalized_answer for keyword in keywords)


def get_first_source_document_id(sources: list[dict]) -> str:
    if not sources:
        return ""

    first_source = sources[0]
    return str(first_source.get("document_id") or "")


def evaluate_source_match(
    expected_document_id: str,
    first_source_document_id: str,
) -> bool:
    if expected_document_id:
        return first_source_document_id == expected_document_id

    return first_source_document_id == ""


def write_summary(results: list[dict], output_path: Path) -> Path:
    successful_results = [
        result for result in results if result["status"] == "success"
    ]

    response_times = [
        float(result["response_time_seconds"])
        for result in successful_results
        if result["response_time_seconds"] != ""
    ]

    total_count = len(results)
    success_count = len(successful_results)
    error_count = total_count - success_count

    source_match_count = sum(
        1 for result in successful_results if result["source_match"] == "True"
    )
    keyword_match_count = sum(
        1 for result in successful_results if result["keyword_match"] == "True"
    )

    average_response_time = (
        round(sum(response_times) / len(response_times), 3)
        if response_times
        else ""
    )

    max_response_time = round(max(response_times), 3) if response_times else ""
    min_response_time = round(min(response_times), 3) if response_times else ""

    summary_path = output_path.with_name(output_path.stem + "-summary.csv")

    with summary_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "total_count",
                "success_count",
                "error_count",
                "source_match_count",
                "keyword_match_count",
                "average_response_time_seconds",
                "min_response_time_seconds",
                "max_response_time_seconds",
            ],
        )

        writer.writeheader()
        writer.writerow(
            {
                "total_count": total_count,
                "success_count": success_count,
                "error_count": error_count,
                "source_match_count": source_match_count,
                "keyword_match_count": keyword_match_count,
                "average_response_time_seconds": average_response_time,
                "min_response_time_seconds": min_response_time,
                "max_response_time_seconds": max_response_time,
            }
        )

    return summary_path


def evaluate(model_name: str, repeat_count: int) -> tuple[Path, Path]:
    token = login()

    results = []

    for test_case in TEST_CASES:
        question = test_case["question"]
        expected_document_id = test_case["expected_document_id"]
        expected_keywords = test_case["expected_keywords"]
        case_type = test_case["case_type"]

        for run_index in range(1, repeat_count + 1):
            print(f"Testing [{model_name}] run {run_index}: {question}")

            try:
                response_data, elapsed_seconds = ask_question(token, question)

                answer = str(response_data.get("answer") or "")
                sources = response_data.get("sources") or []

                first_source_document_id = get_first_source_document_id(sources)

                source_match = evaluate_source_match(
                    expected_document_id=expected_document_id,
                    first_source_document_id=first_source_document_id,
                )

                keyword_match = contains_expected_keywords(
                    answer=answer,
                    keywords=expected_keywords,
                )

                results.append(
                    {
                        "model": model_name,
                        "run": run_index,
                        "case_type": case_type,
                        "question": question,
                        "answer": answer,
                        "response_time_seconds": round(elapsed_seconds, 3),
                        "source_count": len(sources),
                        "first_source_document_id": first_source_document_id,
                        "expected_document_id": expected_document_id,
                        "source_match": str(source_match),
                        "keyword_match": str(keyword_match),
                        "answer_length": len(answer),
                        "status": "success",
                        "error": "",
                        "manual_quality_score": "",
                        "manual_notes": "",
                    }
                )

            except Exception as error:
                results.append(
                    {
                        "model": model_name,
                        "run": run_index,
                        "case_type": case_type,
                        "question": question,
                        "answer": "",
                        "response_time_seconds": "",
                        "source_count": "",
                        "first_source_document_id": "",
                        "expected_document_id": expected_document_id,
                        "source_match": "False",
                        "keyword_match": "False",
                        "answer_length": 0,
                        "status": "error",
                        "error": str(error),
                        "manual_quality_score": "",
                        "manual_notes": "",
                    }
                )

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    output_dir = PROJECT_ROOT / "docs" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model_name = model_name.replace(":", "-").replace("/", "-")
    output_path = output_dir / f"rag-evaluation-{safe_model_name}-{timestamp}.csv"

    fieldnames = [
        "model",
        "run",
        "case_type",
        "question",
        "answer",
        "response_time_seconds",
        "source_count",
        "first_source_document_id",
        "expected_document_id",
        "source_match",
        "keyword_match",
        "answer_length",
        "status",
        "error",
        "manual_quality_score",
        "manual_notes",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    summary_path = write_summary(results, output_path)

    return output_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--repeat", type=int, default=1)

    args = parser.parse_args()

    output_path, summary_path = evaluate(
        model_name=args.model,
        repeat_count=args.repeat,
    )

    print("\nEvaluation completed.")
    print(f"Result file: {output_path}")
    print(f"Summary file: {summary_path}")


if __name__ == "__main__":
    main()