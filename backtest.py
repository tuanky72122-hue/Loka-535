import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 300
TEST_DRAWS = 200
REPETITIONS = 100

WINDOWS = [20, 50, 100, 150, 200, 300]


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


def weighted_sample(frequency, window, count=5):
    expected = window * 5 / 35

    weights = {}

    for number in range(1, 36):
        ratio = frequency[number] / expected
        weights[number] = max(ratio, 0.01)

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


def evaluate_window(history, window):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    results = []

    for index in range(start, len(history)):
        training = history[:index]
        actual = history[index]["numbers"]

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

        results.append(matches)

    return results


def evaluate_random(history):
    start = max(
        MIN_TRAINING_DRAWS,
        len(history) - TEST_DRAWS
    )

    results = []

    for index in range(start, len(history)):
        actual = history[index]["numbers"]

        prediction = random_sample()

        matches = count_matches(
            prediction,
            actual
        )

        results.append(matches)

    return results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def main():
    history = load_history()

    if len(history) <= MIN_TRAINING_DRAWS:
        print("ERROR: Không đủ dữ liệu để Backtest.")
        return

    print("=" * 50)
    print("LOKA-535 BACKTEST V4")
    print("=" * 50)
    print(f"Tổng dữ liệu: {len(history)} kỳ")
    print(f"Kỳ kiểm thử: {TEST_DRAWS}")
    print()
    print(
        "Kiểm tra Recent Frequency với "
        "nhiều cửa sổ lịch sử."
    )

    random_results = []

    for _ in range(REPETITIONS):
        random_results.extend(
            evaluate_random(history)
        )

    random_average = average(random_results)

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
    print("RECENT FREQUENCY WINDOWS")
    print("=" * 50)

    results = {}

    for window in WINDOWS:
        all_results = []

        for _ in range(REPETITIONS):
            all_results.extend(
                evaluate_window(
                    history,
                    window
                )
            )

        model_average = average(all_results)
        difference = model_average - random_average

        results[window] = model_average

        print(
            f"{window:3d} kỳ: "
            f"{model_average:.4f} "
            f"({difference:+.4f})"
        )

    print()
    print("=" * 50)
    print("KẾT QUẢ")
    print("=" * 50)

    best_window = max(
        results,
        key=results.get
    )

    print(
        f"Cửa sổ có kết quả cao nhất: "
        f"{best_window} kỳ"
    )

    print(
        f"Trung bình: "
        f"{results[best_window]:.4f}"
    )

    print(
        f"So với Random: "
        f"{results[best_window] - random_average:+.4f}"
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