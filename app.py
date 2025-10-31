from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Magazzino e ordini
prodotti = {}  # struttura: {"nome": {"quantita": int, "prezzo": float}}
ordini = {}    # struttura: {"nome_cliente": {"prodotti": [nomi], "quantita": int}}

# Valore totale venduto
valore_totale_venduto = 0.0

@app.route('/')
def index():
    global valore_totale_venduto
    return render_template('index.html', prodotti=prodotti, ordini=ordini, valore_totale_venduto=valore_totale_venduto)

# Aggiungi prodotto
@app.route('/add_product', methods=['POST'])
def add_product():
    nome = request.form['nome_prodotto']
    quantita = int(request.form['quantita_prodotto'])
    prezzo = float(request.form['prezzo_prodotto'])
    if nome in prodotti:
        prodotti[nome]['quantita'] += quantita
        prodotti[nome]['prezzo'] = prezzo  # aggiorna il prezzo se cambia
    else:
        prodotti[nome] = {'quantita': quantita, 'prezzo': prezzo}
    return redirect(url_for('index'))

# Modifica quantità prodotto
@app.route('/update_product/<nome>', methods=['POST'])
def update_product(nome):
    nuova_quantita = int(request.form['nuova_quantita'])
    prodotti[nome]['quantita'] = nuova_quantita
    return redirect(url_for('index'))

# Elimina prodotto
@app.route('/delete_product/<nome>')
def delete_product(nome):
    if nome in prodotti:
        del prodotti[nome]
    return redirect(url_for('index'))

# Aggiungi ordine/kit
@app.route('/add_order', methods=['POST'])
def add_order():
    global valore_totale_venduto
    nome_cliente = request.form['nome_cliente']
    quantita_ordini = int(request.form['quantita'])
    prodotti_selezionati = request.form.getlist('prodotti_kit')  # lista di prodotti

    # Controllo disponibilità
    for p in prodotti_selezionati:
        if p not in prodotti or prodotti[p]['quantita'] < quantita_ordini:
            return f"Prodotto {p} non disponibile in quantità sufficiente."

    # Aggiorna magazzino e valore totale venduto
    for p in prodotti_selezionati:
        prodotti[p]['quantita'] -= quantita_ordini
        valore_totale_venduto += prodotti[p]['prezzo'] * quantita_ordini

    # Salva ordine
    ordini[nome_cliente] = {'prodotti': prodotti_selezionati, 'quantita': quantita_ordini}
    return redirect(url_for('index'))

# Elimina ordine/kit
@app.route('/delete_order/<nome_cliente>')
def delete_order(nome_cliente):
    if nome_cliente in ordini:
        # Restituisci prodotti al magazzino e aggiorna il valore totale venduto
        for p in ordini[nome_cliente]['prodotti']:
            prodotti[p]['quantita'] += ordini[nome_cliente]['quantita']
            valore_totale_venduto -= prodotti[p]['prezzo'] * ordini[nome_cliente]['quantita']
        del ordini[nome_cliente]
    return redirect(url_for('index'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
