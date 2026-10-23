"""Core implementation: regex-based extraction and normalization of clock times.

Design decisions made once, stated plainly:

1. Only 12-hour AM/PM clock times are supported. 24-hour times (e.g. "14:30")
   are intentionally out of scope. Trying to support both led to ambiguous
   strings like "02:30" and conflicting normalization rules; one clear
   interpretation beats a clever compromise.

2. Minutes are optional. "3 PM" and "3:00 PM" are both valid and normalize
   to the same HH:MM:SS string with minutes=0, seconds=0.

3. Seconds are optional. When present, minutes are required.

4. The HH:MM:SS output is zero-padded to two digits per component. It is a
   display string, not a time-zone-aware timestamp. There is no date, no
   timezone, no duration math. The library extracts and normalizes; it does
   not compute.

5. Hour 12 maps to 00 under 24-hour convention: "12 AM" -> "00:00:00" and
   "12 PM" -> "12:00:00". This is the only non-obvious normalization and the
   one edge case a reader will trip over.

6. find_all returns non-overlapping matches left-to-right, consistent with
   Python's re.finditer. Overlapping text like "1 PM 2 AM" yields two
   separate results.

7. Meridiem matching is case-insensitive and accepts both dotted ("a.m.")
   and undotted ("am") forms. This covers the two most common written
   conventions without pulling in a locale database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeMatch:
    """A single extracted time occurrence.

    Attributes:
        raw: The exact substring matched in the source text.
        hour: 24-hour clock hour in the range 0-23.
        minute: Minute in the range 0-59.
        second: Second in the range 0-59.
        start: Character offset of the match start in the source text.
        end: Character offset just past the match end (exclusive).
    """

    raw: str
    hour: int
    minute: int
    second: int
    start: int
    end: int

    def to_iso(self) -> str:
        """Return a zero-padded HH:MM:SS string.

        Included because callers almost always want a sortable, comparable
        form rather than the individual integer fields.
        """
        return f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}"


class TimeMatcher:
    """Extract and normalize 12-hour AM/PM clock times from text.

    Example:
        >>> m = TimeMatcher()
        >>> results = m.find_all("Meet at 3:15 PM or 9 a.m.")
        >>> [r.to_iso() for r in results]
        ['15:15:00', '09:00:00']
    """

    # Hour 1-12, then optional :MM or :MM:SS, then AM/PM.
    # Dot in the meridiem is optional between both letters, hence
    # the a\.?m\.?\b pattern (handles "am", "a.m", "a.m.").
    _PATTERN = re.compile(
        r"\b(1[0-2]|[1-9])"  # hour
        r"(?::([0-5][0-9])(?::([0-5][0-9]))?)?"  # optional minutes and seconds
        r"\s*([aApP]\.?[mM]\.?)\b",  # meridiem
    )

    def __init__(self) -> None:
        # Compiled once so repeated find_all calls are cheap. The class is
        # effectively stateless beyond the pattern; the constructor exists
        # so future options (e.g. locale) can be added without an API break.
        self._pattern = self._PATTERN

    def find_all(self, text: str) -> list[TimeMatch]:
        """Return all non-overlapping 12-hour times found in *text*.

        Order is left-to-right by position. Returns an empty list when
        nothing matches. Does not raise on malformed input; it simply
        does not match.
        """
        results: list[TimeMatch] = []
        for match in self._pattern.finditer(text):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) is not None else 0
            second = int(match.group(3)) if match.group(3) is not None else 0
            meridiem = match.group(4).lower().replace(".", "")

            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            results.append(
                TimeMatch(
                    raw=match.group(0),
                    hour=hour,
                    minute=minute,
                    second=second,
                    start=match.start(),
                    end=match.end(),
                )
            )
        return results

    def find_first(self, text: str) -> TimeMatch | None:
        """Return the first match, or None if no time is present.

        Convenience method: avoids forcing callers to handle an empty list
        for the common "find one time" use case.
        """
        match = self._pattern.search(text)
        if match is None:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) is not None else 0
        second = int(match.group(3)) if match.group(3) is not None else 0
        meridiem = match.group(4).lower().replace(".", "")

        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        return TimeMatch(
            raw=match.group(0),
            hour=hour,
            minute=minute,
            second=second,
            start=match.start(),
            end=match.end(),
        )
