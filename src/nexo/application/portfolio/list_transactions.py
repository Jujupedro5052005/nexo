from nexo.domain._validation import validate_identity
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import order_transactions


class ListTransactions:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    def execute(self, portfolio_id: int) -> list[Transaction]:
        validate_identity(portfolio_id, "portfolio_id")
        return order_transactions(self._repository.list_by_portfolio(portfolio_id))
