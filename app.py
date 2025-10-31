from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Magazzino e kit
prodotti = {}  # formato: {nome: {'quantita': x, 'costo': y}}
kit = {}       # formato: {nome_persona: {'prodotti': [prodotti], 'quantita': x}}

# Totale venduto
valore_totale_venduto = 0

@app.route('/')
def index():
    global valore_totale_venduto
    # Calcola valore totale attuale
    totale_magazzino = sum(prodotti[p]['quantita'] * prodotti[p]['costo'] for p in prodotti)
    return render_template('index.html', prodotti=prodotti, kit=kit, valore_totale_venduto=totale_magazzino)

# Aggiungi prodotto
@app.route('/add_product', methods=['POST'])
def add_product():
    nome = request.form['nome_prodotto']
    quantita = int(request.form['quantita_prodotto'])
    costo = float(request.form['costo_prodotto'])
    
    if nome in prodotti:
        prodotti[nome]['quantita'] += quantita
        prodotti[nome]['costo'] = costo  # aggiorna costo se cambiato
    else:
        prodotti[nome] = {'quantita': quantita, 'costo': costo}
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

# Aggiungi kit / prodotti ordinati
@app.route('/add_kit', methods=['POST'])
def add_kit():
    nome_persona = request.form['nome_persona']
    quantita = int(request.form['quantita'])
    prodotti_inclusi = request.form.getlist('prodotti_kit')

    # Controllo disponibilità
    for p in prodotti_inclusi:
        if p not in prodotti or prodotti[p]['quantita'] < quantita:
            return f"Prodotto {p} non disponibile in quantità sufficiente."

    # Aggiorna magazzino
    for p in prodotti_inclusi:
        prodotti[p]['quantita'] -= quantita

    # Salva kit
    kit[nome_persona] = {'prodotti': prodotti_inclusi, 'quantita': quantita}
    return redirect(url_for('index'))

# Elimina kit / prodotti ordinati
@app.route('/delete_kit/<nome_persona>')
def delete_kit(nome_persona):
    if nome_persona in kit:
        # Restituisci prodotti al magazzino
        for p in kit[nome_persona]['prodotti']:
            if p in prodotti:
                prodotti[p]['quantita'] += kit[nome_persona]['quantita']
            else:
                prodotti[p] = {'quantita': kit[nome_persona]['quantita'], 'costo': 0}
        del kit[nome_persona]
    return redirect(url_for('index'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
