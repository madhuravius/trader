import math


def compute_distance(x1: int, x2: int, y1: int, y2: int) -> int:
    """
    Computes distance between two points. Translates result to int
    """
    return int(math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2)))
