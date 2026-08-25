# Padrões de código

- usar nomes em inglês no código e nomes explícitos;
- aplicar type hints em interfaces públicas e regras relevantes;
- manter classes e funções coesas, com responsabilidade clara;
- preferir composição; usar herança somente para especialização real;
- evitar duplicação de regras e números mágicos;
- usar `Decimal`, nunca `float`, para valores monetários no domínio;
- manter Domain sem PySide6, SQLAlchemy, SQLite e HTTP;
- manter SQL, ORM e integrações externas em Infrastructure;
- manter cálculos financeiros em Domain ou `calculations`, nunca na UI;
- ordenar imports em biblioteca padrão, terceiros e módulos locais;
- documentar decisões não triviais e atualizar o ADR quando a decisão mudar;
- não colocar chaves no código nem versionar `.env`;
- criar ou atualizar testes para regras e correções.

Não criar abstrações, interfaces, serviços ou subclasses apenas para demonstrar
um padrão. O menor desenho coerente com a arquitetura é preferível.
