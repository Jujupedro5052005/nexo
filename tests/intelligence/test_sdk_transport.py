import json

import httpx
from google import genai
from google.genai import types

from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.providers import GeminiIntelligenceProvider


def test_real_sdk_http_serialization_without_network(workspace, storage):
    bodies = []

    def respond(request):
        assert request.url.path.endswith(":generateContent")
        bodies.append(json.loads(request.content))
        config = bodies[-1].get("generationConfig", {})
        if config.get("responseMimeType") == "application/json":
            text = storage.methodologies()[0].model_dump_json()
        else:
            text = "Resposta sintética do transporte de teste."
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"role": "model", "parts": [{"text": text}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {"totalTokenCount": 30},
            },
        )

    http = httpx.Client(transport=httpx.MockTransport(respond))
    client = genai.Client(
        api_key="only-test-placeholder",
        http_options=types.HttpOptions(
            httpx_client=http, retry_options=types.HttpRetryOptions(attempts=1)
        ),
    )
    provider = GeminiIntelligenceProvider(
        AISettings(api_key="placeholder"), storage, client
    )
    try:
        assert (
            provider.plan("Pergunta", workspace.orchestrator.tools.declarations()) == ()
        )
        assert (
            "parameters_json_schema" in bodies[0]["tools"][0]["functionDeclarations"][0]
        )
        assert provider.synthesize("Contexto")
        assert "tools" not in bodies[1]
        assert (
            provider.extract("Documento autorizado").review_status == "pending_review"
        )
        assert "responseSchema" in bodies[2]["generationConfig"]
        assert bodies[0]["systemInstruction"] != bodies[0]["contents"]
    finally:
        provider.close()
