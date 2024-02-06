from enum import Enum, auto

class CollDirection(Enum):
    """ Enum for collision direction
    ALLOW_ALL: from all directions
    ALLOW_FROM_INSIDE: coming from the center (inside)
    ALLOW_FROM_OUTSIDE: coming from the outside
    """
    ALLOW_ALL = auto()
    ALLOW_FROM_INSIDE = auto()
    ALLOW_FROM_OUTSIDE = auto()

    def __str__(self):
        return self.name