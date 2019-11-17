from enum import Enum


class KillType(Enum):
    NONE = 0
    CURRENT = 1
    ALL = 2

    def __bool__(self):
        return self != KillType.NONE

    # Python2 compatibility
    __nonzero__ = __bool__
