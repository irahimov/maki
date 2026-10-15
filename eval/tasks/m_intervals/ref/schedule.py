from intervals import merge_intervals


def free_slots(
    busy: list[tuple[int, int]], day_start: int, day_end: int
) -> list[tuple[int, int]]:
    if day_start >= day_end:
        raise ValueError("day_start must be before day_end")
    free: list[tuple[int, int]] = []
    cur = day_start
    for start, end in merge_intervals(busy):
        if end <= cur:
            continue
        if start > cur:
            free.append((cur, min(start, day_end)))
        cur = max(cur, end)
        if cur >= day_end:
            break
    if cur < day_end:
        free.append((cur, day_end))
    return free
