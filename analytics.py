import json
from collections import Counter
from pathlib import Path


HISTORY_FILE = Path("history.json")


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def analyze(history):
    number_counter = Counter()
    special_counter = Counter()

    for record in history:
        for number in record["numbers"]:
            number_counter[number] += 1

        special_counter[record["special"]] += 1

    total_draws = len(history)

    number_frequency = {
        number: number_counter[number]
        for number in range(1, 36)
    }

    special_frequency = {
        number: special_counter[number]
        for number in range(1, 13)
    }

    return {
        "total_draws": total_draws,
        "number_frequency": number_frequency,
        "special_frequency": special_frequency,
    }


def main():
    history = load_history()

    if not history:
        print("ERROR: history.json không có dữ liệu.")
        return

    result = analyze(history)

    print("=" * 50)
    print("LOKA-535 ANALYTICS")
    print("=" * 50)

    print(f"Tổng số kỳ: {result['total_draws']}")

    print()
    print("Tần suất 1-35:")

    for number, frequency in result["number_frequency"].items():
        print(f"{number:02d}: {frequency}")

    print()
    print("Tần suất số đặc biệt 1-12:")

    for number, frequency in result["special_frequency"].items():
        print(f"{number:02d}: {frequency}")


if __name__ == "__main__":
    main()