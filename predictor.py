import json
import secrets
from pathlib import Path

HISTORY_FILE = Path("history.json")

SHORT_WINDOW = 50
LONG_WINDOW = 100

SHORT_WEIGHT = 0.50
LONG_WEIGHT = 0.50


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(data, key=lambda record: record["id"])


def calculate_frequency(history, window):
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
            SHORT_WEIGHT * short_weights[number]
            + LONG_WEIGHT * long_weights[number]
        )
        for number in range(1, 36)
    }


def weighted_sample(weights):
    available = dict(weights)
    selected = []

    while len(selected) < 5:
        total_weight = sum(available.values())

        random_value = (
            secrets.randbelow(10_000_000)
            / 10_000_000
            * total_weight
        )

        cumulative = 0

        for number, weight in available.items():
            cumulative += weight

            if random_value <= cumulative:
                selected.append(number)
                del available[number]
                break

    return sorted(selected)


def main():
    history = load_history()

    if len(history) < LONG_WINDOW:
        print("ERROR: Không đủ dữ liệu để tạo bộ số.")
        return

    short_frequency = calculate_frequency(
        history,
        SHORT_WINDOW
    )

    long_frequency = calculate_frequency(
        history,
        LONG_WINDOW
    )

    short_weights = build_weights(
        short_frequency,
        SHORT_WINDOW
    )

    long_weights = build_weights(
        long_frequency,
        LONG_WINDOW
    )

    final_weights = blend_weights(
        short_weights,
        long_weights
    )

    prediction = weighted_sample(
        final_weights
    )

    print("=" * 50)
    print("LOKA-535 PREDICTOR")
    print("=" * 50)

    print(
        f"Dữ liệu: {len(history)} kỳ"
    )

    print(
        f"Cửa sổ: {SHORT_WINDOW} + "
        f"{LONG_WINDOW} kỳ"
    )

    print(
        f"Blend: {SHORT_WEIGHT:.0%} / "
        f"{LONG_WEIGHT:.0%}"
    )

    print()
    print("BỘ SỐ THAM CHIẾU:")
    print(
        " - ".join(
            f"{number:02d}"
            for number in prediction
        )
    )

    print()
    print(
        "Lưu ý: Đây là bộ số được chọn "
        "bằng weighted random từ dữ liệu lịch sử."
    )

    print(
        "Kết quả xổ số vẫn mang tính ngẫu nhiên."
    )


if __name__ == "__main__":
    main()