from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.debug = True

ordini_memoria = {}  # memorizza gli ordini in memoria

# --- Helper DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Prodotti
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Prodotti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            quantita_pieni INTEGER,
            quantita_vuoti INTEGER
        )
    ''')
    # Clienti
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Clienti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    ''')
    # Ordini (con nuova colonna stato)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Ordini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            totale REAL,
            stato TEXT DEFAULT 'in sospeso',
            FOREIGN KEY(cliente_id) REFERENCES Clienti(id)
        )
    ''')
    # Dettaglio Ordini
    conn.execute('''
        CREATE TABLE IF NOT EXISTS DettaglioOrdini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ordine_id INTEGER,
            prodotto_id INTEGER,
            quantita INTEGER,
            prezzo_unitario REAL,
            FOREIGN KEY(ordine_id) REFERENCES Ordini(id),
            FOREIGN KEY(prodotto_id) REFERENCES Prodotti(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Rotta principale: inventario ---
@app.route('/')
def index():
    conn = get_db_connection()
    prodotti = conn.execute("SELECT * FROM Prodotti").fetchall()
    conn.close()
    return render_template('index.html', prodotti=prodotti)

# --- Aggiungi prodotto ---
@app.route('/aggiungi_prodotto', methods=['POST'])
def aggiungi_prodotto():
    nome = request.form['nome']
    pieni = int(request.form['pieni'])
    vuoti = int(request.form['vuoti'])
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO Prodotti (nome, quantita_pieni, quantita_vuoti) VALUES (?, ?, ?)",
                     (nome, pieni, vuoti))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect('/')

# --- Modifica quantità ---
@app.route('/modifica_prodotto/<int:prod_id>', methods=['POST'])
def modifica_prodotto(prod_id):
    pieni = int(request.form['pieni'])
    vuoti = int(request.form['vuoti'])
    conn = get_db_connection()
    conn.execute("UPDATE Prodotti SET quantita_pieni=?, quantita_vuoti=? WHERE id=?",
                 (pieni, vuoti, prod_id))
    conn.commit()
    conn.close()
    return redirect('/')

# --- Elimina prodotto ---
@app.route('/elimina_prodotto/<int:prod_id>')
def elimina_prodotto(prod_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Prodotti WHERE id=?", (prod_id,))
    conn.commit()
    conn.close()
    return redirect('/')

# --- Gestione ordini ---
@app.route('/ordini')
def ordini():
    conn = get_db_connection()
    # ✅ mostra anche i prodotti con quantità 0 o negativa
    prodotti = conn.execute("SELECT * FROM Prodotti").fetchall()
    clienti = conn.execute("SELECT * FROM Clienti").fetchall()

    # Recupera gli ordini già creati con dettagli
    ordini_list = conn.execute("""
        SELECT o.id, c.nome AS cliente, o.data, o.totale, o.stato
        FROM Ordini o
        JOIN Clienti c ON o.cliente_id = c.id
        ORDER BY o.id DESC
    """).fetchall()

    ordini_dettagli = {}
    for o in ordini_list:
        dettagli = conn.execute("""
            SELECT p.nome, d.quantita, d.prezzo_unitario
            FROM DettaglioOrdini d
            JOIN Prodotti p ON d.prodotto_id = p.id
            WHERE d.ordine_id = ?
        """, (o['id'],)).fetchall()
        ordini_dettagli[o['id']] = dettagli

    conn.close()
    return render_template('ordini.html', prodotti=prodotti, clienti=clienti, ordini=ordini_list, dettagli=ordini_dettagli)

@app.route('/crea_ordine', methods=['POST'])
def crea_ordine():
    cliente_nome = request.form['cliente']
    conn = get_db_connection()
    res = conn.execute("SELECT id FROM Clienti WHERE nome=?", (cliente_nome,)).fetchone()
    if not res:
        conn.execute("INSERT INTO Clienti (nome) VALUES (?)", (cliente_nome,))
        conn.commit()
        res = conn.execute("SELECT id FROM Clienti WHERE nome=?", (cliente_nome,)).fetchone()
    cliente_id = res['id']

    totale = 0
    prodotti_ordine = []
    for key in request.form:
        if key.startswith('prod_'):
            prod_id = int(key.split('_')[1])
            quantita = int(request.form[key])
            if quantita <= 0:
                continue
            prezzo = float(request.form[f'prezzo_{prod_id}'])
            prodotti_ordine.append((prod_id, quantita, prezzo))
            totale += quantita * prezzo

    if not prodotti_ordine:
        return redirect('/ordini')

    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO Ordini (cliente_id, data, totale, stato) VALUES (?, ?, ?, 'in sospeso')",
                 (cliente_id, data, totale))
    ordine_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    for prod_id, quantita, prezzo in prodotti_ordine:
        conn.execute("INSERT INTO DettaglioOrdini (ordine_id, prodotto_id, quantita, prezzo_unitario) VALUES (?, ?, ?, ?)",
                     (ordine_id, prod_id, quantita, prezzo))
        # aggiorna inventario: decremento pieni
        conn.execute("UPDATE Prodotti SET quantita_pieni = quantita_pieni - ? WHERE id=?", (quantita, prod_id))

    conn.commit()
    conn.close()

    return redirect('/ordini')

# ✅ --- Elimina ordine e ripristina inventario ---
@app.route('/elimina_ordine/<int:ordine_id>', methods=['POST'])
def elimina_ordine(ordine_id):
    conn = get_db_connection()

    # recupera i dettagli dell'ordine
    dettagli = conn.execute("SELECT prodotto_id, quantita FROM DettaglioOrdini WHERE ordine_id=?", (ordine_id,)).fetchall()

    # restituisce le quantità in inventario
    for d in dettagli:
        conn.execute("UPDATE Prodotti SET quantita_pieni = quantita_pieni + ? WHERE id=?", (d['quantita'], d['prodotto_id']))

    # elimina l'ordine e i suoi dettagli
    conn.execute("DELETE FROM DettaglioOrdini WHERE ordine_id=?", (ordine_id,))
    conn.execute("DELETE FROM Ordini WHERE id=?", (ordine_id,))
    conn.commit()
    conn.close()

    return redirect('/ordini')

# ✅ --- Segna ordine come consegnato ---
@app.route('/consegna_ordine/<int:ordine_id>', methods=['POST'])
def consegna_ordine(ordine_id):
    conn = get_db_connection()
    conn.execute("UPDATE Ordini SET stato='consegnato' WHERE id=?", (ordine_id,))
    conn.commit()
    conn.close()
    return redirect('/ordini')

# --- Report vendite ---
@app.route('/report')
def report():
    mese = request.args.get('mese')
    anno = request.args.get('anno')
    query = "SELECT data, totale FROM Ordini WHERE 1=1"
    params = []
    if anno:
        query += " AND strftime('%Y', data)=?"
        params.append(anno)
    if mese:
        query += " AND strftime('%m', data)=?"
        params.append(mese)
    conn = get_db_connection()
    ordini = conn.execute(query, params).fetchall()
    totale = sum([o['totale'] for o in ordini])
    conn.close()
    return render_template('report.html', ordini=ordini, totale=totale, mese=mese, anno=anno)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
