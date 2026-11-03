"""Package the built folder, rejecting user data and keeping secrets external."""

import argparse
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def package(folder: Path | None = None, destination: Path | None = None) -> Path:
    root = Path(__file__).resolve().parents[1]
    folder = folder or root / "dist" / "Nexo"
    if not (folder / "Nexo.exe").is_file():
        raise ValueError("Gere o executável com Nexo.spec antes de empacotar.")
    template = (root / ".env.example").read_text(encoding="utf-8-sig")
    template = re.sub(r"(?m)^([A-Z0-9_]*(?:API_KEY|TOKEN))=.*$", r"\1=", template)
    (folder / ".env.example").write_text(template, encoding="utf-8")
    (folder / "LEIA-ME.txt").write_text(
        "NEXO INVEST\n\nExtraia a pasta inteira e abra Nexo.exe. Mantenha _internal ao lado do EXE. Não exige Python.\n"
        "Apresentação: carteiras, caixa, orçamento, metas, alertas e mercado fictícios, disponíveis sem internet.\n"
        "Meu ambiente: seus registros e provedores de mercado reais.\n"
        "Dados: %LOCALAPPDATA%\\NexoInvest. O pacote não importa bancos do checkout.\n"
        "Gemini/mercado: crie .env ao lado do EXE com suas chaves; use .env.example como referência.\n"
        "O pacote não inclui credenciais. Variáveis de ambiente prevalecem.\n"
        "Fechar e reabrir preserva alterações. Atualizar a pasta do programa não apaga o banco local.\n"
        "Gemini exige chave, internet e autorização de envio do contexto. Não há chave no ZIP.\n"
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
    destination = destination or root / "dist" / "Nexo-Windows.zip"
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    print(package(args.folder, args.destination))
