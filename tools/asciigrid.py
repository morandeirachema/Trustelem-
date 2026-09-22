"""Tiny helper to draw ASCII box diagrams and sequence diagrams on a fixed grid.

Usage from a diagram script:

    from asciigrid import Grid, sequence
    g = Grid(80, 20)
    g.box(0, 0, 20, 4, [" Title", " line 2"])
    g.vline(10, 4, 8)
    print(g.render())

Every box, line and label is placed at explicit coordinates so borders always align.
"""


class Grid:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.g = [[" "] * width for _ in range(height)]

    def put(self, x, y, text):
        for i, c in enumerate(text):
            if 0 <= x + i < self.w and 0 <= y < self.h:
                self.g[y][x + i] = c

    def box(self, x, y, w, h, lines=()):
        self.put(x, y, "+" + "-" * (w - 2) + "+")
        self.put(x, y + h - 1, "+" + "-" * (w - 2) + "+")
        for r in range(y + 1, y + h - 1):
            self.put(x, r, "|" + " " * (w - 2) + "|")
        for i, line in enumerate(lines):
            self.put(x + 1, y + 1 + i, line.ljust(w - 2)[: w - 2])

    def vline(self, x, y1, y2, ch="|"):
        for r in range(y1, y2 + 1):
            self.put(x, r, ch)

    def hline(self, y, x1, x2, ch="-"):
        for c in range(x1, x2 + 1):
            self.put(c, y, ch)

    def render(self):
        return "\n".join("".join(r).rstrip() for r in self.g).rstrip("\n")


def sequence(participants, steps, col_width=None, margin=0):
    """Render a sequence diagram.

    participants: list of names shown in header boxes.
    steps: list of tuples:
        (src_index, dst_index, "label")  message arrow
        ("note", index, "text")          note next to a lifeline
    """
    boxw = col_width or (max(len(p) for p in participants) + 4)
    n = len(participants)
    centers = [margin + i * (boxw + 2) + boxw // 2 for i in range(n)]
    width = margin + n * (boxw + 2)
    for step in steps:
        if step[0] == "note":
            width = max(width, centers[step[1]] + 4 + len(step[2]))
        else:
            width = max(width, centers[min(step[0], step[1])] + 2 + len(step[2]))
    height = 3 + 2 * len(steps) + 1
    g = Grid(width + 2, height)
    for i, p in enumerate(participants):
        x = margin + i * (boxw + 2)
        g.box(x, 0, boxw, 3, [p.center(boxw - 2)])
    for c in centers:
        g.vline(c, 3, height - 1)
    row = 3
    for step in steps:
        if step[0] == "note":
            _, idx, text = step
            g.put(centers[idx] + 2, row + 1, "[" + text + "]")
        else:
            a, b, label = step
            ca, cb = centers[a], centers[b]
            if ca < cb:
                g.hline(row + 1, ca + 1, cb - 2)
                g.put(cb - 1, row + 1, ">")
                g.put(ca + 2, row, label)
            else:
                g.hline(row + 1, cb + 2, ca - 1)
                g.put(cb + 1, row + 1, "<")
                g.put(cb + 2, row, label)
        row += 2
    return g.render()
