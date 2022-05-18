import math

values_range = 2 * math.pi


def radian_to_orientation(radian: float, shift: float = 0) -> int:
    radian += shift
    radian = pi_modulo(radian)
    percent = (radian + math.pi) / values_range
    mult = percent * 16
    rounded = round(mult)

    return min(15, max(0, rounded))


def pi_modulo(radian: float) -> float:
    while radian > math.pi:
        radian -= 2 * math.pi
    while radian < -math.pi:
        radian += 2 * math.pi
    return radian
