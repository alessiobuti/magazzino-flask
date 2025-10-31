from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Magazzino e ordini
prodotti = {}  # {'Miele': 20, 'Burro cacao': 15}
ordini = {}    # {'Alberto': [{'prodotto': 'Miele', 'quantita': 2, 'prezzo': 5.0}, ...]}

@app.route('/')
def index():
    # Calcolo valore totale degli ordini
    totale_valore = 0
    for ord_list in ordini.values():
        for item in ord_list:
            totale_valore += item['quantita'] * item['prezzo']
    return render_template('index.html', prodotti=prodotti, ordini=ordini, totale_valore=totale_valore)

# Aggiungi prodotto al magazzino
@app.route('/add_product', methods=['POST'])
def add_product():
    nome = request.form['nome_prodotto']
    quantita = int(request.form['quantita_prodotto'])
    if nome in prodotti:
        prodotti[nome] += quantita
    else:
        prodotti[nome] = quantita
    return redirect(url_for('index'))

# Modifica quantità prodotto nel magazzino
@app.route('/update_product/<nome>', methods=['POST'])
def update_product(nome):
    nuova_quantita = int(request.form['nuova_quantita'])
    prodotti[nome] = nuova_quantita
    return redirect(url_for('index'))

# Elimina prodotto dal magazzino
@app.route('/delete_product/<nome>')
def delete_product(nome):
    if nome in prodotti:
        del prodotti[nome]
    return redirect(url_for('index'))

# Aggiungi ordine/kit
@app.route('/add_order', methods=['POST'])
def add_order():
    nome_persona = request.form['nome_persona']
    prodotti_selezionati = request.form.getlist('prodotti_ordine')
    quantita_list = request.form.getlist('quantita')
    prezzi_list = request.form.getlist('prezzo')

    # Controllo disponibilità
    for i, p in enumerate(prodotti_selezionati):
        q = int(quantita_list[i])
        if p not in prodotti or prodotti[p] < q:
            return f"Prodotto {p} non disponibile in quantità sufficiente."

    # Aggiorna magazzino e ordini
    if nome_persona not in ordini:
        ordini[nome_persona] = []

    for i, p in enumerate(prodotti_selezionati):
        q = int(quantita_list[i])
        prezzo = float(prezzi_list[i])
        prodotti[p] -= q
        ordini[nome_persona].append({'prodotto': p, 'quantita': q, 'prezzo': prezzo})

    return redirect(url_for('index'))

# Elimina ordine
@app.route('/delete_order/<nome_persona>')
def delete_order(nome_persona):
    if nome_persona in ordini:
        # Restituisci prodotti al magazzino
        for item in ordini[nome_persona]:
            prodotti[item['prodotto']] += item['quantita']
        del ordini[nome_persona]
    return redirect(url_for('index'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
