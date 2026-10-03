import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

MIN_TRAINING_DRAWS = 300
BLOCK_SIZE = 200

WINDOW_SHORT = 50
WINDOW_LONG = 100

BLEND_SHORT_WEIGHT = 0.50
BLEND_LONG_WEIGHT = 0.50


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(data, key=lambda record: record["id"])


def calculate_recent_frequency(history, window):
    recent = history[-window:]

    frequency = {
        number: 0
        for number in range(1, 36)
    }

    for record in recent:
        for number in record["numbers"]:
            frequency[number] += 1

    return frequency


def build_weights(frequency, window):
    expected = window * 5 / 35

    return {
        number: max(
            frequency[number] / expected,
            0.01
        )
        for number in range(1, 36)
    }


def blend_weights(short_weights, long_weights):
    return {
        number: (
            BLEND_SHORT_WEIGHT
            * short_weights[number]
            +
            BLEND_LONG_WEIGHT
            * long_weights[number]
        )
        for number in range(1, 36)
    }


def weighted_sample(weights):
    available = dict(weights)
    selected = []

    for _ in range(5):
        total_weight = sum(
            available.values()
        )

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
        index = secrets.randbelow(
            len(numbers)
        )

        selected.append(
            numbers.pop(index)
        )

    return sorted(selected)


def count_matches(prediction, actual):
    return len(
        set(prediction) &
        set(actual)
    )


def evaluate_block(
    history,
    start,
    end,
    random_predictions
):
    results = {
        "random": [],
        "50": [],
        "100": [],
        "blend": []
    }

    for position, index in enumerate(
        range(start, end)
    ):
        training = history[:index]
        actual = history[index]["numbers"]

        random_prediction = (
            random_predictions[position]
        )

        results["random"].append(
            count_matches(
                random_prediction,
                actual
            )
        )

        short_frequency = (
            calculate_recent_frequency(
                training,
                WINDOW_SHORT
            )
        )

        long_frequency = (
            calculate_recent_frequency(
                training,
                WINDOW_LONG
            )
        )

        short_weights = build_weights(
            short_frequency,
            WINDOW_SHORT
        )

        long_weights = build_weights(
            long_frequency,
            WINDOW_LONG
        )

        prediction_50 = weighted_sample(
            short_weights
        )

        prediction_100 = weighted_sample(
            long_weights
        )

        blended = blend_weights(
            short_weights,
            long_weights
        )

        prediction_blend = weighted_sample(
            blended
        )

        results["50"].append(
            count_matches(
                prediction_50,
                actual
            )
        )

        results["100"].append(
            count_matches(
                prediction_100,
                actual
            )
        )

        results["blend"].append(
            count_matches(
                prediction_blend,
                actual
            )
        )

    return results


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def main():
    history = load_history()

    if len(history) < (
        MIN_TRAINING_DRAWS + BLOCK_SIZE
    ):
        print(
            "ERROR: Không đủ dữ liệu "
            "để chạy Backtest V7."
        )
        return

    latest_possible_start = (
        len(history) - BLOCK_SIZE
    )

    block_starts = [
        MIN_TRAINING_DRAWS,
        MIN_TRAINING_DRAWS + BLOCK_SIZE,
        latest_possible_start
    ]

    block_starts = sorted(
        set(
            start
            for start in block_starts
            if start + BLOCK_SIZE
            <= len(history)
        )
    )

    overall = {
        "random": [],
        "50": [],
        "100": [],
        "blend": []
    }

    print("=" * 60)
    print("LOKA-535 BACKTEST V7")
    print("BLEND 50/100")
    print("=" * 60)

    print(
        f"Tổng dữ liệu: {len(history)} kỳ"
    )

    print(
        f"Block: {BLOCK_SIZE} kỳ"
    )

    print(
        "Mô hình: Random / 50 / 100 / Blend 50-50"
    )

    print()
    print(
        "Blend = 50% trọng số 50 kỳ "
        "+ 50% trọng số 100 kỳ."
    )

    for block_number, start in enumerate(
        block_starts,
        start=1
    ):
        end = min(
            start + BLOCK_SIZE,
            len(history)
        )

        block_length = end - start

        random_predictions = [
            random_sample()
            for _ in range(block_length)
        ]

        results = evaluate_block(
            history,
            start,
            end,
            random_predictions
        )

        print()
        print("=" * 60)
        print(f"BLOCK {block_number}")
        print("=" * 60)

        print(
            f"Test index: {start} → {end - 1}"
        )

        for model in [
            "random",
            "50",
            "100",
            "blend"
        ]:
            model_average = average(
                results[model]
            )

            random_average = average(
                results["random"]
            )

            difference = (
                model_average
                - random_average
            )

            if model == "random":
                print(
                    f"Random : "
                    f"{model_average:.4f}"
                )
            else:
                print(
                    f"{model:>6} : "
                    f"{model_average:.4f} "
                    f"({difference:+.4f})"
                )

            overall[model].extend(
                results[model]
            )

    random_overall = average(
        overall["random"]
    )

    print()
    print("=" * 60)
    print("TỔNG HỢP TẤT CẢ BLOCK")
    print("=" * 60)

    print(
        f"Random : "
        f"{random_overall:.4f}"
    )

    for model in [
        "50",
        "100",
        "blend"
    ]:
        model_average = average(
            overall[model]
        )

        difference = (
            model_average
            - random_overall
        )

        print(
            f"{model:>6} : "
            f"{model_average:.4f} "
            f"({difference:+.4f})"
        )

    print()
    print("=" * 60)
    print("KẾT THÚC V7")
    print("=" * 60)

    print(
        "Backtest chỉ đánh giá tín hiệu lịch sử, "
        "không chứng minh khả năng dự đoán xổ số."
    )


if __name__ == "__main__":
    main()