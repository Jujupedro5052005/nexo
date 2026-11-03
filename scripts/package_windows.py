"""Package the built folder, rejecting user data and keeping secrets external."""

import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def package() -> Path:
    root = Path(__file__).resolve().parents[1]
    folder = root / "dist" / "Nexo"
    if not (folder / "Nexo.exe").is_file():
        raise ValueError("Gere o executável com Nexo.spec antes de empacotar.")
    template = (root / ".env.example").read_text(encoding="utf-8-sig")
    template = re.sub(r"(?m)^([A-Z0-9_]*(?:API_KEY|TOKEN))=.*$", r"\1=", template)
    (folder / ".env.example").write_text(template, encoding="utf-8")
    (folder / "LEIA-ME.txt").write_text(
        "NEXO INVEST\n\nAbra Nexo.exe e escolha Demo ou Normal. Mantenha a pasta _internal ao lado do EXE.\n"
        "Demo usa registros fictícios em banco separado. Normal preserva seus próprios registros.\n"
        "Dados: %LOCALAPPDATA%\\NexoInvest. O pacote não importa bancos do checkout.\n"
        "Gemini/mercado: crie .env ao lado do EXE com suas chaves; use .env.example como referência.\n"
        "O pacote não inclui credenciais. Variáveis de ambiente prevalecem.\n"
        "Sem internet: ledger, planejamento, metas e simuladores funcionam; não há preço fictício de fallback.\n"
        "IR é apoio parcial, com premissas manuais. Não gera declaração ou DARF.\n"
        "Código, documentação e limites: https://github.com/Jujupedro5052005/nexo\n",
        encoding="utf-8",
    )
    files = sorted(path for path in folder.rglob("*") if path.is_file())
    for path in files:
        if (
            path.name == ".env"
            or path.suffix in {".db", ".sqlite", ".sqlite3"}
            or path.name == "provider_usage.json"
        ):
            raise ValueError(
                "Remova dados/segredos da distribuição antes de empacotar."
            )
    destination = root / "dist" / "Nexo-Windows.zip"
    temporary = destination.with_suffix(".zip.tmp")
    try:
        with ZipFile(
            temporary, "w", compression=ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for path in files:
                archive.write(path, "Nexo/" + path.relative_to(folder).as_posix())
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


if __name__ == "__main__":
    print(package())
