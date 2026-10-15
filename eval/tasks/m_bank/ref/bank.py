from account import Account


def transfer(src: Account, dst: Account, amount: float) -> None:
    if src is dst:
        raise ValueError("cannot transfer to the same account")
    src.withdraw(amount)
    dst.deposit(amount)
