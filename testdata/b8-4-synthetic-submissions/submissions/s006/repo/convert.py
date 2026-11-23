"""Convert between kilometres and miles."""

import sys

KM_PER_MILE = 1.609344


def to_miles(km: float) -> float:
    return km / KM_PER_MILE


def to_km(miles: float) -> float:
    return miles * KM_PER_MILE


if __name__ == "__main__":
    value, unit = float(sys.argv[1]), sys.argv[2]
    print(to_miles(value) if unit == "km" else to_km(value))
