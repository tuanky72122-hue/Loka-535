import json
import secrets
from pathlib import Path


HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 100
TEST_DRAWS = 200
RANDOM_TRIALS = 5


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(
        data,
        key=lambda record: record["id"],
    )


def calculate_frequency(history):
    frequency = {number: 0 for number in range(1, 36)}

    for record in history:
        for number in record["numbers"]:
            frequency[number] += 1

    return frequency


def calculate_recent_frequency(history, window=100):
    recent = history[-window:]
    frequency = {number: 0 for number in range(1, 36)}

    for record in recent:
        for number in record["numbers"]:
            frequency[number] += 1

    return frequency


def calculate_gap(history):
    last_seen = {}

    for index, record in enumerate(history):
        for number in record["numbers"]:
            last_seen[number] = index

    latest_index = len(history) - 1

    return {
        number: (
            latest_index - last_seen[number]
            if number in last_seen
            else len(history)
        )
        for number in range(1, 36)
    }


def build_weights(history):
    frequency = calculate_frequency(history)
    recent = calculate_recent_frequency(history)
    gap = calculate_gap(history)

    total_draws = len(history)
    expected = total_draws * 5 / 35

    weights = {}

    for number in range(1, 36):
        long_term = frequency[number] / expected

        recent_expected = min(
            len(history),
            100,
        ) * 5 / 35

        recent_ratio = (
            recent[number] / recent_expected
            if recent_expected > 0
            else 1
        )

        gap_factor = 1 + min(gap[number], 20) / 100

        weight = (
            0.50 * long_term
            + 0.30 * recent_ratio
            + 0.20 * gap_factor
        )

        weights[number] = max(weight, 0.01)

    return weights


def weighted_sample(weights, count=5):
    available = dict(weights)
    selected = []

    for _ in range(count):
        total_weight = sum(available.values())

        target = secrets.randbelow(
            10_000_000
        ) / 10_000_000 * total_weight

        cumulative = 0

        for number, weight in available.items():
            cumulative += weight

            if target <= cumulative:
                selected.append(number)
                del available[number]
                break

    return sorted(selected)


def random_sample():
    numbers = list(range(1, 36))
    selected = []

    while len(selected) < 5:
        index = secrets.randbelow(len(numbers))
        selected.append(numbers.pop(index))

    return sorted(selected)


def count_matches(prediction, actual):
    return len(
        set(prediction) & set(actual)
    )


def evaluate_model(history):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS,
    )

    weighted_results = []
    random_results = []

    for index in range(start, len(history)):
        training = history[:index]
        actual = history[index]["numbers"]

        weights = build_weights(training)

        for _ in range(RANDOM_TRIALS):
            prediction = weighted_sample(weights)
            matches = count_matches(
                prediction,
                actual,
            )
            weighted_results.append(matches)

            random_prediction = random_sample()
            random_matches = count_matches(
                random_prediction,
                actual,
            )
            random_results.append(
                random_matches
            )

    return weighted_results, random_results


def summarize(results):
    if not results:
        return {
            "trials": 0,
            "average": 0,
            "zero": 0,
            "one": 0,
            "two": 0,
            "three_or_more": 0,
        }

    return {
        "trials": len(results),
        "average": sum(results) / len(results),
        "zero": results.count(0),
        "one": results.count(1),
        "two": results.count(2),
        "three_or_more": sum(
            1 for value in results
            if value >= 3
        ),
    }


def print_summary(title, summary):
    print()
    print("=" * 50)
    print(title)
    print("=" * 50)

    print(f"Số lần thử: {summary['trials']}")
    print(
        f"Số khớp trung bình: "
        f"{summary['average']:.4f}"
    )
    print(
        f"0 số khớp: "
        f"{summary['zero']}"
    )
    print(
        f"1 số khớp: "
        f"{summary['one']}"
    )
    print(
        f"2 số khớp: "
        f"{summary['two']}"
    )
    print(
        f">=3 số khớp: "
        f"{summary['three_or_more']}"
    )


def main():
    history = load_history()

    if len(history) <= MIN_TRAINING_DRAWS:
        print(
            "ERROR: Không đủ dữ liệu "
            "để Backtest."
        )
        return

    print("=" * 50)
    print("LOKA-535 BACKTEST")
    print("=" * 50)

    print(
        f"Tổng dữ liệu: "
        f"{len(history)} kỳ"
    )

    print(
        f"Kỳ tối thiểu trước khi test: "
        f"{MIN_TRAINING_DRAWS}"
    )

    print(
        f"Số kỳ kiểm thử tối đa: "
        f"{TEST_DRAWS}"
    )

    print(
        f"Số lần random mỗi kỳ: "
        f"{RANDOM_TRIALS}"
    )

    weighted, random_results = evaluate_model(
        history
    )

    weighted_summary = summarize(weighted)
    random_summary = summarize(
        random_results
    )

    print_summary(
        "WEIGHTED RANDOM",
        weighted_summary,
    )

    print_summary(
        "PURE RANDOM BASELINE",
        random_summary,
    )

    difference = (
        weighted_summary["average"]
        - random_summary["average"]
    )

    print()
    print("=" * 50)
    print("CHÊNH LỆCH TRUNG BÌNH")
    print("=" * 50)

    print(
        f"Weighted - Random: "
        f"{difference:+.4f}"
    )

    print()
    print(
        "LƯU Ý: Kết quả Backtest không "
        "chứng minh khả năng dự đoán kỳ tiếp theo."
    )


if __name__ == "__main__":
    main()