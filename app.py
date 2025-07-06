import os
import subprocess
import re
import uuid
import shutil
import zipfile
from io import BytesIO
import cloudinary
import cloudinary.uploader
import cloudinary.api

from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, send_file

# ----------------- KHỞI TẠO VÀ CẤU HÌNH -----------------

app = Flask(__name__)
# Thay thế bằng một chuỗi bí mật ngẫu nhiên của riêng bạn
app.secret_key = 'a_very_long_and_random_secret_key_for_flask_sessions' 
# Giới hạn kích thước file upload là 5MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

# Cấu hình Cloudinary từ biến môi trường (đã set bằng `flyctl secrets`)
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
  secure = True
)

# ----------------- CÁC BIẾN VÀ HÀM DÙNG CHUNG -----------------

# Tìm đường dẫn đến các công cụ lúc khởi động để tránh tìm lại nhiều lần
TECTONIC_PATH = shutil.which('tectonic')
PDFTOCAIRO_PATH = shutil.which('pdftocairo')

# Template LaTeX chuẩn cho mỗi hình TikZ
STANDALONE_TEMPLATE = r"""
\documentclass[tikz, border=5pt]{{standalone}}
\usepackage[utf8]{{vietnam}}
\usepackage{{tikz,tikz-3dplot,tkz-tab,tikz-cd,tikz-qtree}}
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

    final_latex_code = STANDALONE_TEMPLATE.format(tikz_code=tikz_code)
    
    with open(temp_tex_file, 'w', encoding='utf-8') as f:
        f.write(final_latex_code)
    try:
        # Chạy Tectonic, timeout 30 giây
        subprocess.run(
            [TECTONIC_PATH, '--outdir', '.', temp_tex_file],
            check=True, capture_output=True, text=True, cwd=working_dir, timeout=30
        )
        # Chạy pdftocairo, timeout 30 giây
        subprocess.run(
            [PDFTOCAIRO_PATH, '-png', '-r', '300', '-singlefile', output_pdf_file, os.path.join(working_dir, base_name)],
            check=True, capture_output=True, text=True, timeout=30
        )
        return output_png_file
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_log = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
        print(f"Lỗi khi chuyển đổi '{base_name}': {error_log}")
        return None

# ==========================================================
# === ROUTE CHO GIAO DIỆN "PRO" (Lấy link Cloudinary) ===
# ==========================================================

@app.route('/')
def pro_uploader():
    """Trang chủ, hiển thị giao diện Pro."""
    return render_template('pro_uploader.html')

@app.route('/process-tex-file', methods=['POST'])
def process_tex_file():
    """Xử lý file .tex, upload lên Cloudinary, trả về JSON."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Không có tệp được gửi."}), 400
        
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.tex'):
        return jsonify({"success": False, "error": "Vui lòng chọn một tệp .tex hợp lệ."}), 400

    try:
        latex_content = file.read().decode('utf-8')
    except Exception as e:
        return jsonify({"success": False, "error": f"Không thể đọc tệp: {e}"}), 400
        
    tikz_parts = re.findall(r'\\begin{tikzpicture}.*?\\end{tikzpicture}', latex_content, re.DOTALL)
    
    if not tikz_parts:
        return jsonify({"success": False, "error": "Không tìm thấy môi trường tikzpicture nào trong tệp."}), 400

    # Tạo thư mục tạm duy nhất cho request này
    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)
    
    uploaded_images = []
    
    try:
        for i, tikz_part in enumerate(tikz_parts):
            base_name = f'hinh_{i+1}'
            png_path = convert_single_tikz(tikz_part, temp_dir, base_name=base_name)
            
            if png_path and os.path.exists(png_path):
                try:
                    upload_result = cloudinary.uploader.upload(
                        png_path,
                        folder="tikz_images", # Upload vào thư mục 'tikz_images' trên Cloudinary
                        public_id=f"{os.path.splitext(file.filename)[0]}_{base_name}" 
                    )
                    uploaded_images.append({
                        "original_filename": base_name + ".png",
                        "secure_url": upload_result.get('secure_url')
                    })
                except Exception as e:
                    print(f"Lỗi upload '{base_name}' lên Cloudinary: {e}")
                    # Bỏ qua nếu upload lỗi, tiếp tục với các hình khác

    finally:
        # Luôn dọn dẹp thư mục tạm dù thành công hay thất bại
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
    if not uploaded_images:
        return jsonify({"success": False, "error": "Không thể chuyển đổi hoặc upload bất kỳ hình nào. Vui lòng kiểm tra log server."}), 500
        
    return jsonify({
        "success": True, 
        "images": uploaded_images
    })

# ===================================================================
# === ROUTE CHO GIAO DIỆN "CLASSIC" (Tải về ZIP / PNG đơn) ===
# ===================================================================

@app.route('/classic')
def classic_index():
    """Hiển thị giao diện Classic."""
    return render_template('classic.html')

@app.route('/classic-upload', methods=['POST'])
def classic_upload_file():
    """Xử lý upload file và trả về file ZIP."""
    if 'file' not in request.files:
        flash('Không có tệp được gửi.', 'error')
        return redirect(url_for('classic_index'))
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.tex'):
        flash('Vui lòng chọn một tệp .tex hợp lệ.', 'error')
        return redirect(url_for('classic_index'))

    latex_content = file.read().decode('utf-8')
    tikz_parts = re.findall(r'\\begin{tikzpicture}.*?\\end{tikzpicture}', latex_content, re.DOTALL)
    if not tikz_parts:
        flash('Không tìm thấy môi trường tikzpicture nào trong tệp đã tải lên.', 'error')
        return redirect(url_for('classic_index'))
        
    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)
    generated_files = []

    try:
        for i, tikz_part in enumerate(tikz_parts):
            base_name = f'hinh_{i+1}'
            png_path = convert_single_tikz(tikz_part, temp_dir, base_name=base_name)
            if png_path:
                generated_files.append(png_path)

        if not generated_files:
            flash('Không thể chuyển đổi bất kỳ hình TikZ nào. Có thể tất cả đều bị lỗi.', 'error')
            return redirect(url_for('classic_index'))
            
        # Nén các file PNG thành file ZIP trong bộ nhớ
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f_path in generated_files:
                file_name_in_zip = os.path.basename(f_path)
                zf.write(f_path, arcname=file_name_in_zip)
        memory_file.seek(0)
        
        zip_filename = os.path.splitext(file.filename)[0] + '.zip'
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=zip_filename)

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@app.route('/classic-convert-code', methods=['POST'])
def classic_convert_code():
    """Xử lý việc dán code trực tiếp và trả về một file PNG."""
    tikz_code = request.form.get('tikz_code')
    if not tikz_code or r'\begin{tikzpicture}' not in tikz_code:
        flash('Vui lòng nhập một đoạn code TikZ hợp lệ.', 'error')
        return redirect(url_for('classic_index'))

    temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        png_path = convert_single_tikz(tikz_code, temp_dir)
        if png_path and os.path.exists(png_path):
            return send_file(png_path, mimetype='image/png', as_attachment=True, download_name='tikz_image.png')
        else:
            flash('Lỗi biên dịch LaTeX! Vui lòng kiểm tra lại code của bạn.', 'error')
            return redirect(url_for('classic_index'))
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# Dòng này không cần thiết khi deploy với Gunicorn nhưng rất hữu ích để chạy thử trên máy local
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)