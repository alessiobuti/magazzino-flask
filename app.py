from flask import Flask, render_template, request, redirect

app = Flask(__name__)

products = [
    {"sku": "M001", "name": "Miele", "quantity": 20},
    {"sku": "B001", "name": "Burro cacao", "quantity": 15},
    {"sku": "S001", "name": "Saponetta", "quantity": 30},
    {"sku": "C001", "name": "Crema", "quantity": 25}
]

kits = []

@app.route('/')
def index():
    return render_template('index.html', products=products, kits=kits)

@app.route('/add_product', methods=['POST'])
def add_product():
    sku = request.form['sku']
    name = request.form['name']
    quantity = int(request.form['quantity'])
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
    for sku in kit_skus:
        product = next((p for p in products if p['sku'] == sku), None)
        if not product or product['quantity'] < 1:
            return f"Errore: prodotto {sku} non disponibile", 400
    for sku in kit_skus:
        for p in products:
            if p['sku'] == sku:
                p['quantity'] -= 1
    kits.append({"name": kit_name, "skus": kit_skus})
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
