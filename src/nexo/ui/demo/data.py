"""Presentation-only dataset for the disconnected visual prototype."""

DEMO_NOTICE = "Dados demonstrativos"
PORTFOLIO_SERIES = [82, 84, 87, 86, 91, 95, 98, 103, 108, 112, 117, 125]
INVESTED_SERIES = [78, 80, 82, 85, 87, 90, 94, 98, 101, 105, 108, 111]
REFERENCE_SERIES = [80, 81, 83, 84, 87, 89, 91, 95, 98, 101, 105, 109]
ALLOCATION = [
    ("Renda variável", 34, "R$ 42.646,29", "#10C7C7"),
    ("Renda fixa", 25, "R$ 31.357,57", "#4D7CFF"),
    ("Fundos Imobiliários", 16, "R$ 20.068,84", "#8B6CFF"),
    ("Internacional", 12, "R$ 15.051,63", "#3DDC84"),
    ("Criptomoedas", 8, "R$ 10.034,42", "#FFB020"),
    ("Caixa", 5, "R$ 6.271,51", "#6E7D91"),
]
POSITIONS = [
    ("PETR4", "R$ 24.840,00", "19,8%", "+R$ 3.120,40"),
    ("VALE3", "R$ 18.620,50", "14,8%", "+R$ 1.870,20"),
    ("ITUB4", "R$ 15.480,90", "12,3%", "+R$ 980,75"),
    ("BOVA11", "R$ 12.950,00", "10,3%", "+R$ 720,10"),
    ("BBAS3", "R$ 9.870,40", "7,9%", "-R$ 185,30"),
]
PORTFOLIOS = [
    ("Longo Prazo", "R$ 125.430,28", "+12,42%", "14 ativos", "Agora"),
    ("Reserva", "R$ 38.200,00", "+8,91%", "5 ativos", "Hoje, 09:42"),
    ("Internacional", "R$ 24.870,50", "+6,30%", "7 ativos", "Ontem"),
]
ASSETS = [
    ("PETR4", "Petrobras PN", "Ação", "R$ 36,82", "+1,24%", "Sim"),
    ("VALE3", "Vale ON", "Ação", "R$ 61,40", "-0,48%", "Sim"),
    ("HGLG11", "CSHG Logística", "FII", "R$ 158,70", "+0,19%", "Não"),
    ("BOVA11", "iShares Ibovespa", "ETF", "R$ 127,34", "+0,82%", "Sim"),
    ("BTC", "Bitcoin", "Cripto", "R$ 342.810,00", "+2,91%", "Não"),
]
TRANSACTIONS = [
    ("08/09/2026", "Longo Prazo", "Compra", "PETR4", "100", "R$ 35,10", "R$ 3.510,00"),
    ("05/09/2026", "Reserva", "Aporte", "—", "—", "—", "R$ 2.500,00"),
    ("29/08/2026", "Longo Prazo", "Provento", "ITUB4", "—", "—", "R$ 184,20"),
    ("21/08/2026", "Internacional", "Compra", "IVVB11", "20", "R$ 312,40", "R$ 6.248,00"),
    ("12/08/2026", "Longo Prazo", "Venda", "VALE3", "15", "R$ 62,80", "R$ 942,00"),
]
GOALS = [
    ("Reserva de emergência", "Segurança", "R$ 27.000", "R$ 30.000", 90, "Dez/2026"),
    ("Viagem Europa", "Experiência", "R$ 8.400", "R$ 20.000", 42, "Jul/2027"),
    ("Entrada do imóvel", "Patrimônio", "R$ 34.500", "R$ 120.000", 29, "Dez/2029"),
]
ALERTS = [
    ("PETR4 abaixo de R$ 31,50", "Preço abaixo de", "Ativo", "Agora"),
    ("Reserva de emergência atingiu 90%", "Meta alcançada", "Ativo", "Há 2 h"),
    ("Carteira fora da alocação alvo", "Desvio superior a 5%", "Ativo", "Ontem"),
]
