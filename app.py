import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from backend.db import Database
from backend import queries

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

db = Database()


@app.route("/")
def index():
    return render_template("index.html", db_available=db.available, db_error=db.error)


@app.route("/api/search")
def search_users():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"results": []})
    try:
        results = db.run(queries.SEARCH_USERS, query=q)
        return jsonify({"results": results})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/user/<int:user_id>")
def user_detail(user_id):
    try:
        user = db.run(queries.GET_USER, user_id=user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        trusts = db.run(queries.DIRECT_TRUSTS, user_id=user_id)
        trusted_by = db.run(queries.DIRECT_TRUSTED_BY, user_id=user_id)
        suggestions = db.run(queries.SUGGESTIONS, user_id=user_id)

        return jsonify({
            "user": user[0],
            "trusts": trusts,
            "trusted_by": trusted_by,
            "suggestions": suggestions,
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/path")
def shortest_path():
    from_id = request.args.get("from", type=int)
    to_id = request.args.get("to", type=int)
    if from_id is None or to_id is None:
        return jsonify({"error": "Both 'from' and 'to' user ids are required."}), 400

    try:
        result = db.run(queries.SHORTEST_PATH, from_id=from_id, to_id=to_id)
        if not result:
            return jsonify({"path": None, "hops": None,
                             "message": "No trust path found within 6 hops."})
        return jsonify(result[0])
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


if __name__ == "__main__":
    app.run(debug=True, port=5000)
