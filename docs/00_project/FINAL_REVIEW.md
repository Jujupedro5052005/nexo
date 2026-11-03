# Revisão final para entrega — 03/11/2026

## Atualização após integrar master

A master avançou para `b09f0371d557e82f123ce540765275ffcfd326c1`, com mercado
online real nos dois modos. A resolução preserva essa mudança: o isolamento
com preços fictícios descrito na revisão original abaixo foi substituído.
`PresentationMarketData` fica apenas em `tests/presentation_market.py`.
O teste de composição foi substituído na master por `test_delivery_market_modes`,
que verifica os dois ambientes com disponibilidade e indisponibilidade de mercado.
Mantidos o empacotamento, a renomeação do teste de persistência e a documentação
acadêmica; roteiro/checklist refletem o comportamento online atual.

## Registro da revisão original (anterior à atualização)

Base revisada: `master`, commit `a66c7d4e5767a7d2e5c64b1d4e86346f1ebf2797`.
Fontes acadêmicas: orientações Projeto Semestral fornecidas nesta revisão,
proposta revisada anexada e instruções finais de apresentação/entrega.

## Parecer

O núcleo tem evidências de Python/POO, interface PySide6, gráficos funcionais,
persistência SQLite, reconstrução de posições, compra/venda e múltiplos
provedores. Os riscos mais imediatos são coerência entre documentação e código,
reprodutibilidade da demonstração e montagem dos arquivos finais. Não há ganho
acadêmico em ampliar a IA antes de demonstrar e explicar esse núcleo.

Isto é uma avaliação técnica, não uma nota atribuída pelo professor. O aceite
no Windows alvo e o ensaio pelo autor continuam necessários.

## Inconsistências encontradas e tratamento

| Prioridade | Constatação reproduzida / evidência | Tratamento nesta revisão |
|---|---|---|
| Alta | O modo Apresentação criava `ProviderServices` antes de substituir o mercado pelo provedor fictício. A abertura real falhou no httpx devido a proxy SOCKS sem dependência opcional, embora a demo não precisasse de HTTP. | A composição demo não instancia clientes reais. Diagnóstico identifica apresentação local; teste de conexão externa desabilitado nesse modo. Meu ambiente conserva seus provedores. |
| Alta | `package_windows.py` aceitava `.env.local` e `nexo.db-wal`, comprovado com arquivos fictícios em pasta temporária. | Recusa variantes privadas de `.env`, bancos/sidecars, contadores e symlinks antes de alterar o bundle. |
| Média | O empacotador aceitava apenas um EXE sem `_internal`, saída dentro do bundle e falhava para destino em diretório novo. | Exige `_internal`, recusa ZIP dentro da origem e prepara diretório de destino. Isso valida a estrutura mínima, não a integridade de DLLs ou o executável Windows. |
| Média | O comando do README falhava na coleta: dois `test_professor_delivery.py` eram importados com o mesmo nome. | Teste de persistência renomeado e comando atualizado; nenhum teste foi removido. |
| Média | Escopo prometia renomear/remover carteiras; `PortfolioRepository` possui apenas `add/list_all` e a UI oferece criação/seleção. | Escopo e RF-001 registram a implementação parcial; manutenção individual fica no TODO. Evitada inclusão apressada de exclusão do histórico. |
| Média | A proposta conceitual mostra Portfolio contendo posições; a classe real contém ID/nome, e serviços reconstroem o estado. | Roteiro explica explicitamente a diferença e usa composição Position/Asset e injeção de serviços como evidências reais. |
| Média | Checklist genérico não incluía planilha de avaliação nem distinguia código completo de executável. | Checklist específico de arquivos, exportação de código versionado e pendência da planilha oficial. |
| Média | Roteiro anterior apenas percorria telas, sem tempos ou recortes de POO. | Roteiro de dez minutos com fluxo numérico conferível, diagrama, classes/métodos e limites. |
| Baixa | Subtítulo de Análises prometia dados reais também em Apresentação. | Texto neutro, coerente com ambos os ambientes. |

## Cobertura acadêmica observada

| Exigência | Evidência concreta | Limite de avaliação |
|---|---|---|
| Python e POO efetiva | Modelos imutáveis/validados, contratos ABC, providers intercambiáveis, repositories e casos de uso | Autor precisa explicar os recortes e decisões; quantidade de classes não comprova domínio |
| GUI Windows | PySide6, launcher, spec PyInstaller, scripts de pacote/smoke | Esta revisão executou a GUI offscreen no Linux; não certifica o EXE em Windows limpo |
| Elemento gráfico funcional | Gráficos de custo, concentração e resultados derivados das posições | Custo histórico não é patrimônio histórico de mercado |
| Integração com banco | Ledger persistido, chaves estrangeiras, replay antes da escrita e reabertura | Demo comprova SQLite; preços fictícios não comprovam API |
| API externa | Adaptadores Yahoo/brapi/bolsai/CVM, normalização, fontes e tratamento de falha | Sem autenticação/chamadas de mercado reais nesta revisão |
| Entrega e apresentação | Roteiro de 8–12 minutos e checklist específico | Planilha oficial e slides finais ainda precisam ser incluídos pelo autor |

## Validação desta revisão

- Instalação nova a partir de requirements e instalação editável concluídas em
  Python 3.12/Linux. Dependências sem lock podem divergir das do build Windows.
- Seleção inicial: **261 testes aprovados**, cobrindo domínio, aplicação,
  repositories SQLite, caixa/risco, IR parcial, entrega e empacotamento.
- Abertura real offscreen após isolar a composição demo: saída zero, caixa e
  patrimônio preenchidos; captura atual inspecionada. Essa execução não substitui
  validação nativa Windows, DPI nem aceite de serviços externos.
- Suíte comum bloqueia rede; nenhum preço externo/autenticação Gemini é dado
  como validado. Arquivos temporários e bancos isolados não integram o PR.

Regressão final: **44 testes aprovados** (72,31 s), incluindo composição dos
dois ambientes, rejeição de clientes reais na demo, persistência, pacote,
navegação e foco da IA. Ruff dos arquivos alterados, mypy dos três módulos de
produção afetados, compileall e diff-check aprovados. A seleção ampliada opcional
de UI foi interrompida sem conclusão e não é contabilizada como aprovação.
Não se afirma uma nova execução completa de todos os testes do repositório.

## Pendências antes da entrega

1. Obter e anexar a planilha oficial de avaliação: ela não foi localizada nos
   arquivos fornecidos nem no repositório. Não inventar pesos ou notas.
2. Ensaiar o fluxo de compra/venda e explicar os recortes de POO sem abrir o
   código inteiro. Usar prints atuais: capturas históricas podem mostrar cards
   vazios ou rótulos já alterados.
3. Congelar a versão, registrar o commit, gerar um novo executável Windows e
   validar o ZIP em outra máquina. O repositório não contém o EXE revisado.
4. Entregar a pasta completa do código, o executável, slides e planilha. A receita
   de empacotamento Windows não empacota automaticamente o código-fonte.
5. Congelar versões das dependências do ambiente Windows que efetivamente passar
   no aceite. Não gerar um lock Windows a partir deste ambiente Linux.

Evoluções posteriores: renomear/remover carteiras com política clara, correção
auditável de operações, acessibilidade e APIs opcionais autenticadas.
IR automático, DARF, envio de alertas externos e ordens reais não devem aparecer
como funcionalidades entregues. Ver [TODO](../../TODO.md).
