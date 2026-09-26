"""Bouncy numbers — Python implementation."""

from __future__ import annotations

import sys


def is_bouncy(n: int) -> bool:
    """Return True if n is a bouncy number."""
    digits = [int(d) for d in str(n)]
    increasing = all(digits[i] <= digits[i + 1] for i in range(len(digits) - 1))
    decreasing = all(digits[i] >= digits[i + 1] for i in range(len(digits) - 1))
    return not increasing and not decreasing


def least_number_with_bouncy_ratio(percent: int) -> int:
    """Return the least number for which bouncy numbers are exactly `percent`%.

    Uses integer arithmetic: bouncy_count * 100 == percent * current to avoid
    floating-point comparison errors.

    Args:
        percent: Target percentage, must be between 1 and 99 inclusive.

    Raises:
        ValueError: If percent is outside the valid range.
    """
    if not (1 <= percent <= 99):
        raise ValueError(f"percent must be between 1 and 99, got {percent}")

    bouncy_count = 0
    current = 1

    while True:
        current += 1
        if is_bouncy(current):
            bouncy_count += 1
        if bouncy_count * 100 == percent * current:
            return current


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python bouncy.py <percent>")
        sys.exit(1)

    try:
        percent = int(sys.argv[1])
    except ValueError:
        print("Error: percent must be an integer.")
        sys.exit(1)

    try:
        result = least_number_with_bouncy_ratio(percent)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
