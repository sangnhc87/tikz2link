# app.py - PHIÊN BẢN SỬA LỖI CUỐI CÙNG

import os
import subprocess
import tempfile
import shutil
import glob
import re
import uuid
import zipfile
from io import BytesIO

# Import các thư viện cần thiết
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, send_file
from werkzeug.utils import secure_filename

# =====================================================================
# === THIẾT LẬP FLASK =================================================
# =====================================================================
app = Flask(__name__, template_folder='templates')
app.secret_key = 'a_very_long_and_random_secret_key_for_flask_sessions'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
  secure = True
)

# =====================================================================
# === CÁC BIẾN VÀ HÀM DÙNG CHUNG =======================================
# =====================================================================
TECTONIC_PATH = shutil.which('tectonic')
PDFTOCAIRO_PATH = shutil.which('pdftocairo')
PANDOC_PATH = shutil.which('pandoc')

STANDALONE_TEMPLATE = r"""
\documentclass[tikz, border=5pt]{{standalone}}
\usepackage[utf8]{{vietnam}}
\usepackage{{tikz,tikz-3dplot,tkz-tab,tikz-cd,tikz-qtree}}
\usepackage{{xcolor}}
\usepackage[dethi]{{ex_test}}
\usepackage{{tkz-euclide,tkz-tab,pgfplots}}
\pgfplotsset{{compat=newest}}
\usetikzlibrary{{arrows,shapes,patterns,calc,positioning,decorations.pathreplacing,matrix,backgrounds,fadings,intersections,shadows.blur,math,through,angles,quotes,shapes.geometric}}
\begin{{document}}
{tikz_code}
\end{{document}}
"""

def prepare_working_directory(working_dir, files_from_request=None):
    os.makedirs(working_dir, exist_ok=True)
    app_root = os.path.dirname(os.path.abspath(__file__))
    sty_dir = os.path.join(app_root, 'sty')
    if os.path.exists(sty_dir):
        for filename in os.listdir(sty_dir):
            if filename.endswith(".sty"):
                shutil.copy2(os.path.join(sty_dir, filename), os.path.join(working_dir, filename))
    if files_from_request:
        for file in files_from_request:
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(working_dir, filename))

def compile_full_latex_to_pdf(latex_code, working_dir):
    base_name = "document"
    temp_tex_file = os.path.join(working_dir, f'{base_name}.tex')
    with open(temp_tex_file, 'w', encoding='utf-8') as f: f.write(latex_code)
    try:
        command = [TECTONIC_PATH, '--outdir', '.', temp_tex_file]
        subprocess.run(command, check=True, cwd=working_dir, capture_output=True, text=True, timeout=90)
        subprocess.run(command, check=True, cwd=working_dir, capture_output=True, text=True, timeout=90)
        output_pdf_file = os.path.join(working_dir, f'{base_name}.pdf')
        if os.path.exists(output_pdf_file): return output_pdf_file, None
        else: return None, "Biên dịch xong nhưng không tạo ra file PDF."
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return None, e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
        
def convert_single_tikz(tikz_code, working_dir, base_name="tikz_output"):
    temp_tex_file = os.path.join(working_dir, f'{base_name}.tex')
    output_pdf_file = os.path.join(working_dir, f'{base_name}.pdf')
    output_png_file = os.path.join(working_dir, f'{base_name}.png')
    final_latex_code = STANDALONE_TEMPLATE.format(tikz_code=tikz_code)
    with open(temp_tex_file, 'w', encoding='utf-8') as f: f.write(final_latex_code)
    try:
        subprocess.run([TECTONIC_PATH, '--outdir', '.', temp_tex_file], check=True, cwd=working_dir, capture_output=True, text=True, timeout=90)
        subprocess.run([PDFTOCAIRO_PATH, '-png', '-r', '300', '-singlefile', output_pdf_file, os.path.join(working_dir, base_name)], check=True, capture_output=True, text=True, timeout=30)
        return output_png_file
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Lỗi khi chuyển đổi '{base_name}': {e.stderr if hasattr(e, 'stderr') else str(e)}")
        return None
        
# =====================================================================
# === CÁC ROUTE PHỤC VỤ GIAO DIỆN VÀ FILE TĨNH =======================
# =====================================================================
@app.route('/')
def index(): return render_template('pro_uploader.html')

@app.route('/pro-uploader')
def pro_uploader(): return render_template('pro_uploader.html')

@app.route('/classic')
def classic_index(): return render_template('classic.html')
@app.route('/editor')
def editor_index(): return render_template('editor.html')
@app.route('/soanthao')
def soanthao_page(): return render_template('soanthao.html')

@app.route('/latex-editor')
def latex_editor_page(): return render_template('latex_editor.html')

@app.route('/library')
def library():
    try:
        result = cloudinary.api.resources(type="upload", prefix="tikz_images/", max_results=100, direction="desc")
        return render_template('library.html', images=result.get('resources', []))
    except Exception as e:
        print(f"Lỗi Cloudinary: {e}"); return render_template('library.html', images=[])

# =====================================================================
# === LOGIC CHO TRANG SOẠN THẢO MỚI (soanthao.html) ==================
# =====================================================================
SESSION_DIRS = {}
@app.route('/api/init-session', methods=['POST'])
def init_session():
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join('/tmp', session_id)
    os.makedirs(temp_dir, exist_ok=True)
    SESSION_DIRS[session_id] = temp_dir
    return jsonify({"success": True, "session_id": session_id})

