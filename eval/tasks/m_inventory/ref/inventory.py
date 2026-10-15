class Inventory:
    def __init__(self) -> None:
        self._stock: dict[str, int] = {}

    def add(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def remove(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        if sku not in self._stock:
            raise ValueError("unknown sku")
        if self._stock[sku] < qty:
            raise ValueError("insufficient stock")
        self._stock[sku] -= qty

    def stock(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def low_stock(self, threshold: int) -> list[str]:
        return sorted(s for s, q in self._stock.items() if q < threshold)
