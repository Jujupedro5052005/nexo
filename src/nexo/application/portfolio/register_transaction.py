from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.models.transaction import Transaction


class RegisterTransaction:
    """Validate the entire candidate ledger before committing a new entry."""

    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    def execute(self, transaction: Transaction) -> Transaction:
        if transaction.id is not None:
            raise DomainValidationError("Informe uma movimentação nova, sem ID.")
        return self._repository.add_validated(transaction)
