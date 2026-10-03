import json
import re
import sys
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://www.lotto-8.com/Vietnam/listltoVM35.asp"
HISTORY_FILE = Path("history.json")

MAX_PAGES = 50
REQUEST_DELAY = 0.5

USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/18.3 Mobile/15E148 Safari/604.1"
)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def get_text(self):
        return "\n".join(self.parts)


def fetch_page(page_number):
    query = urlencode({
        "indexpage": page_number,
        "orderby": "new",
    })

    url = f"{BASE_URL}?{query}"

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def html_to_text(html):
    parser = TextParser()
    parser.feed(html)

    lines = []

    for line in parser.get_text().splitlines():
        line = line.replace("\xa0", " ")
        line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()

        if line:
            lines.append(line)

    return lines


def validate_record(record):
    if not isinstance(record, dict):
        return False

    if set(record.keys()) != {
        "id",
        "date",
        "numbers",
        "special",
    }:
        return False

    if not isinstance(record["id"], int):
        return False

    if not isinstance(record["numbers"], list):
        return False

    if len(record["numbers"]) != 5:
        return False

    if len(set(record["numbers"])) != 5:
        return False

    if not all(
        isinstance(n, int) and 1 <= n <= 35
        for n in record["numbers"]
    ):
        return False

    if not isinstance(record["special"], int):
        return False

    if not 1 <= record["special"] <= 12:
        return False

    try:
        datetime.strptime(record["date"], "%Y-%m-%d")
    except ValueError:
        return False

    return True


def parse_page(lines):
    records = []

    for i, line in enumerate(lines):

        match_id = re.fullmatch(r"\d{5}", line)

        if not match_id:
            continue

        draw_id = int(line)

        date_index = None
        day = None
        month = None

        for j in range(i + 1, min(i + 5, len(lines))):
            match_date = re.fullmatch(
                r"(\d{2})/(\d{2})",
                lines[j],
            )

            if match_date:
                day = int(match_date.group(1))
                month = int(match_date.group(2))
                date_index = j
                break

        if date_index is None:
            continue

        year_index = None
        year_short = None

        for j in range(
            date_index + 1,
            min(date_index + 5, len(lines)),
        ):
            if re.fullmatch(r"\d{2}", lines[j]):
                year_short = int(lines[j])
                year_index = j
                break

        if year_index is None:
            continue

        numbers = None
        numbers_index = None

        for j in range(
            year_index + 1,
            min(year_index + 8, len(lines)),
        ):
            values = re.findall(r"\d{1,2}", lines[j])

            if len(values) != 5:
                continue

            candidate = [int(x) for x in values]

            if len(set(candidate)) != 5:
                continue

            if not all(1 <= n <= 35 for n in candidate):
                continue

            numbers = sorted(candidate)
            numbers_index = j
            break

        if numbers_index is None:
            continue

        special = None

        for j in range(
            numbers_index + 1,
            min(numbers_index + 4, len(lines)),
        ):
            if re.fullmatch(r"\d{1,2}", lines[j]):
                value = int(lines[j])

                if 1 <= value <= 12:
                    special = value
                    break

        if special is None:
            continue

        try:
            date_value = datetime(
                2000 + year_short,
                month,
                day,
            ).strftime("%Y-%m-%d")
        except ValueError:
            continue

        record = {
            "id": draw_id,
            "date": date_value,
            "numbers": numbers,
            "special": special,
        }

        if validate_record(record):
            records.append(record)

    return records


def load_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    return [
        record
        for record in data
        if validate_record(record)
    ]


def save_history(records):
    records.sort(
        key=lambda record: record["id"],
        reverse=True,
    )

    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


def collect_all():
    collected = {}

    for page in range(1, MAX_PAGES + 1):

        print(f"Đang đọc trang {page}...")

        try:
            request = fetch_page(page)
            lines = html_to_text(request)
            records = parse_page(lines)

        except Exception as error:
            print(f"Lỗi trang {page}: {error}")
            break

        if not records:
            print("Không còn dữ liệu.")
            break

        print(f"  Tìm thấy {len(records)} kỳ.")

        for record in records:
            collected[record["id"]] = record

        time.sleep(REQUEST_DELAY)

    return list(collected.values())


def main():
    print("=" * 50)
    print("LOKA-535 DATA COLLECTOR")
    print("Nguồn tham khảo: Lotto-8")
    print("=" * 50)

    records = collect_all()

    if not records:
        print()
        print("ERROR: Không lấy được dữ liệu.")
        print("history.json không bị thay đổi.")
        sys.exit(1)

    history = load_history()

    combined = {
        record["id"]: record
        for record in history
    }

    for record in records:
        combined[record["id"]] = record

    final_history = list(combined.values())

    save_history(final_history)

    print()
    print(f"Đã thu thập: {len(records)} kỳ.")
    print(f"Tổng history.json: {len(final_history)} kỳ.")
    print("SUCCESS")


if __name__ == "__main__":
    main()