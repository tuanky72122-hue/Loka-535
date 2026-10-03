import json
from collections import Counter
from pathlib import Path


HISTORY_FILE = Path("history.json")
RECENT_WINDOW = 100


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return sorted(
        data,
        key=lambda record: record["id"],
    )


def calculate_frequency(history):
    counter = Counter()

    for record in history:
        for number in record["numbers"]:
            counter[number] += 1

    return {
        number: counter[number]
        for number in range(1, 36)
    }


def calculate_recent_frequency(history, window):
    recent = history[-window:]
    counter = Counter()

    for record in recent:
        for number in record["numbers"]:
            counter[number] += 1

    return {
        number: counter[number]
        for number in range(1, 36)
    }


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


def calculate_deviation(history, frequency):
    total_draws = len(history)
    expected = total_draws * 5 / 35

    return {
        number: round(
            frequency[number] - expected,
            2,
        )
        for number in range(1, 36)
    }


def print_section(title):
    print()
    print("=" * 50)
    print(title)
    print("=" * 50)


def main():
    history = load_history()

    if not history:
        print("ERROR: history.json không có dữ liệu.")
        return

    frequency = calculate_frequency(history)

    recent_frequency = calculate_recent_frequency(
        history,
        RECENT_WINDOW,
    )

    gap = calculate_gap(history)

    deviation = calculate_deviation(
        history,
        frequency,
    )

    print("=" * 50)
    print("LOKA-535 ANALYTICS")
    print("=" * 50)

    print(f"Tổng số kỳ: {len(history)}")
    print(f"Cửa sổ gần đây: {RECENT_WINDOW} kỳ")

    print_section("TẦN SUẤT TOÀN BỘ")

    for number in range(1, 36):
        print(
            f"{number:02d}: "
            f"{frequency[number]}"
        )

    print_section(
        f"TẦN SUẤT {RECENT_WINDOW} KỲ GẦN NHẤT"
    )

    for number in range(1, 36):
        print(
            f"{number:02d}: "
            f"{recent_frequency[number]}"
        )

    print_section("GAP - SỐ KỲ CHƯA XUẤT HIỆN")

    for number in range(1, 36):
        print(
            f"{number:02d}: "
            f"{gap[number]}"
        )

    print_section(
        "ĐỘ LỆCH SO VỚI TẦN SUẤT KỲ VỌNG"
    )

    for number in range(1, 36):
        print(
            f"{number:02d}: "
            f"{deviation[number]:+.2f}"
        )


if __name__ == "__main__":
    main()