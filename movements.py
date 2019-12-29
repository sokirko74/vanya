def check_fuzzy_increase(integers):
    if len(integers) == 0:
        return True
    max_v = integers[0]
    for v in integers:
        if v > max_v:
            max_v = v
        elif max_v - v > 10:
            return False
    return True


def detect_hump(integers):
    if len(integers) < 3:
        return 0
    max_value = max(integers)
    max_index = [i for i,v in enumerate(integers) if v == max_value][0]
    if max_index == 0 or max_index == len(integers) - 1:
        return 0
    rise = integers[0:max_index]
    if max_value - min(rise) < 10   or not check_fuzzy_increase(rise):
        return 0
    slope = integers[max_index:]
    if max_value - min(slope) < 10 or not check_fuzzy_increase([-x for x in slope]):
        return 0

    return max_value - max((min(slope),min(rise)))


def detect_movements(points):
    movements = dict()
    v = detect_hump([y for (x, y) in points])
    if v > 0:
        movements["down"] = v
    v = detect_hump([-y for (x, y) in points])
    if v > 0:
        movements["up"] = v
    v = detect_hump([x for (x, y) in points])
    if v > 0:
        movements["right"] = v
    v = detect_hump([-x for (x, y) in points])
    if v > 0:
        movements["left"] = v
    return movements
