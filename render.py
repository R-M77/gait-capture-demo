"""Render desktop, compact and reduced-motion SVGs from the synthetic gait model."""

from pathlib import Path
import xml.etree.ElementTree as ET
from gait import DURATION, FLOOR, STRIDE_TRAVEL, state

FIG = Path(__file__).resolve().parent / "figures"
COUNT = 64
PHASES = [i / COUNT for i in range(COUNT + 1)]
COLORS = {
    "ink": "#e6eee7",
    "back": "#70887b",
    "backarm": "#84998c",
    "shirt": "#aec6b1",
    "front": "#d2ddd1",
    "skin": "#e0e7d6",
    "green": "#98e9a7",
}


def el(parent, tag, **attrs):
    return ET.SubElement(
        parent, tag, {k.replace("_", "-"): str(v) for k, v in attrs.items()}
    )


def fmt(x):
    return f"{x:.3f}".rstrip("0").rstrip(".") or "0"


def anim(node, attr, values, active, kind=None, discrete=False, times=None):
    node.set(attr, (kind + "(" + values[0] + ")") if kind else values[0])
    if active:
        args = dict(
            attributeName=attr,
            dur=f"{DURATION}s",
            repeatCount="indefinite",
            values=";".join(values),
            calcMode="discrete" if discrete else "linear",
        )
        if times:
            args["keyTimes"] = ";".join(map(fmt, times))
        if kind:
            args["type"] = kind
        el(node, "animateTransform" if kind else "animate", **args)


def joint(parent, values, kind, active, id=None):
    node = el(parent, "g", **({"id": id} if id else {}))
    anim(node, "transform", values, active, kind)
    return node


def path(g, d, color):
    return el(g, "path", d=d, fill=color)


def person(parent, phases, active=False, selected=False):
    states = [state(t) for t in phases]
    hip = joint(parent, ["0 " + fmt(s["hip"]) for s in states], "translate", active)

    def drawleg(key):
        far = key == "far"
        color = COLORS["back"] if far else COLORS["front"]
        shoe = "#647b6f" if far else "#a9bda9"
        angles = [s[key] for s in states]
        thigh = joint(hip, [fmt(a[0]) for a in angles], "rotate", active)
        path(
            thigh,
            "M-6 -2 Q0 -7 5 -2 Q8 6 5 20 L3.6 36 Q1 40 -3.8 36 L-6 17 Q-8 4 -6 -2Z",
            color,
        )
        knee = joint(
            el(thigh, "g", transform="translate(0 36)"),
            [fmt(a[1]) for a in angles],
            "rotate",
            active,
            "near-knee" if selected and not far else None,
        )
        path(
            knee,
            "M-3.7 -1 Q0 -4.5 3.8 -1 Q6 7 3.7 17 L1.9 35 Q-0.5 38 -2.4 35 L-4 16 Q-5.5 6 -3.7 -1Z",
            color,
        )
        ankle = joint(
            el(knee, "g", transform="translate(0 36)"),
            [fmt(a[2]) for a in angles],
            "rotate",
            active,
        )
        path(
            ankle,
            "M-2.7 -2 L2 -2 Q4 .1 7 .2 Q11 .5 11.4 2.5 Q10.8 3.6 8.5 3.6 L-3.3 3.4 Q-4.6 2.2 -2.7 -2Z",
            shoe,
        )
        if not far:
            el(
                knee,
                "circle",
                r=2.6,
                fill="#214e39",
                stroke=COLORS["green"],
                stroke_width=1.25,
            )

    def arm(key):
        far = key == "backarm"
        angles = [s[key] for s in states]
        arm = joint(
            el(hip, "g", transform="translate(2 -37)"),
            [fmt(a) for a in angles],
            "rotate",
            active,
        )
        color = COLORS["backarm"] if far else COLORS["skin"]
        path(arm, "M-3.7 0 Q0 -4 3.7 0 L3 20 Q0 23 -2.8 20Z", color)
        forearm = joint(
            el(arm, "g", transform="translate(0 20)"),
            [fmt(-19 + a * 0.25) for a in angles],
            "rotate",
            active,
        )
        path(
            forearm,
            "M-2.9 -1 Q0 -3 2.9 -1 L2.1 14 Q4.1 17.2 2.6 20 Q1.6 22 -.8 20 L-2 16Z",
            color,
        )

    drawleg("far")
    arm("backarm")
    drawleg("near")
    path(
        hip,
        "M-6 -2 Q-7 -11 -5 -25 Q-5 -39 1 -42 Q5 -44 9 -40 Q13 -34 10 -26 Q7 -18 8 -11 L8 -1 Q1 2 -6 -2Z",
        COLORS["shirt"],
    )
    path(
        hip,
        "M0 -42 L1 -47 Q-2 -51 -.8 -56 Q1 -62 7 -61 Q13 -60 13.4 -55 L13.3 -53 L15 -50.6 L13.2 -49.8 Q13.5 -45.6 10 -45.8 L7.4 -46 L7.2 -41 Q4 -39.6 0 -42Z",
        COLORS["skin"],
    )
    arm("arm")


def shape(g, x, y, w, h, rx, fill, **attrs):
    return el(g, "rect", x=x, y=y, width=w, height=h, rx=rx, fill=fill, **attrs)


