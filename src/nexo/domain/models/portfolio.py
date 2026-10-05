from dataclasses import dataclass


@dataclass(frozen=True, slots=True, eq=False)
class Portfolio:
    """A portfolio's identity and validated structural data."""

    name: str
    id: int | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Informe o nome da carteira.")
        if self.id is not None and (type(self.id) is not int or self.id <= 0):
            raise ValueError("O identificador da carteira deve ser um inteiro positivo.")
        object.__setattr__(self, "name", name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Portfolio):
            return NotImplemented
        if self.id is None or other.id is None:
            return self is other
        return self.id == other.id

    def __hash__(self) -> int:
        return object.__hash__(self) if self.id is None else hash(self.id)
