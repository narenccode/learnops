"""Say how many days are left until a date."""

import argparse
from datetime import date


def days_until(target: date, today: date) -> int:
    return (target - today).days


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=date.fromisoformat)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    print(f"{days_until(args.target, args.today)} days until {args.target}.")


if __name__ == "__main__":
    main()
