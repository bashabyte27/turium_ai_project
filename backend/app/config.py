from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Everything can be overridden with environment variables or a .env file.
    db_path: str = "data/inbox.db"

    # chunking
    chunk_size: int = 800
    chunk_overlap: int = 100

    # how many chunks we pull in to answer a question
    top_k: int = 5

    # limits for what users can add
    max_note_chars: int = 50000
    max_page_bytes: int = 2000000
    fetch_timeout: float = 10

    # "local" runs a small model on your machine (no key needed)
    # "hash" is a tiny offline fallback, mainly for tests
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Leave llm_api_key empty to get quoted answers without any LLM.
    # Set it (and llm_base_url / llm_model) to use OpenAI, Ollama, Groq, etc.
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # Simplest option: set GEMINI_API_KEY and answers come from Google Gemini
    # (through its OpenAI-compatible endpoint). llm_api_key wins if both are set.
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    gemini_model: str = "gemini-flash-lite-latest"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def use_gemini(self):
        return bool(self.gemini_api_key) and not self.llm_api_key


settings = Settings()
