import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    PROJECT_NAME: str = "EcoRefactor"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY.strip())


settings = Settings()
