from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator


class Interval(ABC):
    @abstractmethod
    def get_size(self) -> float:
        pass

    @abstractmethod
    def check(self, v: float) -> bool:
        pass

    @abstractmethod
    def step_through(self, n_steps: int) -> Iterator[float]:
        pass


class SimpleInterval(Interval):
    min: float
    max: float
    l_inclusive: bool
    r_inclusive: bool

    def __init__(self, min, max, l_inclusive=True, r_inclusive=True):
        if min > max:
            max, min = min, max
        self.min = min
        self.max = max
        self.l_inclusive = l_inclusive
        self.r_inclusive = r_inclusive

    def get_size(self):
        return self.max - self.min

    def restrict_max(self, new_max):
        # maybe it would be smarter to also have an option to change the inclusivity, but I currently dont see a reason for that
        return SimpleInterval(self.min, min(new_max, self.max), self.l_inclusive, self.r_inclusive)

    def restrict_min(self, new_min: float):
        return SimpleInterval(max(self.min, new_min), self.max, self.l_inclusive, self.r_inclusive)

    def check(self, v: float):
        return ((self.l_inclusive and v >= self.min) or (v > self.min)) and ((self.r_inclusive and v <= self.max) or (v < self.max))

    def step_through(self, n_steps: int) -> Iterator[float]:
        step_size = (self.max-self.min)/n_steps
        for i in range(n_steps):
            yield self.min+i*step_size

    def intersect(self, other: SimpleInterval):
        print(
            f"intersect range {{{self.min} to {self.max}}}, {{{other.min} to {other.max}}}")
        if self.min <= other.min:
            links = self
            rechts = other
        else:
            links = other
            rechts = self
        if links.max <= rechts.min:
            return None
        return SimpleInterval(rechts.min, min(links.max, rechts.max))


class MultiInterval(Interval):
    def __init__(self, ranges: List[Interval]):
        size = 0.0
        for range in ranges:
            size += range.get_size()
        self.size = size
        self.ranges = ranges

    def get_size(self) -> float:
        return self.size

    def step_through(self, n_steps) -> Iterator[float]:
        size_per_step = self.size / n_steps
        for range in self.ranges:
            n_steps = int(range.get_size()/size_per_step)
            for x in range.step_through(n_steps):
                # print(f"x:{x}")
                yield x
        # return StopIteration

        print("stepping through multirange")
        # return MultiRangeIter(self, n_steps)

    def check(self, v):
        for r in self.ranges:
            if r.check(v):
                return True
        return False
