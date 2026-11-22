"""Pair synthetic camera exposures with motion samples on a common trigger clock."""

import argparse
from bisect import bisect_left
import csv
import sys
from gait import state


def match_frames(frame_ticks, motion_ticks, tolerance):
    """Return (frame tick, nearest motion index or None); earlier wins a tie.

    Both sequences must use the same time unit and trigger origin.
    """
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    if any(a >= b for a, b in zip(motion_ticks, motion_ticks[1:])):
        raise ValueError("motion timestamps must increase strictly")
    for tick in frame_ticks:
        i = bisect_left(motion_ticks, tick)
        neighbors = [j for j in (i - 1, i) if 0 <= j < len(motion_ticks)]
        closest = min(
            neighbors, key=lambda j: abs(motion_ticks[j] - tick), default=None
        )
        if closest is not None and abs(motion_ticks[closest] - tick) > tolerance:
            closest = None
        yield tick, closest


def example(stream):
    # Integer microseconds avoid float comparisons at exposure boundaries.
    # One synthetic second is stretched to 1.8 seconds in the presentation.
    ticks = list(range(0, 1_000_000, 10_000))
    exposures = range(0, 1_000_000, 250_000)
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["camera_us", "motion_us", "offset_us", "knee_flexion_deg"])
    for frame, i in match_frames(exposures, ticks, 5_000):
        sample = ticks[i]
        writer.writerow(
            [frame, sample, sample - frame, f"{state(sample/1_000_000)['near'][1]:.2f}"]
        )


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    example(sys.stdout)
