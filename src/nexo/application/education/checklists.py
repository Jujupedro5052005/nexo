"""Original educational checklists based on the supplied reading; no risk score."""

from nexo.domain.errors import DomainValidationError

TOPICS = {
    "Fraudes, pirâmides e pig butchering": (
        (
            "Contato afetivo ou mensagem inesperada levou à oferta",
            "Separe a relação pessoal da decisão financeira e confirme identidade por canal independente.",
        ),
        (
            "Prometem retorno elevado, fixo ou sem risco",
            "Exija explicação verificável da origem do retorno; simular ganhos em uma tela não prova custódia ou lastro.",
        ),
        (
            "Preciso recrutar outras pessoas ou fazer novos depósitos para receber",
            "Investigue dependência de recrutamento/novos recursos; isso pode sinalizar esquema de pirâmide ou Ponzi.",
        ),
        (
            "Saque depende de taxa ou depósito adicional não previsto",
            "Verifique o contrato e o destinatário por fontes independentes antes de transferir mais valores.",
        ),
        (
            "Há pressão, exclusividade, segredo ou urgência",
            "Faça uma pausa e confronte a proposta com informações externas e uma pessoa de confiança.",
        ),
        (
            "Não confirmei registro, autorização, custódia e domínio oficial",
            "Consulte cadastros e alertas oficiais da CVM e, quando aplicável, do Banco Central. Registro não garante retorno nem valida qualquer oferta.",
        ),
        (
            "A empresa usa dívida para ampliar tesouraria em criptoativos",
            "Use o cenário de alavancagem: exposição, dívida, liquidez e prêmio sobre ativos podem amplificar perdas. Criptoativo e fraude são conceitos diferentes.",
        ),
    ),
    "ASG, governança e FOFA": (
        (
            "Não conheço riscos ambientais materiais",
            "Investigue exposição a licenças, clima, recursos naturais e passivos ambientais com fonte e data.",
        ),
        (
            "Não conheço riscos sociais materiais",
            "Confira relações trabalhistas, segurança, clientes, fornecedores e comunidades.",
        ),
        (
            "Não avaliei controlador, conflitos e direitos dos minoritários",
            "Examine governança, partes relacionadas, conselho, auditoria e incentivos.",
        ),
        (
            "Não distingui relato da empresa e evidência independente",
            "Registre origem, escopo e limitações dos dados ASG; um rating isolado não substitui a análise.",
        ),
        (
            "Não descrevi forças, fraquezas, oportunidades e ameaças",
            "Construa FOFA e compare fatores internos/externos com a tese financeira; evite um score automático sem metodologia.",
        ),
    ),
    "Planejamento, proteção e sucessão": (
        (
            "Reserva e liquidez não cobrem meu horizonte de necessidades",
            "Use reserva de emergência e orçamento; escolha a cobertura conforme sua situação, sem regra universal.",
        ),
        (
            "Não avaliei riscos pessoais e cobertura de seguros",
            "Relacione eventos, impacto financeiro, dependentes, coberturas e exclusões. Simulador não substitui avaliação contratual.",
        ),
        (
            "Não conferi beneficiários e documentação sucessória",
            "Revise documentos com profissional habilitado; regras dependem de família, ativos e jurisdição.",
        ),
        (
            "Usei alíquota ou benefício fiscal sem conferir a data e o produto",
            "Na calculadora tributária a alíquota é uma premissa manual, não regra atual automaticamente validada.",
        ),
        (
            "A aposentadoria supõe prazo, inflação ou retorno não examinados",
            "Use cenários reais e teste prazos maiores, custos e retorno menor; o prazo do cenário não limita a longevidade real.",
        ),
    ),
    "Adequação e vieses comportamentais": (
        (
            "Preciso do dinheiro antes do prazo ou liquidez do produto",
            "Compatibilize horizonte da meta com prazo, liquidez, carência e possibilidade de perdas.",
        ),
        (
            "Não compreendo estrutura, taxas ou possibilidade de perda",
            "Identifique o fluxo de caixa do instrumento e cenários de perda antes de simular uma operação.",
        ),
        (
            "Estou seguindo a multidão ou tentando recuperar uma perda",
            "Revise a tese sem ancoragem, custo irrecuperável ou aversão à perda; considere cenários contrários.",
        ),
        (
            "Concentração ou alavancagem excedem minha tolerância",
            "Consulte concentração e estresse; não confunda VaR com limite absoluto de perda.",
        ),
    ),
}


def findings(topic: str, selected: tuple[int, ...]) -> tuple[str, ...]:
    if topic not in TOPICS or any(i < 0 or i >= len(TOPICS[topic]) for i in selected):
        raise DomainValidationError("Checklist inválido.")
    if not selected:
        return (
            "Nenhum ponto foi assinalado. Isso não confirma legitimidade, adequação ou ausência de risco; os dados não foram verificados automaticamente.",
        )
    return tuple(TOPICS[topic][i][1] for i in dict.fromkeys(selected))
