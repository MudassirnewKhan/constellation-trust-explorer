"""
All Cypher lives here, kept separate from the Flask routes.
Every query is parameterized — no string-concatenated Cypher anywhere.
"""

GET_USER = """
MATCH (u:User {id: $user_id})
RETURN u.id AS id, u.name AS name
"""

DIRECT_TRUSTS = """
MATCH (u:User {id: $user_id})-[:TRUSTS]->(trusted:User)
RETURN trusted.id AS id, trusted.name AS name
ORDER BY trusted.name
"""

DIRECT_TRUSTED_BY = """
MATCH (u:User {id: $user_id})<-[:TRUSTS]-(truster:User)
RETURN truster.id AS id, truster.name AS name
ORDER BY truster.name
"""

# Friends-of-friends: people trusted by people I trust, whom I don't already
# trust myself. This is a 2-hop traversal — one clean pattern match in Cypher.
# The equivalent in SQL needs a self-join per hop and gets messier with every
# additional hop; here it's the same cost to go to 3 or 4 hops.
SUGGESTIONS = """
MATCH (me:User {id: $user_id})-[:TRUSTS]->(friend:User)-[:TRUSTS]->(fof:User)
WHERE fof <> me AND NOT (me)-[:TRUSTS]->(fof)
RETURN fof.id AS id, fof.name AS name, count(DISTINCT friend) AS mutual_paths
ORDER BY mutual_paths DESC, fof.name
LIMIT 10
"""

# Shortest trust path between two arbitrary users. This is the query a
# relational database would find genuinely awkward — it needs an unbounded
# recursive join in SQL, whereas Cypher's shortestPath() handles variable
# hop-count natively.
SHORTEST_PATH = """
MATCH p = shortestPath(
    (a:User {id: $from_id})-[:TRUSTS*..4]->(b:User {id: $to_id})
)
RETURN [n IN nodes(p) | {id: n.id, name: n.name}] AS path,
       length(p) AS hops
"""

SEARCH_USERS = """
MATCH (u:User)
WHERE toLower(u.name) CONTAINS toLower($query)
RETURN u.id AS id, u.name AS name
ORDER BY u.name
LIMIT 20
"""
