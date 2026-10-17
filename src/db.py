"""
Neo4j Database Driver & Connection Manager.
"""

from typing import Optional, Tuple
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import (
    AuthError,
    ServiceUnavailable,
    ConfigurationError,
    Neo4jError,
)

from src.config import Neo4jConfig


class Neo4jConnection:
    _driver: Optional[Driver] = None

    @classmethod
    def get_driver(
        cls,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Driver:
        """
        Get or initialize the Neo4j driver singleton.
        Can optionally accept runtime overrides (e.g. from Streamlit UI).
        """
        target_uri = uri or Neo4jConfig.get_uri()
        target_user = username or Neo4jConfig.get_username()
        target_pass = password or Neo4jConfig.get_password()

        # If driver already exists and matches params, return it
        if cls._driver is not None:
            return cls._driver

        cls._driver = GraphDatabase.driver(
            target_uri,
            auth=(target_user, target_pass),
        )
        return cls._driver

    @classmethod
    def reset_driver(
        cls,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Driver:
        """Close existing driver and create a new one with given credentials."""
        cls.close()
        return cls.get_driver(uri, username, password)

    @classmethod
    def test_connection(
        cls,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Verify connectivity to Neo4j database.
        Returns (success: bool, message: str) with beginner-friendly diagnostics.
        """
        target_uri = uri or Neo4jConfig.get_uri()
        target_user = username or Neo4jConfig.get_username()
        target_pass = password or Neo4jConfig.get_password()

        temp_driver = None
        try:
            temp_driver = GraphDatabase.driver(
                target_uri,
                auth=(target_user, target_pass),
                connection_timeout=5.0,
            )
            # Verify connectivity by fetching server info
            server_info = temp_driver.get_server_info()
            return True, f"Connected successfully to Neo4j ({server_info.agent}) at {target_uri}"
        except AuthError as e:
            return False, f"Authentication Failed: Invalid username or password for {target_user}. ({e})"
        except ServiceUnavailable as e:
            return (
                False,
                f"Neo4j Service Unavailable at {target_uri}. "
                f"Ensure your Neo4j instance or AuraDB cloud cluster is active and reachable.",
            )
        except ConfigurationError as e:
            return False, f"Configuration Error: {e}"
        except Exception as e:
            return False, f"Connection Failed: {type(e).__name__} - {str(e)}"
        finally:
            if temp_driver:
                temp_driver.close()

    @classmethod
    def close(cls):
        """Close the active driver connection."""
        if cls._driver is not None:
            try:
                cls._driver.close()
            except Exception:
                pass
            cls._driver = None
