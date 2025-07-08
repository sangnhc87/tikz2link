# ===================================================================
# ===   DOCKERFILE HOÀN CHỈNH - HỖ TRỢ THƯ MỤC 'sty'             ===
# ===================================================================

# 1. Bắt đầu từ image Python ổn định
FROM python:3.11-slim-bookworm

# 2. Cài đặt các gói hệ thống và TeX Live
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates libgraphite2-3 poppler-utils \
    texlive-latex-extra texlive-pictures texlive-fonts-recommended fontconfig \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Cài đặt Tectonic
RUN wget -q https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz -O /tmp/tectonic.tar.gz \
    && mkdir -p /opt/tectonic \
    && tar -xzf /tmp/tectonic.tar.gz -C /opt/tectonic \
    && ln -s /opt/tectonic/tectonic /usr/local/bin/tectonic \
    && rm /tmp/tectonic.tar.gz

# 4. Thiết lập môi trường ứng dụng
WORKDIR /app

# 5. Cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy toàn bộ mã nguồn (bao gồm thư mục 'sty') vào image
COPY . .

# 7. Bước chẩn đoán: In ra cây thư mục để xác nhận 'sty' đã được copy
RUN echo ">>> Các file và thư mục đã được copy vào /app:" && ls -lR /app

# 8. Thiết lập biến môi trường để LaTeX tìm kiếm trong thư mục gốc VÀ các thư mục con
#    Giá trị "/app//:" sẽ tự động tìm trong cả /app và /app/sty
ENV TEXINPUTS="/app//:"

# 9. Mở cổng
EXPOSE 8080

# 10. Lệnh chạy ứng dụng
#    Không cần "hardcode" TEXINPUTS nữa vì giải pháp trong app.py tốt hơn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "180", "app:app"]