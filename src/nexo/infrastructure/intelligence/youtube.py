"""Official metadata API only. No video downloads, cookies or transcript scraping."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from nexo.core.cancellation import check_cancelled
from nexo.domain.interfaces.intelligence import IntelligenceProvider
from nexo.domain.models.intelligence import (
    IntelligenceError,
    Methodology,
    SourceReference,
    utc_now,
)
from nexo.infrastructure.intelligence.storage import SqliteIntelligenceStorage


class YouTubeCatalog:
    def __init__(
        self,
        key: str,
        storage: SqliteIntelligenceStorage,
        client: httpx.Client | None = None,
    ) -> None:
        self.key, self.storage = key, storage
        self.client = client or httpx.Client(timeout=15)

    def _get(self, resource: str, **params: Any) -> dict[str, Any]:
        if not self.key:
            raise IntelligenceError(
                "Configure YOUTUBE_API_KEY para catalogar pela API oficial."
            )
        check_cancelled()
        try:
            response = self.client.get(
                f"https://www.googleapis.com/youtube/v3/{resource}",
                params={"key": self.key, **params},
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("Invalid response")
            return body
        except (httpx.HTTPError, ValueError, TypeError):
            raise IntelligenceError(
                "YouTube Data API indisponível, sem permissão ou com cota esgotada."
            ) from None

    def confirm_channel(self, handle: str, expected_id: str) -> dict[str, Any]:
        """Caller must independently confirm identity, never resolve by similar title."""
        if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", expected_id):
            raise IntelligenceError(
                "Informe o ID UC oficial confirmado; nomes semelhantes não são suficientes."
            )
        items = self._get(
            "channels", part="snippet,contentDetails", forHandle=handle
        ).get("items", [])
        if len(items) != 1 or items[0].get("id") != expected_id:
            raise IntelligenceError(
                "O handle não corresponde ao ID confirmado. Catálogo não iniciado."
            )
        return dict(items[0])

    def purge_expired(self) -> None:
        cutoff = utc_now() - timedelta(days=29)
        for doc in self.storage.documents():
            if (
                doc.get("kind") == "youtube"
                and datetime.fromisoformat(doc["fetched_at"]) < cutoff
            ):
                self.storage.delete_document(doc["id"])

    def catalog(
        self, handle: str, expected_id: str, *, limit: int = 5
    ) -> tuple[str, ...]:
        if not 1 <= limit <= 10:
            raise IntelligenceError("Lotes de catálogo permitem 1 a 10 vídeos.")
        self.purge_expired()
        channel = self.confirm_channel(handle, expected_id)
        playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        page = self._get(
            "playlistItems",
            part="contentDetails",
            playlistId=playlist,
            maxResults=limit,
        )
        ids = [item["contentDetails"]["videoId"] for item in page.get("items", [])]
        if not ids:
            return ()
        videos = self._get(
            "videos", part="snippet,contentDetails,status", id=",".join(ids)
        ).get("items", [])
        existing = {d["id"]: d for d in self.storage.documents()}
        result = []
        for item in videos:
            if (
                item.get("status", {}).get("privacyStatus") != "public"
                or item["snippet"].get("channelId") != expected_id
            ):
                continue
            identity = "youtube_" + item["id"]
            snippet = item["snippet"]
            text = (snippet["title"] + " " + snippet.get("description", "")).casefold()
            priority = sum(
                term in text
                for term in (
                    "preço teto",
                    "dividend",
                    "banco",
                    "segur",
                    "fii",
                    "valuation",
                    "indicador",
                )
            )
            previous = existing.get(identity, {})
            self.storage.put_document(
                {
                    "id": identity,
                    "kind": "youtube",
                    "channel_id": expected_id,
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "published_at": snippet["publishedAt"],
                    "duration": item.get("contentDetails", {}).get("duration"),
                    "uri": "https://www.youtube.com/watch?v=" + item["id"],
                    "priority": priority,
                    "status": previous.get("status", "cataloged"),
                    "authorized": previous.get("authorized", False),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            result.append(identity)
        return tuple(result)

    def authorize(self, identity: str, permission_reference: str) -> None:
        if not permission_reference.strip():
            raise IntelligenceError("Registre a referência à autorização do titular.")
        doc = next(
            d
            for d in self.storage.documents()
            if d["id"] == identity and d["kind"] == "youtube"
        )
        self.storage.put_document(
            {
                **doc,
                "authorized": True,
                "permission_reference": permission_reference,
                "status": "selected",
            }
        )

    def close(self) -> None:
        self.client.close()

    def process(self, identity: str, provider: IntelligenceProvider) -> Methodology:
        self.purge_expired()
        doc = next(
            d
            for d in self.storage.documents()
            if d["id"] == identity and d.get("kind") == "youtube"
        )
        if not doc.get("authorized") or not doc.get("permission_reference"):
            raise IntelligenceError(
                "Registre autorização do titular antes de processar o vídeo."
            )
        if doc.get("status") == "processed":
            raise IntelligenceError(
                "Vídeo já processado. Nenhuma nova chamada foi realizada."
            )
        self.storage.put_document({**doc, "status": "processing"})
        try:
            extracted = provider.extract(doc["uri"], video=True)
            identity_method = "video_" + extracted.methodology_id[:50]
            version = (
                max(
                    (
                        m.version
                        for m in self.storage.methodologies()
                        if m.methodology_id == identity_method
                    ),
                    default=0,
                )
                + 1
            )
            method = extracted.model_copy(
                update={
                    "methodology_id": identity_method,
                    "version": version,
                    "review_status": "pending_review",
                    "reviewed_by": None,
                    "source_references": (
                        SourceReference(title=doc["title"], uri=doc["uri"]),
                        *extracted.source_references,
                    ),
                }
            )
            self.storage.save_methodology(method)
            self.storage.put_document(
                {
                    **doc,
                    "status": "processed",
                    "methodology_id": identity_method,
                    "methodology_version": version,
                }
            )
            return method
        except Exception:
            self.storage.put_document({**doc, "status": "failed"})
            raise
