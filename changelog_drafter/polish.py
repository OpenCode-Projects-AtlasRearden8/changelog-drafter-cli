"""Optional polish pass through an OpenAI-compatible endpoint.

Defaults to a local Ollama server (http://localhost:11434/v1). No API key,
no token, no auth header is ever sent — if you point at a hosted gateway that
requires a key, that's on you to proxy; this tool stays key-free by design.
"""

import json
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5"
DEFAULT_TIMEOUT = 30

SYSTEM_PROMPT = (
    "You are a careful changelog editor. Rewrite each changelog bullet into one "
    "clear, human sentence. Keep the exact meaning and truth of the original "
    "bullet; never invent features or fixes. Keep the same number of bullets. "
    "Output exactly one line per bullet, in the same order, with no numbering, "
    "no markdown bullets, and no extra commentary."
)


def polish_bullets(
    base_url: str,
    model: str,
    bullets: list,
    timeout: int = DEFAULT_TIMEOUT,
):
    """Return polished bullets, or None when the endpoint is unavailable.

    Never raises; a failed polish is a graceful no-op back to the local draft.
    """
    url = base_url.rstrip("/") + "/chat/completions"
    user_prompt = "\n".join(f"- {b}" for b in bullets)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    lines = [
        ln.strip().lstrip("-*• ").strip()
        for ln in content.splitlines()
        if ln.strip()
    ]
    lines = [ln for ln in lines if ln]
    if len(lines) != len(bullets):
        return None
    return lines
