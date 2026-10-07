"""Reset only data/nexo_demo.db using existing application use cases; no network."""

from nexo.demo_dataset import DEMO_NOTICE, create_demo_dataset, demo_database_path


def main() -> int:
    summaries = create_demo_dataset()
    print(DEMO_NOTICE)
    print(f"Banco demo criado: {demo_database_path()}")
    for item in summaries:
        print(f"\n{item.name}\n  {item.assets} ativos\n  {item.transactions} movimentações")
        print(f"  Custo aberto: R$ {item.cost_basis:,.2f}")
        print(f"  Resultado realizado: R$ {item.realized_profit_loss:,.2f}")
    print(f"\nTotal: {sum(item.transactions for item in summaries)} movimentações")
    print(f"{sum(item.assets for item in summaries)} posições atuais")
    print("Período: abril/2024 a setembro/2026; cotações atuais não são seedadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
