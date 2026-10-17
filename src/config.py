"""
Configuration loader for OfferLens AI using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Path to project root and .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables from .env file if it exists
load_dotenv(dotenv_path=ENV_PATH, override=False)


class Neo4jConfig:
    @staticmethod
    def get_uri() -> str:
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")

    @staticmethod
    def get_username() -> str:
        return os.getenv("NEO4J_USERNAME", "neo4j")

    @staticmethod
    def get_password() -> str:
        return os.getenv("NEO4J_PASSWORD", "password")

    @staticmethod
    def get_database() -> str:
        return os.getenv("NEO4J_DATABASE", "neo4j")

    @classmethod
    def as_dict(cls) -> dict:
        return {
            "uri": cls.get_uri(),
            "username": cls.get_username(),
            "database": cls.get_database(),
            # password omitted for safety
        }
