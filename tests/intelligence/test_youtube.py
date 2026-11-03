from datetime import timedelta

import httpx
import pytest

from nexo.domain.models.intelligence import IntelligenceError, utc_now
from nexo.infrastructure.intelligence.youtube import YouTubeCatalog

CHANNEL = "UC" + "a" * 22


def catalog(storage, mismatched=False):
    def respond(request):
        if request.url.path.endswith("channels"):
            assert request.url.params["forHandle"] == "@geracaodividendoss"
            body = {
                "items": [
                    {
                        "id": "different" if mismatched else CHANNEL,
                        "snippet": {"title": "Geração Dividendos"},
                        "contentDetails": {"relatedPlaylists": {"uploads": "UUtest"}},
                    }
                ]
            }
        elif request.url.path.endswith("playlistItems"):
            body = {"items": [{"contentDetails": {"videoId": "abcdefghijk"}}]}
        else:
            body = {
                "items": [
                    {
                        "id": "abcdefghijk",
                        "snippet": {
                            "channelId": CHANNEL,
                            "title": "Preço teto e dividendos",
                            "description": "Cenário de teste",
                            "publishedAt": "2026-01-01T00:00:00Z",
                        },
                        "contentDetails": {"duration": "PT10M"},
                        "status": {"privacyStatus": "public"},
                    }
                ]
            }
        return httpx.Response(200, json=body)

    return YouTubeCatalog(
        "test-placeholder",
        storage,
        httpx.Client(transport=httpx.MockTransport(respond)),
    )


def test_catalog_id_verification_metadata_dedup_and_permissions(storage):
    c = catalog(storage)
    identities = c.catalog("@geracaodividendoss", CHANNEL)
    assert identities == ("youtube_abcdefghijk",)
    c.catalog("@geracaodividendoss", CHANNEL)
    assert len(storage.documents()) == 1
    doc = storage.documents()[0]
    assert doc["duration"] == "PT10M" and doc["priority"] > 0
    assert not doc["authorized"]
    with pytest.raises(IntelligenceError):
        c.authorize(identities[0], " ")
    c.authorize(identities[0], "Autorização escrita do titular · fixture")
    c.catalog("@geracaodividendoss", CHANNEL)
    assert storage.documents()[0]["authorized"]
    c.close()


def test_wrong_similar_channel_is_rejected(storage):
    c = catalog(storage, mismatched=True)
    with pytest.raises(IntelligenceError, match="não corresponde"):
        c.catalog("@geracaodividendoss", CHANNEL)
    assert storage.documents() == []
    with pytest.raises(IntelligenceError, match="ID UC"):
        c.catalog("@geracaodividendoss", "unknown")
    with pytest.raises(IntelligenceError, match="1 a 10"):
        c.catalog("@geracaodividendoss", CHANNEL, limit=100)


def test_expiry_and_no_unauthorized_video_processing(workspace, storage):
    c = catalog(storage)
    identity = c.catalog("@geracaodividendoss", CHANNEL)[0]
    with pytest.raises(IntelligenceError, match="titular"):
        c.process(identity, workspace.orchestrator.provider)
    doc = storage.documents()[0]
    storage.put_document(
        {**doc, "fetched_at": (utc_now() - timedelta(days=30)).isoformat()}
    )
    c.purge_expired()
    assert storage.documents() == []


def test_processed_video_remains_pending_review_and_not_repeated(workspace, storage):
    c = catalog(storage)
    identity = c.catalog("@geracaodividendoss", CHANNEL)[0]
    c.authorize(identity, "Autorização fixture")
    method = storage.methodologies()[0]
    workspace.orchestrator.provider.extract = lambda uri, video: method
    extracted = c.process(identity, workspace.orchestrator.provider)
    assert extracted.review_status == "pending_review"
    assert (
        extracted.source_references[0].uri
        == "https://www.youtube.com/watch?v=abcdefghijk"
    )
    assert storage.documents()[0]["status"] == "processed"
    with pytest.raises(IntelligenceError, match="já processado"):
        c.process(identity, workspace.orchestrator.provider)
