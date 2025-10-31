from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Magazzino e ordini
magazzino = {}  # nome_prodotto: quantità
ordini = {}     # id_ordine: {'prodotti': [(nome, quantita, prezzo)], 'totale': valore_totale}

ordine_id_counter = 1  # Contatore per identificare gli ordini

@app.route('/')
def index():
    return render_template('index.html', magazzino=magazzino, ordini=ordini)

# Aggiungi prodotto al magazzino
@app.route('/add_product', methods=['POST'])
def add_product():
    nome = request.form['nome_prodotto']
    quantita = int(request.form['quantita_prodotto'])
    if nome in magazzino:
        magazzino[nome] += quantita
    else:
        magazzino[nome] = quantita
    return redirect(url_for('index'))

# Modifica quantità prodotto
@app.route('/update_product/<nome>', methods=['POST'])
def update_product(nome):
    nuova_quantita = int(request.form['nuova_quantita'])
    magazzino[nome] = nuova_quantita
    return redirect(url_for('index'))

# Elimina prodotto dal magazzino
@app.route('/delete_product/<nome>')
def delete_product(nome):
    if nome in magazzino:
        del magazzino[nome]
    return redirect(url_for('index'))

# Aggiungi ordine
@app.route('/add_order', methods=['POST'])
def add_order():
    global ordine_id_counter
    prodotti_selezionati = request.form.getlist('prodotti')
    quantita_selezionate = request.form.getlist('quantita')
    prezzi_selezionati = request.form.getlist('prezzo')

    prodotti_ordine = []
    totale = 0

    # Controllo disponibilità e aggiorno magazzino
    for i, nome in enumerate(prodotti_selezionati):
        quantita = int(quantita_selezionate[i])
        prezzo = float(prezzi_selezionati[i])
        if nome not in magazzino or magazzino[nome] < quantita:
            return f"Prodotto {nome} non disponibile in quantità sufficiente."
        magazzino[nome] -= quantita
        prodotti_ordine.append((nome, quantita, prezzo))
        totale += quantita * prezzo

    ordini[ordine_id_counter] = {'prodotti': prodotti_ordine, 'totale': totale}
    ordine_id_counter += 1
    return redirect(url_for('index'))

# Elimina ordine
@app.route('/delete_order/<int:ordine_id>')
def delete_order(ordine_id):
    if ordine_id in ordini:
        # Restituisci quantità al magazzino
        for nome, quantita, _ in ordini[ordine_id]['prodotti']:
            if nome in magazzino:
                magazzino[nome] += quantita
            else:
                magazzino[nome] = quantita
        del ordini[ordine_id]
    return redirect(url_for('index'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
