def column_stats(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    if not any(column in row for row in rows):
        raise KeyError(column)
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row.get(column, "")))
        except ValueError:
            continue
    if not values:
        raise ValueError("no numeric values")
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }
