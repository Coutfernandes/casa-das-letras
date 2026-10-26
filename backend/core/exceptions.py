"""Erros de regra de negócio, respondidos pela API com status 422."""


class BusinessRuleError(Exception):
    """
    Uma regra do leilão impediu a operação.

    `code` é estável (o front decide o texto e a tela a partir dele);
    `message` é uma explicação pronta em português; `data` traz valores úteis,
    como o lance mínimo atual.
    """

    status_code = 422

    def __init__(self, code: str, message: str, data: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}