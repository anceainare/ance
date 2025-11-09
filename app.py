from flask import Flask, render_template, request, abort, redirect, url_for
from pathlib import Path
import sqlite3 

app = Flask(__name__)

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

@app.route('/recepte/<int:id>', methods=['GET', 'POST'])
def recepte(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        author_name = request.form.get('author_name', '').strip()
        comment_text = request.form.get('comment_text', '').strip()
        
        if author_name and comment_text:
            conn.execute(
                'INSERT INTO comments (recepte_id, author_name, comment_text) VALUES (?, ?, ?)',
                (id, author_name, comment_text)
            )
            conn.commit()
            return redirect(url_for('recepte', id=id))
    
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
    
    comments = conn.execute(
        'SELECT * FROM comments WHERE recepte_id = ? ORDER BY created_at DESC',
        (id,)
    ).fetchall()
    
    conn.close()
    
    if not recepte:
        abort(404)
        
    return render_template('recepte.html', recepte=recepte, comments=comments)

@app.route('/delete-comment/<int:id>', methods=['POST'])
def delete_comment(id):
    conn = get_db_connection()
    
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (id,)).fetchone()
    if comment:
        conn.execute('DELETE FROM comments WHERE id = ?', (id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('recepte', id=comment['recepte_id'])) if comment else abort(404)

@app.route('/par-mums')
def par_mums():
    return render_template('par_mums.html')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comments'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        cursor.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recepte_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recepte_id) REFERENCES receptes(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        print("Created comments table")
    else:
        print("Comments table already exists")
    
    conn.close()

init_db()
if __name__ == '__main__':
    app.run(debug=True)
