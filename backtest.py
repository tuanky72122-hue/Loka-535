import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 300
BLOCK_SIZE = 200

WINDOWS = [50, 100]


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


def evaluate_block(history, start, end, random_predictions):
    results = {
        window: []
        for window in WINDOWS
    }

    random_results = []

    for position, index in enumerate(range(start, end)):
        training = history[:index]
        actual = history[index]["numbers"]

        random_prediction = random_predictions[position]

        random_results.append(
            count_matches(
                random_prediction,
                actual
            )
        )

        for window in WINDOWS:
            frequency = calculate_recent_frequency(
                training,
                window
            )

            prediction = weighted_sample(
                frequency,
                window
            )

            results[window].append(
                count_matches(
                    prediction,
                    actual
                )
            )

    return results, random_results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def main():
    history = load_history()

    if len(history) < MIN_TRAINING_DRAWS + BLOCK_SIZE:
        print("ERROR: Không đủ dữ liệu để Walk-forward Validation.")
        return

    latest_possible_start = len(history) - BLOCK_SIZE

    block_starts = [
        MIN_TRAINING_DRAWS,
        MIN_TRAINING_DRAWS + BLOCK_SIZE,
        latest_possible_start
    ]

    block_starts = sorted(
        set(
            start
            for start in block_starts
            if start + BLOCK_SIZE <= len(history)
        )
    )

    print("=" * 55)
    print("LOKA-535 BACKTEST V6")
    print("WALK-FORWARD VALIDATION")
    print("=" * 55)

    print(f"Tổng dữ liệu: {len(history)} kỳ")
    print(f"Kích thước mỗi block: {BLOCK_SIZE} kỳ")
    print(f"Cửa sổ kiểm tra: {WINDOWS}")

    print()
    print(
        "Mỗi block chỉ sử dụng dữ liệu xuất hiện "
        "trước kỳ dự đoán."
    )

    overall_results = {
        window: []
        for window in WINDOWS
    }

    overall_random = []

    for block_number, start in enumerate(
        block_starts,
        start=1
    ):
        end = min(
            start + BLOCK_SIZE,
            len(history)
        )

        block_length = end - start

        if block_length <= 0:
            continue

        random_predictions = [
            random_sample()
            for _ in range(block_length)
        ]

        results, random_results = evaluate_block(
            history,
            start,
            end,
            random_predictions
        )

        random_average = average(
            random_results
        )

        overall_random.extend(
            random_results
        )

        print()
        print("=" * 55)
        print(f"BLOCK {block_number}")
        print("=" * 55)

        print(
            f"Test từ index {start} đến {end - 1}"
        )
        print(
            f"Số kỳ kiểm tra: {block_length}"
        )

        print(
            f"Random: {random_average:.4f}"
        )

        for window in WINDOWS:
            model_average = average(
                results[window]
            )

            difference = (
                model_average
                - random_average
            )

            overall_results[window].extend(
                results[window]
            )

            print(
                f"{window:3d} kỳ: "
                f"{model_average:.4f} "
                f"({difference:+.4f})"
            )

    overall_random_average = average(
        overall_random
    )

    print()
    print("=" * 55)
    print("TỔNG HỢP TẤT CẢ BLOCK")
    print("=" * 55)

    print(
        f"Random: "
        f"{overall_random_average:.4f}"
    )

    for window in WINDOWS:
        model_average = average(
            overall_results[window]
        )

        difference = (
            model_average
            - overall_random_average
        )

        print(
            f"{window:3d} kỳ: "
            f"{model_average:.4f} "
            f"({difference:+.4f})"
        )

    print()
    print("=" * 55)
    print("LƯU Ý")
    print("=" * 55)

    print(
        "Backtest không chứng minh rằng mô hình "
        "có thể dự đoán kết quả xổ số."
    )

    print(
        "Mục tiêu của kiểm định là tìm xem tín hiệu "
        "lịch sử có ổn định hơn Random hay không."
    )


if __name__ == "__main__":
    main()