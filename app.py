import sqlite3
import os
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "restaurants.db")
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('visited', 'wishlist')),
            rating INTEGER CHECK(rating IS NULL OR (rating >= 1 AND rating <= 10)),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/api/restaurants", methods=["GET"])
def get_restaurants():
    conn = get_db()
    rows = conn.execute("SELECT * FROM restaurants ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
@app.route("/api/restaurants", methods=["POST"])
def add_restaurant():
    data = request.json
    conn = get_db()
    conn.execute(
        """INSERT INTO restaurants (name, address, lat, lng, status, rating, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            data["name"],
            data.get("address", ""),
            data["lat"],
            data["lng"],
            data["status"],
            data.get("rating"),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201
@app.route("/api/restaurants/<int:rid>", methods=["PUT"])
def update_restaurant(rid):
    data = request.json
    conn = get_db()
    conn.execute(
        """UPDATE restaurants
           SET name=?, address=?, lat=?, lng=?, status=?, rating=?, notes=?
           WHERE id=?""",
        (
            data["name"],
            data.get("address", ""),
            data["lat"],
            data["lng"],
            data["status"],
            data.get("rating"),
            data.get("notes", ""),
            rid,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
@app.route("/api/restaurants/<int:rid>", methods=["DELETE"])
def delete_restaurant(rid):
    conn = get_db()
    conn.execute("DELETE FROM restaurants WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
