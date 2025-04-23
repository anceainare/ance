from flask import Flask, render_template, request, abort
from pathlib import Path
import sqlite3

app = Flask(__name__)

# Si lieta nestrada, es salaboju
# app.config['DATABASE'] = 'receptes.db'

# def get_db_connection():
#     conn = sqlite3.connect(app.config['DATABASE'])
#     conn.row_factory = sqlite3.Row
#     return conn

DATABASE = Path(__file__).parent / 'receptes.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    kategorijas = conn.execute('SELECT id, nosaukums FROM kategorijas').fetchall()
    receptes = conn.execute('''
        SELECT r.id, r.nosaukums, r.image, k.nosaukums AS kategorija
        FROM receptes r
        JOIN kategorijas k ON r.kategorijas_id = k.id
        ORDER BY r.nosaukums
    ''').fetchall()
    conn.close()
    return render_template('index.html', kategorijas=kategorijas, receptes=receptes)

@app.route('/visas-receptes')
def visas_receptes():
    conn = get_db_connection()
    
    kategorija_id = request.args.get('kategorija', '')
    sarezgitiba_id = request.args.get('sarezgitiba', '')
    laiks_id = request.args.get('laiks', '')
    
    query = '''
        SELECT r.id, r.nosaukums, r.image,
               k.nosaukums AS kategorija,
               s.limenis AS sarezgitiba,
               l.minutes AS laiks
        FROM receptes r
        JOIN kategorijas k ON r.kategorijas_id = k.id
        JOIN sarezgitiba s ON r.sarezgitibas_id = s.id
        JOIN laiki l ON r.laiks_id = l.id
    '''
    
    conditions = []
    params = []
    
    if kategorija_id:
        conditions.append("r.kategorijas_id = ?")
        params.append(kategorija_id)
    if sarezgitiba_id:
        conditions.append("r.sarezgitibas_id = ?")
        params.append(sarezgitiba_id)
    if laiks_id:
        conditions.append("r.laiks_id = ?")
        params.append(laiks_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY r.nosaukums"
    receptes = conn.execute(query, tuple(params)).fetchall()
    
    kategorijas = conn.execute('SELECT id, nosaukums FROM kategorijas').fetchall()
    sarezgitibas = conn.execute('SELECT id, limenis FROM sarezgitiba').fetchall()
    laiki = conn.execute('SELECT id, minutes FROM laiki').fetchall()
    
    conn.close()
    return render_template('visas_receptes.html',
                         receptes=receptes,
                         kategorijas=kategorijas,
                         sarezgitibas=sarezgitibas,
                         laiki=laiki)

@app.route('/recepte/<int:id>')
def recepte(id):
    conn = get_db_connection()
    recepte = conn.execute('''
        SELECT r.id, r.nosaukums, r.image, r.apraksts, 
               r.sastavdalas, r.instrukcijas,
               k.nosaukums AS kategorija, 
               s.limenis AS sarezgitiba,
               l.minutes AS laiks
        FROM receptes r
        JOIN kategorijas k ON r.kategorijas_id = k.id
        JOIN sarezgitiba s ON r.sarezgitibas_id = s.id
        JOIN laiki l ON r.laiks_id = l.id
        WHERE r.id = ?
    ''', (id,)).fetchone()
    
    conn.close()
    
    if not recepte:
        abort(404)
        
    return render_template('recepte.html', recepte=recepte)

@app.route('/par-mums')
def par_mums():
    return render_template('par_mums.html')

if __name__ == '__main__':
    app.run(debug=True)