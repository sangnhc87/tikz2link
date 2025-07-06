# app.py (phiên bản Tectonic)
import os
import subprocess
import uuid
import shutil
from flask import Flask, request, render_template, send_file, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'a_very_secret_key'

# Kiểm tra xem tectonic và pdftocairo có tồn tại không
# shutil.which sẽ tìm trong PATH, mà ta đã định nghĩa trong Dockerfile
TECTONIC_PATH = shutil.which('tectonic')
PDFTOCAIRO_PATH = shutil.which('pdftocairo')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tikz_code = request.form.get('tikz_code')

        if not tikz_code or not r'\begin{tikzpicture}' in tikz_code:
            flash('Vui lòng nhập code TikZ hợp lệ.')
            return redirect(url_for('index'))

        if not TECTONIC_PATH or not PDFTOCAIRO_PATH:
             flash('Lỗi Server: Thiếu Tectonic hoặc pdftocairo. Vui lòng liên hệ quản trị viên.', 'error')
             return redirect(url_for('index'))

        temp_dir = os.path.join('/tmp', str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            base_name = 'tikz_output'
            temp_tex_file = os.path.join(temp_dir, f'{base_name}.tex')
            # Tectonic sẽ tạo file PDF trong thư mục làm việc hiện tại,
            # nên chúng ta cần chạy lệnh từ bên trong temp_dir.
            output_pdf_file = os.path.join(temp_dir, f'{base_name}.pdf')
            output_png_file = os.path.join(temp_dir, f'{base_name}.png')

            standalone_latex_code = r"""
            \documentclass[tikz, border=5pt]{standalone}
            \usepackage[utf8]{vietnam}
            \usepackage{tikz,tikz-3dplot,tkz-tab,tkz-linknodes}
            \usepackage{xcolor}
            \usepackage{tkz-euclide,tkz-tab,pgfplots}
            \pgfplotsset{compat=newest}
            \usetikzlibrary{arrows,shapes,patterns,calc,positioning,decorations.pathreplacing,matrix,backgrounds,fadings,intersections,shadows.blur,math,through,angles,quotes,shapes.geometric}
            \begin{document}
            """ + tikz_code + r"""
            \end{document}
            """

            with open(temp_tex_file, 'w', encoding='utf-8') as f:
                f.write(standalone_latex_code)

            # 1. Chạy Tectonic
            # Tectonic cần được chạy từ thư mục chứa file .tex để nó tìm thấy file
            # Nó sẽ tự động tải các gói cần thiết và lưu vào cache
            # `--outdir .` để đảm bảo file pdf được tạo ra trong thư mục hiện tại (temp_dir)
            tectonic_process = subprocess.run(
                [TECTONIC_PATH, '--outdir', '.', temp_tex_file],
                check=True, capture_output=True, text=True, cwd=temp_dir
            )

            # 2. Dùng pdftocairo để chuyển PDF sang PNG
            subprocess.run(
                [PDFTOCAIRO_PATH, '-png', '-r', '300', '-singlefile', output_pdf_file, os.path.join(temp_dir, base_name)],
                check=True, capture_output=True, text=True
            )

            return send_file(output_png_file, mimetype='image/png', as_attachment=True, download_name='tikz_image.png')

        except subprocess.CalledProcessError as e:
            # Lấy log lỗi từ Tectonic để hiển thị
            error_log = e.stderr if e.stderr else e.stdout
            flash(f'Lỗi biên dịch Tectonic! Vui lòng kiểm tra lại code.\nChi tiết: <pre>{error_log}</pre>', 'error')
            return redirect(url_for('index'))
        except FileNotFoundError:
            flash('Không tìm thấy file kết quả. Có lỗi xảy ra trong quá trình chuyển đổi.', 'error')
            return redirect(url_for('index'))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    return render_template('index.html')

if __name__ == '__main__':
    # Chạy bằng python3 thay vì flask run
    app.run(debug=True, host='0.0.0.0', port=8080)