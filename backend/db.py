import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, TransientError


class Database:
    """Thin wrapper around the CognoDB driver with connection-error handling."""

    def __init__(self):
        self._driver = None
        self._connect_error = None
        uri = os.getenv("COGNODB_URI")
        user = os.getenv("COGNODB_USER")
        password = os.getenv("COGNODB_PASS")

        if not uri or not user or not password:
            self._connect_error = "CognoDB credentials are missing from the environment."
            return

        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
        except AuthError:
            self._connect_error = "CognoDB rejected the username or password."
        except ServiceUnavailable:
            self._connect_error = "Could not reach CognoDB. Check the instance is running."
        except Exception as e:
            self._connect_error = f"Could not connect to CognoDB: {e}"

    @property
    def available(self) -> bool:
        return self._driver is not None

    @property
    def error(self):
        return self._connect_error

    def run(self, cypher_query, **params):
        """Run a parameterized query and return a list of record dicts.
        Raises a RuntimeError with a friendly message if the DB is unreachable
        or the query times out under free-tier resource limits."""
        if not self._driver:
            raise RuntimeError(self._connect_error or "Database is not connected.")
        try:
            with self._driver.session() as session:
                result = session.run(cypher_query, parameters=params)
                return [record.data() for record in result]
        except ServiceUnavailable:
            raise RuntimeError("Lost connection to CognoDB mid-query. Please try again.")
        except TransientError:
            raise RuntimeError(
                "This query took too long under the free tier's resource limits. "
                "Try a pair of users with a shorter expected path, or try again."
            )

    def close(self):
        if self._driver:
            self._driver.close()