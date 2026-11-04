"""Assemble the complete academic delivery using the existing bundle guard."""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from package_windows import _validate_files, package
from verify_final_bundle import verify

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-final-20261104"


def source_files() -> list[Path]:
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    files = []
    for name in names:
        path = ROOT / name
        if not name or not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError(f"Link simbólico não permitido: {name}")
        if any(p.lower() in {".git", ".venv", "__pycache__", "dist", "build", "tmp", "temp", "data", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for p in path.relative_to(ROOT).parts):
            continue
        lower = path.name.lower()
        if lower.startswith(".env") and lower != ".env.example":
            continue
        if re.search(r"\.(db|sqlite|sqlite3|log|pyc|bak|tmp)(?:-(wal|shm|journal))?$", lower):
            continue
        files.append(path)
    return sorted(set(files))


def main() -> Path:
    folder = ROOT / "dist/Nexo"
    verify(folder)
    # Reuse secret/data validation and generation of the application instructions.
    intermediate = package(folder, ROOT / "tmp/final-application.zip")
    intermediate.unlink()
    files = _validate_files(folder)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    sources = source_files()
    sheets = [p for p in sources if p.suffix.lower() in {".xlsx", ".xls", ".ods"}]
    smoke_path = ROOT / "deliverables/final_executable_smoke.json"
    smoke = json.loads(smoke_path.read_text(encoding="utf-8")) if smoke_path.exists() else {"status": "pendente"}
    readme = (
        "NEXO INVEST — ENTREGA FINAL\n\n"
        "Extraia a pasta inteira. Abra Aplicativo/Nexo.exe e mantenha _internal ao lado dele. Não exige Python, Chrome, Node ou servidor.\n"
        "A página Apresentação funciona offline. Contingência: abra Apresentacao/Nexo_Apresentacao.html no navegador; o PDF também acompanha a entrega.\n"
        "Apresentação (modo de dados) usa carteiras e operações de exemplo; Meu ambiente usa seus registros. Ambos consultam os provedores reais de mercado, sujeitos a rede/cobertura. Não há mercado inventado no aplicativo.\n"
        "Dados graváveis: %LOCALAPPDATA%/NexoInvest (ou NEXO_DATA_DIR absoluto). Atualizar a pasta do programa não apaga o banco local. Bancos pessoais não acompanham esta entrega; o próprio aplicativo cria os exemplos.\n"
        "Configurações opcionais: copie .env.example para .env ao lado do EXE e configure mercado/IA externamente. Nenhuma credencial é fornecida. Gemini depende de chave e consentimento; apresentação não usa IA.\n"
        "Projeto/ contém fontes, testes, documentação, scripts e requisitos. Instalação de desenvolvimento: veja README.md.\n"
        f"Origem: commit {commit}, acrescido das alterações locais desta entrega; versão {VERSION}.\n"
        f"Gerado em {datetime.now().astimezone().isoformat()}.\n"
        f"Smoke Windows da cópia extraída: {json.dumps(smoke, ensure_ascii=False)}\n"
        + ("Planilhas presentes: " + ", ".join(str(p.relative_to(ROOT)) for p in sheets) if sheets else "PENDÊNCIA: planilha oficial de avaliação não encontrada no checkout nem no kit fornecido; solicitar ao professor e anexar antes da entrega.")
        + "\nÍcone de atalho antigo fixado pode permanecer em cache no Windows. Nenhuma configuração pessoal foi removida.\n"
    )
    destination = ROOT / "dist/Nexo-Entrega-Final.zip"
    temporary = destination.with_suffix(".zip.tmp")
    prefix = "Nexo-Entrega-Final/"
    with ZipFile(temporary, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, prefix + "Aplicativo/" + path.relative_to(folder).as_posix())
        for path in sources:
            archive.write(path, prefix + "Projeto/" + path.relative_to(ROOT).as_posix())
        for path in (ROOT / "src/nexo/resources/presentation").iterdir():
            archive.write(path, prefix + "Apresentacao/" + path.name)
        archive.writestr(prefix + "LEIA-ME-ENTREGA.txt", readme)
    temporary.replace(destination)
    print(destination)
    return destination


if __name__ == "__main__":
    main()
