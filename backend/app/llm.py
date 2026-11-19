import httpx

from app.config import settings
from app.errors import AppError

SYSTEM_PROMPT = (
    "Answer the question using ONLY the numbered sources below. "
    "After each claim, cite the source number in square brackets, like [1] or [2]. "
    "If the sources do not contain the answer, say you could not find it in the saved content. "
    "Keep the answer short."
)


def llm_is_configured():
    return bool(settings.llm_api_key or settings.gemini_api_key)


def ask_llm(question, source_texts):
    """Send the question and the retrieved chunks to an OpenAI-compatible chat API."""
    sources = "\n\n".join(f"[{number}] {text}" for number, text in enumerate(source_texts, start=1))
    if settings.use_gemini:
        api_key, base_url, model = settings.gemini_api_key, settings.gemini_base_url, settings.gemini_model
    else:
        api_key, base_url, model = settings.llm_api_key, settings.llm_base_url, settings.llm_model
    body = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"},
        ],
    }
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
        raise AppError(502, "llm_error", f"The language model request failed: {error}")