def build(compact, active, output=FIG):
    output.mkdir(parents=True, exist_ok=True)
    w, h = (384, 194) if compact else (724, 236)
    left, rx, rw = (142, 153, 219) if compact else (264, 293, 410)
    ytop, ybottom = (10, 183) if compact else (13, 222)
    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        width=str(w),
        height=str(h),
        viewBox=f"0 0 {w} {h}",
        role="img",
    )
    el(svg, "title").text = "Synchronized gait capture for fall detection"
    el(svg, "desc").text = (
        "One illustrated stride. Four camera samples follow the walker, and a point on the motion trace follows the bend of the foreground knee."
    )
    shape(svg, 1, 1, w - 2, h - 2, 12, "#141d1a", stroke="#475a50")
    shape(svg, 10, ytop, left - 10, ybottom - ytop, 8, "#0e1714")
    # Camera framing brackets leave the scene free of captions.
    for x, y, sx, sy in [
        (18, ytop + 9, 1, 1),
        (left - 8, ytop + 9, -1, 1),
        (18, ybottom - 9, 1, -1),
        (left - 8, ybottom - 9, -1, -1),
    ]:
        el(
            svg,
            "path",
            d=f"M{x+sx*10} {y} H{x} v{sy*10}",
            fill="none",
            stroke="#607c6b",
            stroke_width=1.6,
        )
    scale, floor_y = (1.06, 164) if compact else (1.32, 199)
    cx = (left + 10) / 2
    top = floor_y - FLOOR * scale
    phases = PHASES if active else [0.25]
    el(svg, "path", d=f"M21 {floor_y} H{left-10}", stroke="#536c5d")
    defs = el(svg, "defs")
    clip = el(defs, "clipPath", id="ground")
    shape(clip, 21, floor_y + 1, left - 31, 7, 0, "white")
    ground = el(svg, "g", clip_path="url(#ground)")
    scroll = el(ground, "g")
    anim(
        scroll,
        "transform",
        [fmt(-p * STRIDE_TRAVEL * scale) + " 0" for p in phases],
        active,
        "translate",
    )
    for i in range(13):
        x = 21 + i * (STRIDE_TRAVEL / 4) * scale
        el(scroll, "path", d=f"M{fmt(x)} {floor_y+2} v3", stroke="#415649")
    person(
        el(svg, "g", transform=f"translate({cx} {fmt(top)}) scale({scale})"),
        phases,
        active,
        True,
    )
    label1, cy, ch, label2, plot_top, plot_bottom = (
        (31, 40, 52, 121, 136, 174) if compact else (41, 51, 67, 154, 167, 210)
    )

    def label(y, txt):
        el(
            svg,
            "text",
            x=rx,
            y=y,
            fill=COLORS["ink"],
            font_family="system-ui, sans-serif",
            font_size=14 if compact else 17,
            font_weight=600,
        ).text = txt

    label(label1, "Camera frames")
    label(label2, "Knee motion")
    cell = rw / 4
    for i in range(4):
        x = rx + i * cell
        width = cell - 4
        shape(svg, fmt(x), cy, fmt(width), ch, 5, "#213129")
        sample_scale = ch / 158
        person(
            el(
                svg,
                "g",
                transform=f"translate({fmt(x+width/2)} {fmt(cy+(ch-138*sample_scale)/2-23*sample_scale)}) scale({fmt(sample_scale)})",
            ),
            [i / 4],
        )
        highlight = shape(
            svg,
            fmt(x + 1),
            cy + 1,
            fmt(width - 2),
            ch - 2,
            4,
            "none",
            stroke=COLORS["green"],
            stroke_width=2,
            id=f"frame-{i}",
        )
        index = list(range(4)) + [0] if active else [1]
        anim(
            highlight,
            "opacity",
            ["1" if k == i else "0" for k in index],
            active,
            discrete=True,
            times=[0, 0.25, 0.5, 0.75, 1],
        )
    start, end = rx, rx + rw - 4

    def pos(t):
        angle = state(t)["near"][1]
        return start + t * (end - start), plot_bottom - (angle / 90) * (
            plot_bottom - plot_top
        )

    for i in range(5):
        x = start + i * (end - start) / 4
        el(
            svg,
            "path",
            d=f"M{fmt(x)} {plot_top-4} V{plot_bottom+1}",
            stroke="#34473c",
            stroke_dasharray="2 4",
        )
    points = [pos(i / COUNT) for i in range(COUNT + 1)]
    d = "M" + " L".join(fmt(x) + " " + fmt(y) for x, y in points)
    path(svg, d + f" V{plot_bottom+1} H{start}Z", "#203a2c")
    el(
        svg,
        "path",
        d=d,
        fill="none",
        stroke=COLORS["green"],
        stroke_width=2.4,
        stroke_linecap="round",
        stroke_linejoin="round",
    )
    el(svg, "path", d=f"M{start} {plot_bottom+1} H{end}", stroke="#506455")
    playhead = joint(
        svg, [fmt(pos(t)[0]) + " 0" for t in phases], "translate", active, "playhead"
    )
    el(playhead, "path", d=f"M0 {plot_top-4} V{plot_bottom+1}", stroke="#c0d5c6")
    point = el(
        playhead,
        "circle",
        cx="0",
        r=3.6 if compact else 4.3,
        fill=COLORS["green"],
        stroke="#15241b",
        stroke_width=1.5,
        id="motion-point",
    )
    anim(point, "cy", [fmt(pos(t)[1]) for t in phases], active)
    ET.indent(svg)
    file = output / (
        "gait-capture"
        + ("-compact" if compact else "")
        + ("" if active else "-still")
        + ".svg"
    )
    with file.open("w", encoding="utf-8", newline="\n") as stream:
        ET.ElementTree(svg).write(stream, encoding="unicode")


if __name__ == "__main__":
    for compact in (False, True):
        for active in (True, False):
            build(compact, active)
