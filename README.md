# time_regex_matcher_py

Extracts and normalizes 12-hour AM/PM clock times from unstructured text using regular expressions.

## Usage

```python
from time_regex_matcher_py import TimeMatcher, TimeMatch

m = TimeMatcher()
results = m.find_all("Meet at 3:15 PM or 9 a.m.")
for r in results:
    print(r.raw, r.to_iso())
# 3:15 PM 15:15:00
# 9 a.m. 09:00:00

first = m.find_first("Lunch at 12 PM")
print(first.to_iso())  # 12:00:00
```

## Why this exists

Clock times appear in prose, logs, and free-form notes in inconsistent forms: dotted meridiems, undotted ones, with or without seconds. This library extracts them and normalizes to a zero-padded `HH:MM:SS` string without dragging in a date parser or a locale database. The trade-off: only 12-hour AM/PM notation is supported. 24-hour times like `14:30` are deliberately out of scope, because trying to support both led to ambiguous strings and conflicting normalization rules. One interpretation, stated plainly.

## The edge you will hit

`12 AM` normalizes to `00:00:00` and `12 PM` stays `12:00:00`. This is the standard 12-to-24-hour conversion, but it is the one case where the arithmetic is not just "add 12 for PM." If your downstream code assumes hours 1-12, the midnight result will surprise you.

## Exports

- `TimeMatcher` — the extractor. Methods: `find_all(text)` returns `list[TimeMatch]`, `find_first(text)` returns `TimeMatch | None`.
- `TimeMatch` — frozen dataclass with fields `raw`, `hour`, `minute`, `second`, `start`, `end`, and a `to_iso()` method returning `HH:MM:SS`.

Zero third-party dependencies. Standard library only.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

