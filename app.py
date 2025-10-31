from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Magazzino e kit
prodotti = {}
kit = {}

@app.route('/')
def index():
    return render_template('index.html', prodotti=prodotti, kit=kit)

# Aggiungi prodotto
@app.route('/add_product', methods=['POST'])
def add_product():
    nome = request.form['nome_prodotto']
    quantita = int(request.form['quantita_prodotto'])
    if nome in prodotti:
        prodotti[nome] += quantita
    else:
        prodotti[nome] = quantita
    return redirect(url_for('index'))

# Modifica quantità prodotto
@app.route('/update_product/<nome>', methods=['POST'])
def update_product(nome):
    nuova_quantita = int(request.form['nuova_quantita'])
    prodotti[nome] = nuova_quantita
    return redirect(url_for('index'))

# Elimina prodotto
@app.route('/delete_product/<nome>')
def delete_product(nome):
    if nome in prodotti:
        del prodotti[nome]
    return redirect(url_for('index'))

# Aggiungi kit
@app.route('/add_kit', methods=['POST'])
def add_kit():
    nome_persona = request.form['nome_persona']
    quantita_kit = int(request.form['quantita_kit'])
    prodotti_inclusi = request.form.getlist('prodotti_kit')

    # Controllo disponibilità
    for p in prodotti_inclusi:
        if p not in prodotti or prodotti[p] < quantita_kit:
            return f"Prodotto {p} non disponibile in quantità sufficiente."

    # Aggiorna magazzino
    for p in prodotti_inclusi:
        prodotti[p] -= quantita_kit

    # Salva kit
    kit[nome_persona] = {'prodotti': prodotti_inclusi, 'quantita': quantita_kit}
    return redirect(url_for('index'))

# Elimina kit
@app.route('/delete_kit/<nome_persona>')
def delete_kit(nome_persona):
    if nome_persona in kit:
        # Restituisci prodotti al magazzino
        for p in kit[nome_persona]['prodotti']:
            prodotti[p] += kit[nome_persona]['quantita']
        del kit[nome_persona]
    return redirect(url_for('index'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # usa la porta fornita da Render
    app.run(host="0.0.0.0", port=port, debug=True)

