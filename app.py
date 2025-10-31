from flask import Flask, render_template_string, request, redirect
import sqlite3
import os

app = Flask(__name__)

DB_FILE = "magazzino.db"

# --------------------------
# DATABASE SETUP
# --------------------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Prodotti
        c.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            quantita INTEGER DEFAULT 0
        )
        """)
        # Kit
        c.execute("""
        CREATE TABLE IF NOT EXISTS kit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
        """)
        # Componenti del kit
        c.execute("""
        CREATE TABLE IF NOT EXISTS kit_componenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kit_id INTEGER,
            prodotto_id INTEGER,
            quantita INTEGER,
            FOREIGN KEY (kit_id) REFERENCES kit(id),
            FOREIGN KEY (prodotto_id) REFERENCES prodotti(id)
        )
        """)
        conn.commit()

if not os.path.exists(DB_FILE):
    init_db()

# --------------------------
# PAGINA PRINCIPALE
# --------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestione Magazzino</title>
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 30px auto; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        form { margin-bottom: 20px; }
        input, select, button { padding: 5px; margin: 3px; }
        h2 { margin-top: 40px; }
    </style>
</head>
<body>
    <h1>📦 Gestione Magazzino</h1>

    <h2>➕ Aggiungi Prodotto</h2>
    <form action="/add_product" method="post">
        Nome: <input type="text" name="nome" required>
        SKU: <input type="text" name="sku" required>
        Quantità: <input type="number" name="quantita" required>
        <button type="submit">Aggiungi</button>
    </form>

    <h2>📋 Prodotti</h2>
    <table>
        <tr><th>ID</th><th>Nome</th><th>SKU</th><th>Quantità</th><th>Azione</th></tr>
        {% for p in prodotti %}
        <tr>
            <td>{{ p[0] }}</td>
            <td>{{ p[1] }}</td>
            <td>{{ p[2] }}</td>
            <td>{{ p[3] }}</td>
            <td>
                <form action="/update_quantity/{{ p[0] }}" method="post" style="display:inline;">
                    <input type="number" name="delta" placeholder="+/- quantità">
                    <button type="submit">Aggiorna</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>

    <h2>🧩 Crea Kit</h2>
    <form action="/create_kit" method="post">
        Nome kit: <input type="text" name="nome_kit" required><br>
        {% for p in prodotti %}
            <input type="checkbox" name="prodotti" value="{{ p[0] }}"> {{ p[1] }} ({{ p[3] }} disponibili)
            Quantità per kit: <input type="number" name="qta_{{ p[0] }}" min="1" value="1"><br>
        {% endfor %}
        <button type="submit">Crea Kit</button>
    </form>

    <h2>📦 Aggiungi Kit</h2>
    <form action="/add_kit" method="post">
        <select name="kit_id">
            {% for k in kit %}
            <option value="{{ k[0] }}">{{ k[1] }}</option>
            {% endfor %}
        </select>
        <input type="number" name="quantita" placeholder="Quanti kit?" min="1" required>
        <button type="submit">Aggiungi Kit</button>
    </form>

    <h2>🧺 Kit Disponibili</h2>
    <table>
        <tr><th>ID</th><th>Nome Kit</th><th>Componenti</th></tr>
        {% for k in kit %}
        <tr>
            <td>{{ k[0] }}</td>
            <td>{{ k[1] }}</td>
            <td>
                {% for c in componenti[k[0]] %}
                    {{ c[1] }} (x{{ c[2] }})<br>
                {% endfor %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# --------------------------
# ROUTES
# --------------------------
@app.route("/")
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM prodotti")
    prodotti = c.fetchall()
    c.execute("SELECT * FROM kit")
    kit = c.fetchall()
    componenti = {}
    for k in kit:
        c.execute("""
        SELECT p.id, p.nome, kc.quantita
        FROM kit_componenti kc
        JOIN prodotti p ON kc.prodotto_id = p.id
        WHERE kc.kit_id = ?
        """, (k[0],))
        componenti[k[0]] = c.fetchall()
    conn.close()
    return render_template_string(HTML, prodotti=prodotti, kit=kit, componenti=componenti)

@app.route("/add_product", methods=["POST"])
def add_product():
    nome = request.form["nome"]
    sku = request.form["sku"]
    quantita = int(request.form["quantita"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO prodotti (nome, sku, quantita) VALUES (?, ?, ?)", (nome, sku, quantita))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/update_quantity/<int:prod_id>", methods=["POST"])
def update_quantity(prod_id):
    delta = int(request.form["delta"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE prodotti SET quantita = quantita + ? WHERE id = ?", (delta, prod_id))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/create_kit", methods=["POST"])
def create_kit():
    nome_kit = request.form["nome_kit"]
    prodotti_selezionati = request.form.getlist("prodotti")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO kit (nome) VALUES (?)", (nome_kit,))
    kit_id = c.lastrowid
    for pid in prodotti_selezionati:
        qta = int(request.form.get(f"qta_{pid}", 1))
        c.execute("INSERT INTO kit_componenti (kit_id, prodotto_id, quantita) VALUES (?, ?, ?)", (kit_id, pid, qta))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/add_kit", methods=["POST"])
def add_kit():
    kit_id = int(request.form["kit_id"])
    quantita_kit = int(request.form["quantita"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT prodotto_id, quantita FROM kit_componenti WHERE kit_id = ?", (kit_id,))
    componenti = c.fetchall()
    for prod_id, qta in componenti:
        c.execute("UPDATE prodotti SET quantita = quantita - ? WHERE id = ?", (qta * quantita_kit, prod_id))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
