from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# Lista dei prodotti in magazzino
products = [
    {"sku": "M001", "name": "Miele", "quantity": 20},
    {"sku": "B001", "name": "Burro cacao", "quantity": 15},
    {"sku": "S001", "name": "Saponetta", "quantity": 30},
    {"sku": "C001", "name": "Crema", "quantity": 25}
]

# Lista dei kit creati
kits = []

# Template HTML semplice
TEMPLATE = """
<!doctype html>
<title>Magazzino</title>
<h1>Magazzino</h1>
<h2>Prodotti</h2>
<table border="1" cellpadding="5">
<tr><th>SKU</th><th>Nome</th><th>Quantità</th><th>Elimina</th></tr>
{% for p in products %}
<tr>
    <td>{{ p.sku }}</td>
    <td>{{ p.name }}</td>
    <td>{{ p.quantity }}</td>
    <td>
        <form action="/delete/{{ p.sku }}" method="post">
            <button type="submit">Elimina</button>
        </form>
    </td>
</tr>
{% endfor %}
</table>

<h2>Aggiungi prodotto</h2>
<form action="/add_product" method="post">
    SKU: <input type="text" name="sku" required>
    Nome: <input type="text" name="name" required>
    Quantità: <input type="number" name="quantity" min="1" required>
    <button type="submit">Aggiungi</button>
</form>

<h2>Crea kit</h2>
<form action="/create_kit" method="post">
    Nome kit: <input type="text" name="kit_name" required>
    <br>
    Prodotti (SKU separati da virgola): <input type="text" name="kit_skus" required>
    <br>
    <button type="submit">Crea kit</button>
</form>

<h2>Kit creati</h2>
<table border="1" cellpadding="5">
<tr><th>Nome Kit</th><th>Prodotti</th></tr>
{% for k in kits %}
<tr>
    <td>{{ k.name }}</td>
    <td>{{ ", ".join(k.skus) }}</td>
</tr>
{% endfor %}
</table>
"""

@app.route('/')
def index():
    return render_template_string(TEMPLATE, products=products, kits=kits)

@app.route('/add_product', methods=['POST'])
def add_product():
    sku = request.form['sku']
    name = request.form['name']
    quantity = int(request.form['quantity'])
    # Controlla se lo SKU esiste già
    for p in products:
        if p['sku'] == sku:
            p['quantity'] += quantity
            break
    else:
        products.append({"sku": sku, "name": name, "quantity": quantity})
    return redirect('/')

@app.route('/delete/<sku>', methods=['POST'])
def delete_product(sku):
    global products
    products = [p for p in products if p['sku'] != sku]
    return redirect('/')

@app.route('/create_kit', methods=['POST'])
def create_kit():
    kit_name = request.form['kit_name']
    kit_skus = [s.strip() for s in request.form['kit_skus'].split(',')]
    
    # Controlla se tutti i prodotti sono disponibili
    for sku in kit_skus:
        product = next((p for p in products if p['sku'] == sku), None)
        if not product or product['quantity'] < 1:
            return f"Errore: prodotto {sku} non disponibile", 400
    
    # Sottrae 1 alla quantità di ciascun prodotto
    for sku in kit_skus:
        for p in products:
            if p['sku'] == sku:
                p['quantity'] -= 1
    
    kits.append({"name": kit_name, "skus": kit_skus})
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
