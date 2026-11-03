"""Explicit maintenance commands; no cloud operation runs just by starting the app."""

import argparse
import json
from pathlib import Path

from nexo.application.intelligence.knowledge_service import KnowledgeService
from nexo.application.intelligence.methodologies import builtin_methodologies
from nexo.core.paths import application_data_dir
from nexo.domain.models.intelligence import IntelligenceError
from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.knowledge import (
    GeminiFileSearchRetriever,
    LocalKnowledgeRetriever,
)
from nexo.infrastructure.intelligence.providers import (
    GeminiIntelligenceProvider,
    MockIntelligenceProvider,
)
from nexo.infrastructure.intelligence.storage import SqliteIntelligenceStorage
from nexo.infrastructure.intelligence.youtube import YouTubeCatalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="NEXO Intelligence · biblioteca e integrações explícitas"
    )
    parser.add_argument(
        "--database", type=Path, help="Banco da IA (nunca o banco de carteiras)"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("test-connection")
    sub.add_parser("list")
    for name in ("import-document", "import-methodology"):
        cmd = sub.add_parser(name)
        cmd.add_argument("path", type=Path)
        if name == "import-document":
            cmd.add_argument("--authorized", action="store_true")
    cmd = sub.add_parser("review")
    cmd.add_argument("identity")
    cmd.add_argument("version", type=int)
    cmd.add_argument("--reviewer", required=True)
    cmd.add_argument("--approve", action="store_true")
    for name in ("extract", "index", "delete-document", "process-video"):
        cmd = sub.add_parser(name)
        cmd.add_argument("identity")
        if name in {"extract", "process-video"}:
            cmd.add_argument("--allow-cloud", action="store_true")
        if name == "index":
            cmd.add_argument("--allow-paid-indexing", action="store_true")
    cmd = sub.add_parser("catalog-youtube")
    cmd.add_argument("--handle", default="@geracaodividendoss")
    cmd.add_argument("--confirmed-channel-id", required=True)
    cmd.add_argument("--limit", type=int, default=5)
    cmd = sub.add_parser("authorize-video")
    cmd.add_argument("identity")
    cmd.add_argument("--permission-reference", required=True)
    args = parser.parse_args(argv)
    settings = AISettings.from_environment()
    path = args.database or application_data_dir() / "nexo_intelligence.db"
    if path.name in {"nexo.db", "nexo_demo.db"}:
        parser.error("Selecione um banco dedicado à IA.")
    storage = SqliteIntelligenceStorage(path)
    existing = {(m.methodology_id, m.version) for m in storage.methodologies()}
    for method in builtin_methodologies():
        if (method.methodology_id, method.version) not in existing:
            storage.save_methodology(method)
    provider = (
        GeminiIntelligenceProvider(settings, storage)
        if settings.cloud
        else MockIntelligenceProvider()
    )
    service = KnowledgeService(storage, provider)
    catalog = YouTubeCatalog(settings.youtube_api_key, storage)
    try:
        result: object
        if args.command == "status":
            result = {
                "mode": "gemini" if settings.cloud else "offline",
                "key_configured": bool(settings.api_key),
                "model": settings.model,
                "usage": storage.usage(),
            }
        elif args.command == "test-connection":
            result = provider.test_connection()
        elif args.command == "list":
            result = {
                "documents": [
                    {k: v for k, v in d.items() if k != "text"}
                    for d in storage.documents()
                ],
                "methodologies": [
                    m.model_dump(mode="json") for m in storage.methodologies()
                ],
            }
        elif args.command == "import-document":
            result = LocalKnowledgeRetriever(storage).import_document(
                args.path, authorized=args.authorized
            )
        elif args.command == "import-methodology":
            result = service.import_methodology(args.path).model_dump(mode="json")
        elif args.command == "review":
            result = service.review(
                args.identity,
                args.version,
                approve=args.approve,
                reviewer=args.reviewer,
            ).model_dump(mode="json")
        elif args.command == "extract":
            if not args.allow_cloud:
                raise IntelligenceError(
                    "Use --allow-cloud para autorizar a extração pelo Gemini."
                )
            result = service.extract(args.identity).model_dump(mode="json")
        elif args.command in {"index", "delete-document"}:
            if (
                not isinstance(provider, GeminiIntelligenceProvider)
                or not settings.file_search_store
            ):
                if args.command == "delete-document":
                    doc = next(
                        d for d in storage.documents() if d["id"] == args.identity
                    )
                    if doc.get("remote_name") or doc.get("remote_operation"):
                        raise IntelligenceError(
                            "Configure o store original para remover o documento remoto primeiro."
                        )
                    storage.delete_document(args.identity)
                    result = "Documento local removido."
                else:
                    raise IntelligenceError(
                        "Configure Gemini e NEXO_AI_FILE_SEARCH_STORE."
                    )
            else:
                remote = GeminiFileSearchRetriever(
                    provider, storage, settings.file_search_store
                )
                if args.command == "index":
                    result = remote.index(
                        args.identity, allow_indexing=args.allow_paid_indexing
                    )
                else:
                    remote.delete(args.identity)
                    result = "Documento removido."
        elif args.command == "catalog-youtube":
            result = catalog.catalog(
                args.handle, args.confirmed_channel_id, limit=args.limit
            )
        elif args.command == "authorize-video":
            catalog.authorize(args.identity, args.permission_reference)
            result = "Autorização registrada."
        else:
            if not args.allow_cloud:
                raise IntelligenceError(
                    "Use --allow-cloud para autorizar a análise do vídeo selecionado."
                )
            result = catalog.process(args.identity, provider).model_dump(mode="json")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (IntelligenceError, OSError, ValueError, StopIteration):
        print(
            "Operação indisponível. Verifique autorização, configuração, ID/versão e limites locais. Segredos não são exibidos."
        )
        return 1
    finally:
        provider.close()
        catalog.close()


if __name__ == "__main__":
    raise SystemExit(main())
