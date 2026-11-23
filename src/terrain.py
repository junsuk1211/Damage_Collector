"""바닥에 놓인 상자와 캐릭터의 수평 충돌."""

MELEE_HEIGHT = 56
MELEE_VERTICAL_REACH = 64


def melee_path_clear(x, feet, target_x, target_feet, boxes=()):
    if abs(target_feet - feet) > MELEE_VERTICAL_REACH:
        return False

    if x > target_x:
        x, target_x = target_x, x
        feet, target_feet = target_feet, feet
    for left, right, top in boxes:
        overlap_left, overlap_right = max(x, left), min(target_x, right)
        if overlap_left > overlap_right:
            continue
        if x == target_x:
            lowest_feet = min(feet, target_feet)
        else:
            slope = (target_feet - feet) / (target_x - x)
            lowest_feet = feet + slope * ((overlap_left if slope >= 0 else overlap_right) - x)
        if lowest_feet + MELEE_HEIGHT < top:
            return False
    return True


def stop_at_boxes(x, next_x, feet, half_width, boxes):
    for left, right, top in boxes:
        if feet >= top:
            continue
        if x <= left - half_width < next_x:
            next_x = left - half_width
        elif next_x < right + half_width <= x:
            next_x = right + half_width
    return next_x
