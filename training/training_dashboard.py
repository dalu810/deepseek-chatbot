import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from rag_db import (
    get_all_materials,
    insert_material,
    delete_materials_by_ids,
    update_material,
    create_rag_chunks_table,
    reprocess_embeddings_from_db
)
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET'])
def index():
    materials = get_all_materials()
    return render_template('training.html', materials=materials)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        flash('No file selected.', 'danger')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"{os.path.splitext(filename)[0]}_{timestamp}.csv"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    file.save(filepath)

    added, updated = 0, 0
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header_skipped = False
        for row in reader:
            if not header_skipped:
                header_skipped = True
                continue
            if len(row) >= 2:
                question = row[0].strip()
                answer = row[1].strip()
                status = insert_material(question, answer)
                if status == 'added':
                    added += 1
                elif status == 'updated':
                    updated += 1

    flash(f'{added} added, {updated} updated.', 'success')
    return redirect(url_for('index'))

@app.route('/delete_selected', methods=['POST'])
def delete_selected():
    ids = request.form.getlist('selected_ids[]')
    if ids:
        ids = list(map(int, ids))  # Cast to integers
        delete_materials_by_ids(ids)
        flash(f'{len(ids)} item(s) deleted.', 'success')
    else:
        flash('No items selected.', 'warning')
    return redirect(url_for('index'))

@app.route('/reprocess_chunks', methods=['POST'])
def reprocess_chunks():
    reprocess_embeddings_from_db()
    flash('Reprocessed all embeddings.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