@app.route('/api/upload-image', methods=['POST'])
def api_upload_image():
    session_id = request.form.get('session_id')
    if not session_id or session_id not in SESSION_DIRS: return jsonify({"success": False, "error": "Phiên không hợp lệ."}), 400
    if 'image_file' not in request.files: return jsonify({"success": False, "error": "Không có file ảnh."}), 400
    file = request.files['image_file']
    if not file.filename: return jsonify({"success": False, "error": "Chưa chọn file."}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(SESSION_DIRS[session_id], filename))
    return jsonify({"success": True, "filename": filename})

@app.route('/api/compile-latex-pdf', methods=['POST'])
def api_compile_latex_pdf():
    session_id = request.form.get('session_id')
    latex_code = request.form.get('latex_code')
    if not session_id or session_id not in SESSION_DIRS: return jsonify({"success": False, "error": "Phiên không hợp lệ."}), 400
    if not latex_code: return jsonify({"success": False, "error": "Không có code LaTeX."}), 400
    working_dir = SESSION_DIRS[session_id]
    prepare_working_directory(working_dir)
    pdf_path, error_log = compile_full_latex_to_pdf(latex_code, working_dir)
    if pdf_path: return send_file(pdf_path, mimetype='application/pdf')
    else: return jsonify({"success": False, "error": error_log}), 500

# =====================================================================
# === LOGIC CHO CÁC TRANG CŨ (pro, classic) - ĐÃ KHÔI PHỤC ==============
# =====================================================================
@app.route('/process-tex-file', methods=['POST'])
def process_tex_file():
    if 'file' not in request.files: return jsonify({"success": False, "error": "Không có tệp."}), 400
    file = request.files['file']
    if not file.filename or not file.filename.endswith('.tex'): return jsonify({"success": False, "error": "File không hợp lệ."}), 400
    try: latex_content = file.read().decode('utf-8')
    except Exception as e: return jsonify({"success": False, "error": f"Lỗi đọc tệp: {e}"}), 400
    tikz_parts = re.findall(r'\\begin{tikzpicture}.*?\\end{tikzpicture}', latex_content, re.DOTALL)
    if not tikz_parts: return jsonify({"success": False, "error": "Không tìm thấy tikzpicture."}), 400
    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    uploaded_images = []
    try:
        prepare_working_directory(temp_dir)
        for i, tikz_part in enumerate(tikz_parts):
            base_name = f'hinh_{i+1}'
            png_path = convert_single_tikz(tikz_part, temp_dir, base_name=base_name)
            if png_path:
                try:
                    upload_result = cloudinary.uploader.upload(png_path, folder="tikz_images", public_id=f"{os.path.splitext(file.filename)[0]}_{base_name}")
                    uploaded_images.append({"original_filename": base_name + ".png", "secure_url": upload_result.get('secure_url')})
                except Exception as e: print(f"Lỗi upload '{base_name}': {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    if not uploaded_images: return jsonify({"success": False, "error": "Không thể xử lý hình ảnh."}), 500
    return jsonify({"success": True, "images": uploaded_images})

@app.route('/classic-upload', methods=['POST'])
def classic_upload_file():
    if 'file' not in request.files: flash('Không có tệp.', 'error'); return redirect(url_for('classic_index'))
    file = request.files['file']
    if not file.filename or not file.filename.endswith('.tex'): flash('File không hợp lệ.', 'error'); return redirect(url_for('classic_index'))
    latex_content = file.read().decode('utf-8')
    tikz_parts = re.findall(r'\\begin{tikzpicture}.*?\\end{tikzpicture}', latex_content, re.DOTALL)
    if not tikz_parts: flash('Không tìm thấy tikzpicture.', 'error'); return redirect(url_for('classic_index'))
    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    generated_files = []
    try:
        prepare_working_directory(temp_dir)
        for i, tikz_part in enumerate(tikz_parts):
            base_name = f'hinh_{i+1}'
            png_path = convert_single_tikz(tikz_part, temp_dir, base_name=base_name)
            if png_path: generated_files.append(png_path)
        if not generated_files: flash('Không thể chuyển đổi.', 'error'); return redirect(url_for('classic_index'))
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f_path in generated_files: zf.write(f_path, arcname=os.path.basename(f_path))
        memory_file.seek(0)
        zip_filename = os.path.splitext(file.filename)[0] + '.zip'
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=zip_filename)
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        
@app.route('/classic-convert-code', methods=['POST'])
def classic_convert_code():
    tikz_code = request.form.get('tikz_code')
    if not tikz_code or r'\begin{tikzpicture}' not in tikz_code: flash('Code không hợp lệ.', 'error'); return redirect(url_for('classic_index'))
    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    try:
        prepare_working_directory(temp_dir)
        png_path = convert_single_tikz(tikz_code, temp_dir)
        if png_path and os.path.exists(png_path):
            return send_file(png_path, mimetype='image/png', as_attachment=True, download_name='tikz_image.png')
        else:
            flash('Lỗi biên dịch.', 'error'); return redirect(url_for('classic_index'))
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        
# =====================================================================
# === KHỞI ĐỘNG SERVER =================================================
# =====================================================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)