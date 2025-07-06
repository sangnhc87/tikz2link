# Dockerfile cuối cùng - Cài đặt sẵn các gói TeX Live

# 1. Bắt đầu từ image Python 3.11 gọn nhẹ
FROM python:3.11-slim

# 2. Cài đặt các phần mềm hệ thống cần thiết
# THÊM: texlive-latex-extra và texlive-pictures để có sẵn các gói .sty
RUN apt-get update && apt-get install -y \
    wget \
    libgraphite2-3 \
    poppler-utils \
    texlive-latex-extra \
    texlive-pictures \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 3. Tải, giải nén và cài đặt Tectonic
RUN wget -q https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz -O /tmp/tectonic.tar.gz \
    && mkdir -p /opt/tectonic \
    && tar -xzf /tmp/tectonic.tar.gz -C /opt/tectonic \
    && ln -s /opt/tectonic/tectonic /usr/local/bin/tectonic \
    && rm /tmp/tectonic.tar.gz

# 4. Thiết lập môi trường ứng dụng Python
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 5. Mở cổng 8080
EXPOSE 8080

# 6. Lệnh để chạy ứng dụng
# Giữ timeout cao để đảm bảo an toàn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "app:app"]