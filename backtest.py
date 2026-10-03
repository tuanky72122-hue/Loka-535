import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 100
TEST_DRAWS = 200
REPETITIONS = 100
RECENT_WINDOW = 100


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


def calculate_recent_frequency(history, window=RECENT_WINDOW):
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


def build_weights(history, model):
    frequency = calculate_frequency(history)
    recent = calculate_recent_frequency(history)
    gap = calculate_gap(history)

    total_draws = len(history)
    expected = total_draws * 5 / 35

    recent_window = min(total_draws, RECENT_WINDOW)
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

        if model == "frequency":
            weight = long_term

        elif model == "recent":
            weight = recent_ratio

        elif model == "gap":
            weight = gap_factor

        elif model == "combined":
            weight = (
                0.50 * long_term
                + 0.30 * recent_ratio
                + 0.20 * gap_factor
            )

        else:
            weight = 1

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


def evaluate_model(history, model):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    results = []

    for index in range(start, len(history)):
        training = history[:index]
        actual = history[index]["numbers"]

        if model == "random":
            prediction = random_sample()
        else:
            weights = build_weights(training, model)
            prediction = weighted_sample(weights)

        matches = count_matches(prediction, actual)
        results.append(matches)

    return results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def summarize(results):
    return {
        "average": average(results),
        "zero": results.count(0),
        "one": results.count(1),
        "two": results.count(2),
        "three_or_more": sum(
            1 for value in results if value >= 3
        ),
    }


def run_repetitions(history, model):
    averages = []

    total_results = []

    for _ in range(REPETITIONS):
        results = evaluate_model(history, model)

        averages.append(average(results))
        total_results.extend(results)

    return averages, total_results


def print_model_result(name, averages, results):
    summary = summarize(results)

    print()
    print("=" * 50)
    print(name)
    print("=" * 50)

    print(
        f"Trung bình số khớp: "
        f"{average(averages):.4f}"
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
        print("ERROR: Không đủ dữ liệu để Backtest.")
        return

    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    test_draws = len(history) - start

    models = [
        ("random", "PURE RANDOM"),
        ("frequency", "FREQUENCY DÀI HẠN"),
        ("recent", "RECENT FREQUENCY"),
        ("gap", "GAP"),
        ("combined", "COMBINED 50/30/20"),
    ]

    print("=" * 50)
    print("LOKA-535 BACKTEST V3")
    print("=" * 50)
    print(f"Tổng dữ liệu: {len(history)} kỳ")
    print(f"Kỳ kiểm thử: {test_draws}")
    print(f"Số lượt kiểm định: {REPETITIONS}")
    print()
    print(
        "Mỗi mô hình được kiểm tra độc lập "
        "trên cùng 200 kỳ lịch sử."
    )

    model_results = {}

    for model, name in models:
        averages, results = run_repetitions(
            history,
            model
        )

        model_results[model] = average(averages)

        print_model_result(
            name,
            averages,
            results
        )

    random_average = model_results["random"]

    print()
    print("=" * 50)
    print("SO SÁNH VỚI PURE RANDOM")
    print("=" * 50)

    for model, name in models:
        if model == "random":
            continue

        difference = (
            model_results[model]
            - random_average
        )

        print(
            f"{name}: "
            f"{difference:+.4f}"
        )

    print()
    print("=" * 50)
    print("KẾT LUẬN KIỂM ĐỊNH")
    print("=" * 50)
    print(
        "Kết quả chỉ phản ánh dữ liệu lịch sử "
        "và không chứng minh khả năng dự đoán kỳ tiếp theo."
    )


if __name__ == "__main__":
    main()