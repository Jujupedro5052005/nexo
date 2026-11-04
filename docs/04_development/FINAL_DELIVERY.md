# Entrega final — 04/11/2026

A apresentação aprovada é distribuída sem alteração em
`src/nexo/resources/presentation`. `PresentationPage` mantém uma instância de
WebEngine, carrega o HTML com `embedded=1` e pausa/retoma ao navegar. O perfil
efêmero bloqueia rede, arquivos diferentes do HTML, janelas e downloads.
Somente tour e tela cheia são aceitos como solicitações ao host; não há bridge
para dados, serviços financeiros ou comandos Python.

`PageId` centraliza os destinos. Apresentação é o destino 10; Configurações
passa a 11. Os modos de dados continuam independentes da página e usam os
provedores reais existentes. Nenhuma mudança no ledger, cálculos ou banco.

Ícones usam os arquivos aprovados; AppUserModelID estável `NexoInvest.Desktop`.
Windows 11 tenta DWM com HRESULT verificado, HWND e COLORREF tipados.
Windows 10 usa barra Qt com mover e redimensionar pelo sistema, controles,
duplo clique e restauração de estado ao sair da apresentação em tela cheia.
Referência: [DWMWINDOWATTRIBUTE](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute).
Atalhos previamente fixados podem manter ícone em cache; não são apagados.

Educação alinha conteúdo no topo, rotula tema e mantém cartão compacto,
checkboxes e orientações adjacentes; espaço excedente fica ao final.
O botão prepara a pergunta no copiloto sem enviá-la.

Build final: `python -m PyInstaller --clean --noconfirm Nexo.spec`. Limpar o cache
evita reutilização de módulos antigos no PYZ; conferir o código empacotado e o
smoke da extração. Os hooks oficiais de
QtWebEngineCore/Widgets incluem processo auxiliar, recursos, plugins e traduções;
o corpus de IA permanece incluído. Não se desabilita o sandbox Chromium.
Empacotamento: `python scripts/package_final.py`, reaproveitando as proteções
de `package_windows.py` e selecionando os fontes pelo Git (incluindo novos
arquivos não ignorados), sem dados pessoais, ambientes ou caches.

Destino: `dist/Nexo-Entrega-Final.zip`. O README registra versão, commit-base,
alterações locais e resultado do smoke. `scripts/smoke_final_windows.py` opera
a janela real da cópia extraída com dados temporários e budgets remotos zero;
`scripts/smoke_executable.py` verifica seletor e ambos os modos.

Planilha oficial de avaliação ausente no checkout e no kit fornecido. Não foi
criada uma substituta. Assinatura e validação em máquina Windows limpa continuam
fora da verificação local. Evidências finais em `deliverables/`.

Aceite concluído: [FINAL_WINDOWS_VALIDATION](../../deliverables/FINAL_WINDOWS_VALIDATION.md).
