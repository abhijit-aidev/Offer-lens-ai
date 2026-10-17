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
        Returns (success: bool, message: str) with crystal-clear diagnostics.
        """
        target_uri = uri or Neo4jConfig.get_uri()
        target_user = username or Neo4jConfig.get_username()
        target_pass = password or Neo4jConfig.get_password()

        temp_driver = None
        try:
            temp_driver = GraphDatabase.driver(
                target_uri,
                auth=(target_user, target_pass),
                connection_timeout=3.0,
            )
            # Verify connectivity by fetching server info
            server_info = temp_driver.get_server_info()
            return True, f"Connected to Neo4j ({server_info.agent}) at {target_uri}"
        except AuthError as e:
            return False, f"Authentication Failed: Invalid username or password for user '{target_user}'. ({e})"
        except ServiceUnavailable as e:
            if "localhost" in target_uri or "127.0.0.1" in target_uri:
                return (
                    False,
                    f"No active Neo4j service detected at {target_uri} (Connection Refused). "
                    f"A local Neo4j server is not running on this machine. "
                    f"To enable live graph features, connect to a free Neo4j AuraDB cloud instance "
                    f"or start a local Neo4j instance.",
                )
            return (
                False,
                f"Neo4j Service Unavailable at {target_uri}. "
                f"The host is unreachable. Please verify network access and routing.",
            )
        except ConfigurationError as e:
            return False, f"Configuration Error: {e}"
        except Exception as e:
            return False, f"Connection Failed: {type(e).__name__} ({str(e)})"
        finally:
            if temp_driver:
                try:
                    temp_driver.close()
                except Exception:
                    pass

    @classmethod
    def get_diagnostics(
        cls,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> dict:
        """Returns structured diagnostic metadata for developer inspection."""
        target_uri = uri or Neo4jConfig.get_uri()
        target_user = username or Neo4jConfig.get_username()
        connected, msg = cls.test_connection(uri, username, password)
        return {
            "connected": connected,
            "target_uri": target_uri,
            "username": target_user,
            "message": msg,
            "is_local": "localhost" in target_uri or "127.0.0.1" in target_uri,
            "protocol": target_uri.split("://")[0] if "://" in target_uri else "bolt",
        }


    @classmethod
    def close(cls):
        """Close the active driver connection."""
        if cls._driver is not None:
            try:
                cls._driver.close()
            except Exception:
                pass
            cls._driver = None
