"""
Loads the trust-network dataset into CognoDB.

Data model:
    (:User {id: int, name: string})-[:TRUSTS]->(:User)

Run:
    python scripts/load_data.py
"""
import os
import csv
import random
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

FIRST_NAMES = [
    "Aria", "Kai", "Nova", "Rhea", "Leo", "Mira", "Zane", "Ivy", "Omar", "Sana",
    "Finn", "Layla", "Rian", "Tara", "Neel", "Dara", "Kian", "Elle", "Soren", "Maya",
]
LAST_INITIALS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def read_csv(filepath):
    with open(filepath, "r") as f:
        return list(csv.DictReader(f))


def get_env_safe(key):
    val = os.getenv(key)
    return val.strip() if val else None


def generate_name(seed_id: int) -> str:
    """Deterministic fake name from a node id, so reruns stay stable."""
    rng = random.Random(seed_id)
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_INITIALS)}."


CONSTRAINT_QUERY = "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE"

NODE_QUERY = """
UNWIND $batch AS row
MERGE (u:User {id: row.id})
SET u.name = row.name
"""

EDGE_QUERY = """
UNWIND $batch AS row
MATCH (s:User {id: row.source})
MATCH (t:User {id: row.target})
MERGE (s)-[:TRUSTS]->(t)
"""


def load_data(uri, user, password):
    if not uri or "<" in uri:
        print("CognoDB URI not configured in .env — copy .env.example to .env and fill it in.")
        return

    print("Loading CSVs into memory...")
    raw_nodes = read_csv("data/nodes.csv")
    raw_edges = read_csv("data/edges.csv")

    nodes = [{"id": int(r["id"]), "name": generate_name(int(r["id"]))} for r in raw_nodes]
    edges = [{"source": int(r["source"]), "target": int(r["target"])} for r in raw_edges]

    print("--- Ingesting into CognoDB ---")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            try:
                session.run(CONSTRAINT_QUERY)
                print("Unique constraint created.")
            except Exception as e:
                print(f"Note on constraint: {e}")

            start_time = time.time()
            batch_size = 5000

            for i in range(0, len(nodes), batch_size):
                session.run(NODE_QUERY, batch=nodes[i : i + batch_size])
            print(f"Nodes loaded ({len(nodes)} records).")

            for i in range(0, len(edges), batch_size):
                session.run(EDGE_QUERY, batch=edges[i : i + batch_size])
            print(f"Edges loaded ({len(edges)} records).")

            print(f"SUCCESS: Total load time: {time.time() - start_time:.2f} seconds")
    finally:
        driver.close()


if __name__ == "__main__":
    load_data(
        get_env_safe("COGNODB_URI"),
        get_env_safe("COGNODB_USER"),
        get_env_safe("COGNODB_PASS"),
    )
