from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.debug = True

# 🔹 Configurazione database PostgreSQL (Render imposta DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# === MODELLI ===

class Prodotto(db.Model):
    __tablename__ = 'prodotti'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    quantita_pieni = db.Column(db.Integer, default=0)
    quantita_vuoti = db.Column(db.Integer, default=0)


class Cliente(db.Model):
    __tablename__ = 'clienti'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)


class Ordine(db.Model):
    __tablename__ = 'ordini'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    totale = db.Column(db.Float, nullable=False)
    stato = db.Column(db.String(50), default='in sospeso')

    cliente = db.relationship('Cliente', backref='ordini')
    dettagli = db.relationship('DettaglioOrdine', backref='ordine', cascade="all, delete-orphan")


class DettaglioOrdine(db.Model):
    __tablename__ = 'dettagli_ordini'
    id = db.Column(db.Integer, primary_key=True)
    ordine_id = db.Column(db.Integer, db.ForeignKey('ordini.id'), nullable=False)
    prodotto_id = db.Column(db.Integer, db.ForeignKey('prodotti.id'), nullable=False)
    quantita = db.Column(db.Integer, nullable=False)
    prezzo_unitario = db.Column(db.Float, nullable=False)

    prodotto = db.relationship('Prodotto')


# 🔹 Crea tabelle al primo avvio
with app.app_context():
    db.create_all()

# === ROTTE ===

@app.route('/')
def index():
    prodotti = Prodotto.query.all()
    return render_template('index.html', prodotti=prodotti)


@app.route('/aggiungi_prodotto', methods=['POST'])
def aggiungi_prodotto():
    nome = request.form['nome']
    pieni = int(request.form['pieni'])
    vuoti = int(request.form['vuoti'])
    if not Prodotto.query.filter_by(nome=nome).first():
        nuovo = Prodotto(nome=nome, quantita_pieni=pieni, quantita_vuoti=vuoti)
        db.session.add(nuovo)
        db.session.commit()
    return redirect('/')


@app.route('/modifica_prodotto/<int:prod_id>', methods=['POST'])
def modifica_prodotto(prod_id):
    prodotto = Prodotto.query.get_or_404(prod_id)
    prodotto.quantita_pieni = int(request.form['pieni'])
    prodotto.quantita_vuoti = int(request.form['vuoti'])
    db.session.commit()
    return redirect('/')


@app.route('/elimina_prodotto/<int:prod_id>')
def elimina_prodotto(prod_id):
    prodotto = Prodotto.query.get_or_404(prod_id)
    db.session.delete(prodotto)
    db.session.commit()
    return redirect('/')


@app.route('/ordini')
def ordini():
    prodotti = Prodotto.query.all()
    clienti = Cliente.query.all()
    ordini_list = Ordine.query.order_by(Ordine.id.desc()).all()
    return render_template('ordini.html', prodotti=prodotti, clienti=clienti, ordini=ordini_list)


@app.route('/crea_ordine', methods=['POST'])
def crea_ordine():
    cliente_nome = request.form['cliente']
    cliente = Cliente.query.filter_by(nome=cliente_nome).first()
    if not cliente:
        cliente = Cliente(nome=cliente_nome)
        db.session.add(cliente)
        db.session.commit()

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

    nuovo_ordine = Ordine(cliente_id=cliente.id, totale=totale, stato='in sospeso')
    db.session.add(nuovo_ordine)
    db.session.flush()  # per ottenere subito nuovo_ordine.id

    for prod_id, quantita, prezzo in prodotti_ordine:
        dettaglio = DettaglioOrdine(
            ordine_id=nuovo_ordine.id,
            prodotto_id=prod_id,
            quantita=quantita,
            prezzo_unitario=prezzo
        )
        db.session.add(dettaglio)

        prodotto = Prodotto.query.get(prod_id)
        prodotto.quantita_pieni -= quantita

    db.session.commit()
    return redirect('/ordini')


@app.route('/elimina_ordine/<int:ordine_id>', methods=['POST'])
def elimina_ordine(ordine_id):
    ordine = Ordine.query.get_or_404(ordine_id)

    # Ripristina inventario
    for d in ordine.dettagli:
        d.prodotto.quantita_pieni += d.quantita

    db.session.delete(ordine)
    db.session.commit()
    return redirect('/ordini')


@app.route('/consegna_ordine/<int:ordine_id>', methods=['POST'])
def consegna_ordine(ordine_id):
    ordine = Ordine.query.get_or_404(ordine_id)
    ordine.stato = 'consegnato'
    db.session.commit()
    return redirect('/ordini')


@app.route('/report')
def report():
    mese = request.args.get('mese')
    anno = request.args.get('anno')

    query = Ordine.query
    if anno:
        query = query.filter(db.extract('year', Ordine.data) == int(anno))
    if mese:
        query = query.filter(db.extract('month', Ordine.data) == int(mese))

    ordini = query.all()
    totale = sum(o.totale for o in ordini)
    return render_template('report.html', ordini=ordini, totale=totale, mese=mese, anno=anno)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
