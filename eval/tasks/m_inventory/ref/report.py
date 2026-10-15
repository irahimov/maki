from inventory import Inventory


def format_report(inv: Inventory) -> str:
    skus = [s for s in inv.low_stock(float("inf")) if inv.stock(s) > 0]
    lines = [f"{s}: {inv.stock(s)}" for s in skus]
    return "\n".join(lines) if lines else "(empty)"
