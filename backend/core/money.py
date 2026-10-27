"""Valores em centavos escritos como se lê no Brasil."""


def format_brl(cents: int) -> str:
    """125000 → "R$ 1.250,00". Só com inteiros, sem arredondamento."""
    sign = "-" if cents < 0 else ""
    reais, centavos = divmod(abs(cents), 100)
    return f"{sign}R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"
