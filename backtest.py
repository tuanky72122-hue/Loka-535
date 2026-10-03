import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 100
TEST_DRAWS = 200
REPETITIONS = 100


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(data, key=lambda record: record["id"])


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

    recent_window = min(total_draws, 100)
    recent_expected = recent_window * 5 / 35

    weights = {}

    for number in range(1, 36):
        long_term = frequency[number] / expected

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

        target = (
            secrets.randbelow(10_000_000)
            / 10_000_000
            * total_weight
        )

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
    return len(set(prediction) & set(actual))


def evaluate_once(history):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    weighted_results = []
    random_results = []

    for index in range(start, len(history)):
        training = history[:index]
        actual = history[index]["numbers"]

        weights = build_weights(training)

        weighted_prediction = weighted_sample(weights)
        random_prediction = random_sample()

        weighted_matches = count_matches(
            weighted_prediction,
            actual
        )

        random_matches = count_matches(
            random_prediction,
            actual
        )

        weighted_results.append(weighted_matches)
        random_results.append(random_matches)

    return weighted_results, random_results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def summarize_results(results):
    return {
        "average": average(results),
        "zero": results.count(0),
        "one": results.count(1),
        "two": results.count(2),
        "three_or_more": sum(
            1 for value in results if value >= 3
        ),
    }


def main():
    history = load_history()

    if len(history) <= MIN_TRAINING_DRAWS:
        print("ERROR: Không đủ dữ liệu để Backtest.")
        return

    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    actual_test_draws = len(history) - start

    print("=" * 50)
    print("LOKA-535 BACKTEST V2")
    print("=" * 50)
    print(f"Tổng dữ liệu: {len(history)} kỳ")
    print(f"Kỳ kiểm thử: {actual_test_draws}")
    print(f"Số lượt kiểm định: {REPETITIONS}")
    print()
    print(
        "Mỗi lượt: 1 Weighted Random + 1 Pure Random "
        "trên cùng các kỳ thực tế."
    )

    differences = []
    weighted_averages = []
    random_averages = []

    weighted_total = []
    random_total = []

    for _ in range(REPETITIONS):
        weighted, random_results = evaluate_once(history)

        weighted_avg = average(weighted)
        random_avg = average(random_results)
        difference = weighted_avg - random_avg

        weighted_averages.append(weighted_avg)
        random_averages.append(random_avg)
        differences.append(difference)

        weighted_total.extend(weighted)
        random_total.extend(random_results)

    weighted_summary = summarize_results(weighted_total)
    random_summary = summarize_results(random_total)

    positive_runs = sum(
        1 for difference in differences
        if difference > 0
    )

    negative_runs = sum(
        1 for difference in differences
        if difference < 0
    )

    equal_runs = sum(
        1 for difference in differences
        if difference == 0
    )

    overall_difference = (
        average(weighted_averages)
        - average(random_averages)
    )

    print()
    print("=" * 50)
    print("WEIGHTED RANDOM")
    print("=" * 50)
    print(
        f"Số lần dự đoán: "
        f"{len(weighted_total)}"
    )
    print(
        f"Số khớp trung bình: "
        f"{weighted_summary['average']:.4f}"
    )
    print(f"0 số khớp: {weighted_summary['zero']}")
    print(f"1 số khớp: {weighted_summary['one']}")
    print(f"2 số khớp: {weighted_summary['two']}")
    print(
        f">=3 số khớp: "
        f"{weighted_summary['three_or_more']}"
    )

    print()
    print("=" * 50)
    print("PURE RANDOM BASELINE")
    print("=" * 50)
    print(
        f"Số lần dự đoán: "
        f"{len(random_total)}"
    )
    print(
        f"Số khớp trung bình: "
        f"{random_summary['average']:.4f}"
    )
    print(f"0 số khớp: {random_summary['zero']}")
    print(f"1 số khớp: {random_summary['one']}")
    print(f"2 số khớp: {random_summary['two']}")
    print(
        f">=3 số khớp: "
        f"{random_summary['three_or_more']}"
    )

    print()
    print("=" * 50)
    print("KẾT QUẢ 100 LƯỢT KIỂM ĐỊNH")
    print("=" * 50)

    print(
        f"Weighted thắng: "
        f"{positive_runs}/{REPETITIONS}"
    )

    print(
        f"Random thắng: "
        f"{negative_runs}/{REPETITIONS}"
    )

    print(
        f"Hòa: "
        f"{equal_runs}/{REPETITIONS}"
    )

    print()
    print(
        f"Weighted trung bình: "
        f"{average(weighted_averages):.4f}"
    )

    print(
        f"Random trung bình: "
        f"{average(random_averages):.4f}"
    )

    print(
        f"Weighted - Random: "
        f"{overall_difference:+.4f}"
    )

    print()
    print("=" * 50)
    print("LƯU Ý")
    print("=" * 50)
    print(
        "Backtest chỉ kiểm tra dữ liệu lịch sử. "
        "Nó không chứng minh khả năng dự đoán kỳ tiếp theo."
    )


if __name__ == "__main__":
    main()