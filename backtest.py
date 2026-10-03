import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 100
TEST_DRAWS = 200
REPETITIONS = 100

WINDOWS = [30, 40, 50, 60, 75, 100]


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(data, key=lambda record: record["id"])


def calculate_recent_frequency(history, window):
    recent = history[-window:]

    frequency = {number: 0 for number in range(1, 36)}

    for record in recent:
        for number in record["numbers"]:
            frequency[number] += 1

    return frequency


def weighted_sample(frequency, window):
    expected = window * 5 / 35

    weights = {}

    for number in range(1, 36):
        ratio = frequency[number] / expected
        weights[number] = max(ratio, 0.01)

    available = dict(weights)
    selected = []

    for _ in range(5):
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


def evaluate_once(history, random_predictions):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    results = {
        window: []
        for window in WINDOWS
    }

    random_results = []

    for position, index in enumerate(
        range(start, len(history))
    ):
        training = history[:index]
        actual = history[index]["numbers"]

        random_prediction = random_predictions[position]

        random_matches = count_matches(
            random_prediction,
            actual
        )

        random_results.append(random_matches)

        for window in WINDOWS:
            if len(training) < window:
                continue

            frequency = calculate_recent_frequency(
                training,
                window
            )

            prediction = weighted_sample(
                frequency,
                window
            )

            matches = count_matches(
                prediction,
                actual
            )

            results[window].append(matches)

    return results, random_results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


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

    totals = {
        window: []
        for window in WINDOWS
    }

    random_totals = []

    print("=" * 50)
    print("LOKA-535 BACKTEST V5")
    print("=" * 50)
    print(f"Tổng dữ liệu: {len(history)} kỳ")
    print(f"Kỳ kiểm thử: {test_draws}")
    print(f"Số lượt kiểm định: {REPETITIONS}")
    print()
    print(
        "Các cửa sổ được so sánh: "
        "30, 40, 50, 60, 75, 100 kỳ."
    )
    print(
        "Mỗi lượt sử dụng cùng một Random baseline "
        "cho tất cả cửa sổ."
    )

    for _ in range(REPETITIONS):
        random_predictions = []

        for _ in range(test_draws):
            random_predictions.append(
                random_sample()
            )

        results, random_results = evaluate_once(
            history,
            random_predictions
        )

        for window in WINDOWS:
            totals[window].extend(
                results[window]
            )

        random_totals.extend(
            random_results
        )

    random_average = average(random_totals)

    print()
    print("=" * 50)
    print("PURE RANDOM BASELINE")
    print("=" * 50)
    print(
        f"Trung bình số khớp: "
        f"{random_average:.4f}"
    )

    print()
    print("=" * 50)
    print("RECENT FREQUENCY")
    print("=" * 50)

    averages = {}

    for window in WINDOWS:
        model_average = average(
            totals[window]
        )

        difference = (
            model_average
            - random_average
        )

        averages[window] = model_average

        print(
            f"{window:3d} kỳ: "
            f"{model_average:.4f} "
            f"({difference:+.4f})"
        )

    best_window = max(
        averages,
        key=averages.get
    )

    print()
    print("=" * 50)
    print("KẾT QUẢ")
    print("=" * 50)

    print(
        f"Cửa sổ cao nhất: "
        f"{best_window} kỳ"
    )

    print(
        f"Trung bình: "
        f"{averages[best_window]:.4f}"
    )

    print(
        f"So với Random: "
        f"{averages[best_window] - random_average:+.4f}"
    )

    print()
    print("=" * 50)
    print("LƯU Ý")
    print("=" * 50)
    print(
        "Kết quả Backtest chỉ phản ánh dữ liệu lịch sử "
        "và không chứng minh khả năng dự đoán kỳ tiếp theo."
    )


if __name__ == "__main__":
    main()