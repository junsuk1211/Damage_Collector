"""바닥에 놓인 상자와 캐릭터의 수평 충돌."""


def stop_at_boxes(x, next_x, feet, half_width, boxes):
    for left, right, top in boxes:
        if feet >= top:
            continue
        if x <= left - half_width < next_x:
            next_x = left - half_width
        elif next_x < right + half_width <= x:
            next_x = right + half_width
    return next_x
