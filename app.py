# app.py (phiên bản cuối cùng, hỗ trợ cả upload file và dán code)

import os
import subprocess
import re
import uuid
import shutil
import zipfile
from io import BytesIO
from flask import Flask, request, render_template, send_file, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'a_super_duper_secret_key_that_is_long'
# Đặt giới hạn kích thước file upload (vd: 5MB)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

# Tìm đường dẫn đến các công cụ lúc khởi động
TECTONIC_PATH = shutil.which('tectonic')
PDFTOCAIRO_PATH = shutil.which('pdftocairo')

# Template LaTeX cho một hình
STANDALONE_TEMPLATE = r"""
\documentclass[tikz, border=5pt]{{standalone}}
\usepackage[utf8]{{vietnam}}
\usepackage{{tikz,tikz-3dplot,tkz-tab}}
\usepackage{{xcolor}}
\usepackage{{tkz-euclide,tkz-tab,pgfplots}}
\pgfplotsset{{compat=newest}}
\usetikzlibrary{{arrows,shapes,patterns,calc,positioning,decorations.pathreplacing,matrix,backgrounds,fadings,intersections,shadows.blur,math,through,angles,quotes,shapes.geometric}}
\begin{{document}}
{tikz_code}
\end{{document}}
"""

def convert_single_tikz(tikz_code, working_dir, base_name="tikz_output"):
    """
    Hàm chuyển đổi MỘT đoạn code TikZ thành file PNG.
    Trả về đường dẫn đến file PNG nếu thành công, None nếu thất bại.
    """
    temp_tex_file = os.path.join(working_dir, f'{base_name}.tex')
    output_pdf_file = os.path.join(working_dir, f'{base_name}.pdf')
    output_png_file = os.path.join(working_dir, f'{base_name}.png')

    # Điền code TikZ vào template
    final_latex_code = STANDALONE_TEMPLATE.format(tikz_code=tikz_code)
    
    with open(temp_tex_file, 'w', encoding='utf-8') as f:
        f.write(final_latex_code)

    try:
        # Chạy Tectonic
        subprocess.run(
            [TECTONIC_PATH, '--outdir', '.', temp_tex_file],
            check=True, capture_output=True, text=True, cwd=working_dir, timeout=30 # Thêm timeout 30s
        )
        # Chạy pdftocairo
        subprocess.run(
            [PDFTOCAIRO_PATH, '-png', '-r', '300', '-singlefile', output_pdf_file, os.path.join(working_dir, base_name)],
            check=True, capture_output=True, text=True, timeout=30 # Thêm timeout 30s
        )
        return output_png_file
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Ghi lại lỗi để có thể debug nếu cần
        error_log = e.stderr if hasattr(e, 'stderr') else str(e)
        print(f"Lỗi khi chuyển đổi {base_name}: {error_log}")
        return None

@app.route('/')
def index():
    # Trang chủ chỉ hiển thị form
    return render_template('index.html')

@app.route('/convert-code', methods=['POST'])
def convert_code():
    """Xử lý việc dán code trực tiếp."""
    tikz_code = request.form.get('tikz_code')
    if not tikz_code or r'\begin{tikzpicture}' not in tikz_code:
        flash('Vui lòng nhập một đoạn code TikZ hợp lệ.', 'error')
        return redirect(url_for('index'))

    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        png_path = convert_single_tikz(tikz_code, temp_dir)
        if png_path and os.path.exists(png_path):
            return send_file(png_path, mimetype='image/png', as_attachment=True, download_name='tikz_image.png')
        else:
            flash('Lỗi biên dịch LaTeX! Vui lòng kiểm tra lại code của bạn.', 'error')
            return redirect(url_for('index'))
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.route('/upload-file', methods=['POST'])
def upload_file():
    """Xử lý việc upload file .tex."""
    if 'file' not in request.files:
        flash('Không có phần tệp nào được gửi.', 'error')
        return redirect(url_for('index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Chưa chọn tệp nào.', 'error')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.tex'):
        latex_content = file.read().decode('utf-8')
        
        # Tìm tất cả các khối tikzpicture
        tikz_parts = re.findall(r'\\begin{tikzpicture}.*?\\end{tikzpicture}', latex_content, re.DOTALL)
        
        if not tikz_parts:
            flash('Không tìm thấy môi trường tikzpicture nào trong tệp đã tải lên.', 'error')
            return redirect(url_for('index'))

        temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        
        generated_files = []
        for i, tikz_part in enumerate(tikz_parts):
            base_name = f'hinh_{i+1}'
            png_path = convert_single_tikz(tikz_part, temp_dir, base_name=base_name)
            if png_path:
                generated_files.append(png_path)
        
        if not generated_files:
            shutil.rmtree(temp_dir)
            flash('Không thể chuyển đổi bất kỳ hình TikZ nào. Có thể tất cả đều bị lỗi.', 'error')
            return redirect(url_for('index'))

        # Tạo file ZIP trong bộ nhớ
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f_path in generated_files:
                # Đặt tên file bên trong ZIP
                file_name_in_zip = os.path.basename(f_path)
                zf.write(f_path, arcname=file_name_in_zip)
        
        # Đưa con trỏ về đầu file trong bộ nhớ
        memory_file.seek(0)
        
        # Dọn dẹp thư mục tạm
        shutil.rmtree(temp_dir)

        # Lấy tên file gốc để đặt tên cho file zip
        zip_filename = os.path.splitext(file.filename)[0] + '.zip'
        
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=zip_filename)

    else:
        flash('Chỉ chấp nhận tệp có đuôi .tex', 'error')
        return redirect(url_for('index'))

# Không cần dòng này khi dùng Gunicorn, nhưng giữ lại để debug local
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)