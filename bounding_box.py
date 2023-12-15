
from ball import Ball
from interval import MultiInterval, SimpleInterval


class BoundingBox:
    def __init__(self, x_range: SimpleInterval, y_range: SimpleInterval):
        self.x_range = x_range
        self.y_range = y_range

    def times_inside(self, ball: Ball) -> MultiInterval | None:
        # find when ball enters/exits range
        rpos = SimpleInterval(0, 100)  # positive real
        x_t_ranges = []
        x_min_colls = (
            ball.bahn.x - (self.x_range.min - ball.radius)).find_roots(rpos, do_numeric=True)
        x_max_colls = (
            ball.bahn.x - (self.x_range.max + ball.radius)).find_roots(rpos, do_numeric=True)

        x0 = ball.pos_0.x
        x_colls = x_min_colls + x_max_colls  # .sort()
        #x_colls.append(float("inf"))
        x_colls.sort()
        if x_colls is None or len(x_colls) == 0:
            return None
        prev_t = 0

        if not self.x_range.check(x0):
            prev_t = x_colls.pop(0)
        for (i, t) in enumerate(x_colls):
            if i % 2 == 0:
                x_t_ranges.append(SimpleInterval(prev_t, t))
                # prev_t = None
            else:
                prev_t = t
        # if prev_t is not None:
        #     raise ValueError("Hmmmmm, sollte nicht passien")
        # x_t_ranges.append(Range(prev_t, self.x_range.max))

        y_min_colls = (
            ball.bahn.y - (self.y_range.min - ball.radius)).find_roots(rpos, do_numeric=True)
        y_max_colls = (
            ball.bahn.y - (self.y_range.max + ball.radius)).find_roots(rpos, do_numeric=True)

        y_colls = y_min_colls + y_max_colls
        y_colls.sort()
        y_colls.append(float("inf"))
        y0 = ball.pos_0.y

        prev_t = 0
        if not self.y_range.check(y0) and len(y_colls) > 0:
            prev_t = y_colls.pop(0)
        t_ranges = []
        x_rang_i = 0

        for (i, t) in enumerate(y_colls):
            if i % 2 == 0:
                y_range = SimpleInterval(prev_t, t)
                # x_i = 0
                while x_rang_i < len(x_t_ranges):
                    intersect = y_range.intersect(x_t_ranges[x_rang_i])
                    if intersect is None:
                        break
                    t_ranges.append(intersect)
                    x_rang_i += 1

                # prev_t = None
            else:
                prev_t = t
        multi_range = MultiInterval(t_ranges)  # anderen name wählen
        return multi_range