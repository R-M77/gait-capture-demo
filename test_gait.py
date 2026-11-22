import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

import gait
import render
from sync import match_frames


class GaitTest(unittest.TestCase):
    def test_support_clearance_and_chain_length(self):
        for i in range(1000):
            t = i / 1000
            thigh, knee, shoe = map(math.radians, gait.state(t)["near"])
            x = -gait.LENGTH * (math.sin(thigh) + math.sin(thigh + knee))
            y = gait.pelvis(t) + gait.LENGTH * (
                math.cos(thigh) + math.cos(thigh + knee)
            )
            ax, ay, pitch = gait.ankle(t)
            self.assertAlmostEqual(x, ax)
            self.assertAlmostEqual(y, ay)
            theta = thigh + knee + shoe
            self.assertAlmostEqual(theta, math.radians(pitch))
            pivot = 9 if pitch >= 0 else -3.3
            sole_y = y + 3.4 * math.cos(theta) + pivot * math.sin(theta)
            if t <= gait.STANCE_END:
                self.assertAlmostEqual(sole_y, gait.FLOOR)
                world_x = (
                    x
                    + pivot * math.cos(theta)
                    - 3.4 * math.sin(theta)
                    + gait.STRIDE_TRAVEL * t
                )
                self.assertAlmostEqual(world_x, 22 + pivot)
            else:
                self.assertLess(sole_y, gait.FLOOR)

    def test_phase_landmarks(self):
        bend = lambda t: gait.state(t)["near"][1]
        self.assertLess(bend(0), 10)
        self.assertTrue(15 < bend(0.14) < 24)
        self.assertLess(bend(0.38), 10)
        peak = max(range(100), key=lambda i: bend(i / 100))
        self.assertTrue(70 <= peak <= 76)
        self.assertTrue(55 <= bend(peak / 100) <= 65)
        for i in range(100):
            t = i / 100
            for a, b in zip(gait.state(t)["near"], gait.state(t + 0.5)["far"]):
                self.assertAlmostEqual(a, b)
        self.assertEqual(gait.state(0)["near"], gait.state(1)["near"])

    def test_shipped_figures_and_timing(self):
        ns = "{http://www.w3.org/2000/svg}"
        with TemporaryDirectory() as tmp:
            for compact in (False, True):
                for animated in (False, True):
                    render.build(compact, animated, Path(tmp))
            for file in Path(tmp).glob("*.svg"):
                self.assertEqual(
                    file.read_bytes(), (render.FIG / file.name).read_bytes()
                )
                svg = ET.parse(file)
                animations = [
                    e
                    for e in svg.iter()
                    if e.tag in (ns + "animate", ns + "animateTransform")
                ]
                if "-still" in file.name:
                    self.assertFalse(animations)
                    continue
                self.assertTrue(
                    all(
                        e.get("dur") == f"{gait.DURATION}s"
                        and e.get("repeatCount") == "indefinite"
                        for e in animations
                    )
                )
                knee = svg.find(".//*[@id='near-knee']")[0]
                point = svg.find(".//*[@id='motion-point']")[0]
                angles = list(map(float, knee.get("values").split(";")))
                heights = list(map(float, point.get("values").split(";")))
                top, bottom = (136, 174) if "compact" in file.name else (167, 210)
                self.assertEqual(len(angles), len(heights))
                self.assertEqual(len(angles), len(render.PHASES))
                for t, deg, y in zip(render.PHASES, angles, heights):
                    self.assertAlmostEqual(deg, gait.state(t)["near"][1], delta=0.00051)
                    self.assertAlmostEqual(
                        y, bottom - deg / 90 * (bottom - top), delta=0.001
                    )
                for i in range(4):
                    sample = svg.find(f".//*[@id='frame-{i}']")[0]
                    self.assertEqual(sample.get("keyTimes"), "0;0.25;0.5;0.75;1")
                    self.assertEqual(
                        sample.get("values").split(";"),
                        [str(int(j == i)) for j in (0, 1, 2, 3, 0)],
                    )


class PairingTest(unittest.TestCase):
    def test_offsets_ties_missing_and_boundaries(self):
        self.assertEqual(
            list(match_frames([-5, 5, 16, 31, 60], [0, 10, 30], 5)),
            [(-5, 0), (5, 0), (16, None), (31, 2), (60, None)],
        )
        self.assertEqual(list(match_frames([0], [], 0)), [(0, None)])
        for times in ([1, 1], [2, 1]):
            with self.assertRaises(ValueError):
                list(match_frames([0], times, 0))
        with self.assertRaises(ValueError):
            list(match_frames([0], [0], -1))


if __name__ == "__main__":
    unittest.main()
