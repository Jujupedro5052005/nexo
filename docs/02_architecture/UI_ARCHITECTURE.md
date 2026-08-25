# Arquitetura da interface

## Abordagem

A interface desktop será implementada em PySide6 seguindo a estrutura atual de
`src/nexo/ui/`. As pastas separam responsabilidades práticas, sem declarar MVC
ou MVVM rígido.

| Pasta | Papel esperado |
|---|---|
| `windows/` | Janelas e shell principal. |
| `pages/` | Áreas navegáveis como mercado, carteiras, detalhes, análises, alertas e configurações. |
| `widgets/` | Elementos visuais reutilizáveis. |
| `components/` | Composições de apresentação compartilhadas quando houver distinção útil de `widgets`. |
| `dialogs/` | Formulários e modais. |
| `viewmodels/` | Estado preparado para apresentação, se necessário. |
| `controllers/` | Coordenação de interações da UI, se a abordagem continuar útil. |
| `styles/` | Tema e estilos. |
| `resources/` | Ícones e imagens. |

Os nomes são orientativos. Pastas vazias não comprovam classes implementadas.
A fronteira entre `components` e `widgets`, assim como o uso efetivo de
controllers/viewmodels, será confirmada durante a UI sem duplicar papéis.

## Comunicação

`main.py` constrói repositórios, adaptadores e casos de uso e fornece à UI as
dependências necessárias.

```text
evento PySide6
  -> handler/controller curto
  -> caso de uso da Application
  -> resultado/modelo de apresentação
  -> atualização dos widgets
```

A UI não recebe sessão SQLAlchemy, não executa SQL ou HTTP e não reconstrói
posições. Widgets PySide6 não atravessam para Application ou Domain.

## Estado e atualização

Após criar ou alterar uma carteira ou registrar transação, a UI recarrega o
estado pelos casos de uso adequados. Ela não mantém uma segunda cópia financeira
mutável. A carteira selecionada deve estar explícita para que compras, vendas,
dashboard e análises usem o `portfolio_id` correto.

Não se exige event bus, estado global ou framework de injeção. Sinais locais do
PySide6 podem coordenar componentes visuais.

## Validação e mensagens

1. UI valida presença e conversão de campos.
2. Domain valida invariantes financeiras.
3. Application coordena o resultado da operação.
4. Infrastructure traduz falhas técnicas.
5. UI apresenta mensagens claras sem SQL, stack trace ou dados sensíveis.

Chamadas de rede futuras não podem bloquear a thread da interface; a estratégia
assíncrona será escolhida quando a integração for implementada.

## Testes

Casos de uso falsos podem ser fornecidos aos componentes para testar submissão,
seleção de carteira, mensagens e estados vazios. Fluxos críticos também devem
ser validados manualmente no Windows. Consulte
[`TESTING.md`](../04_development/TESTING.md).
