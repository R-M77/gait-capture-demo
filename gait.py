from math import acos, atan2, cos, degrees, hypot, pi, radians, sin, sqrt

LENGTH = 36
FLOOR = 160
STANCE_END = 0.60
STRIDE_TRAVEL = 76
# A slowed presentation clock makes the four camera samples easy to follow.
DURATION = 1.8


def curve(t, keys):
    """Periodic cubic Hermite interpolation; tangent units are per cycle."""
    t %= 1
    for (a, x, dx), (b, y, dy) in zip(keys, keys[1:]):
        if a <= t <= b:
            span = b - a
            s = (t - a) / span
            return (
                (2 * s**3 - 3 * s**2 + 1) * x
                + (s**3 - 2 * s**2 + s) * span * dx
                + (-2 * s**3 + 3 * s**2) * y
                + (s**3 - s**2) * span * dy
            )


def ankle(t):
    """Tracking-camera coordinates. Heel and toe pivot about the planted sole."""
    t %= 1
    pitch = curve(
        t,
        [
            (0, -12, 0),
            (0.09, 0, 0),
            (0.39, 0, 0),
            (0.50, 6, 125),
            (0.6, 35, 50),
            (0.66, 36, 0),
            (0.84, 1, -130),
            (0.95, -12, 0),
            (1, -12, 0),
        ],
    )
    theta = radians(pitch)
    # Align the supporting sole point with the moving floor at heel strike,
    # foot flat, and toe-off. A flat heel-to-toe shoe is used for contact geometry.
    toe, heel = 9.0, -3.3
    pivot = toe if pitch >= 0 else heel
    x = curve(
        t,
        [
            (0, 22, -76),
            (0.6, 22 - 0.6 * 76, -76),
            (0.65, -25, 0),
            (0.82, -1, 152),
            (0.955, 22.8, 0),
            (1, 22, -76),
        ],
    )
    x += pivot * (1 - cos(theta)) + 3.4 * sin(theta)
    lift = curve(
        t,
        [
            (0, 0, 0),
            (0.6, 0, 0),
            (0.72, 6.8, 0),
            (0.89, 3.6, -34),
            (0.955, 1.6, -24),
            (1, 0, 0),
        ],
    )
    y = FLOOR - (3.4 * cos(theta) + pivot * sin(theta)) - lift
    return x, y, pitch


def pelvis(t):
    # Choose a continuous pelvis path through three stance landmarks. For a
    # two-link leg, hip-to-ankle distance is 2 * length * cos(knee_flexion / 2).
    heights = []
    for phase, flexion in [(0, 7), (0.14, 19), (0.38, 6)]:
        x, y, _ = ankle(phase)
        radius = 2 * LENGTH * cos(radians(flexion / 2))
        heights.append(y - sqrt(radius**2 - x * x))
    a, b, c = heights
    return curve(2 * t, [(0, a, 0), (0.28, b, 0), (0.76, c, 0), (1, a, 0)])


def leg(t, hip_y):
    x, y, pitch = ankle(t)
    dy = y - hip_y
    ratio = hypot(x, dy) / (2 * LENGTH)
    if ratio > 1.000001:
        raise ValueError(f"Ankle beyond reach at phase {t % 1:.4f}")
    half = acos(min(1.0, ratio))
    thigh = -degrees(atan2(x, dy) + half)
    bend = degrees(2 * half)
    return thigh, bend, pitch - thigh - bend


def state(t):
    hip = pelvis(t)
    arm = 20 * cos(2 * pi * (t - 0.03))
    return {
        "hip": hip,
        "near": leg(t, hip),
        "far": leg(t + 0.5, hip),
        "arm": arm,
        "backarm": -arm,
    }
