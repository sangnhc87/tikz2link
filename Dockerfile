# Bắt đầu từ image Python 3.11 gọn nhẹ
FROM python:3.11-slim

# Cài đặt các phần mềm hệ thống cần thiết
# Thêm 'poppler-utils' để có pdftocairo
RUN apt-get update && apt-get install -y \
    wget \
    libgraphite2-3 \
    poppler-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Tải, giải nén và cài đặt Tectonic phiên bản 0.15.0
RUN wget -q https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz -O /tmp/tectonic.tar.gz \
    && mkdir -p /opt/tectonic \
    && tar -xzf /tmp/tectonic.tar.gz -C /opt/tectonic \
    && ln -s /opt/tectonic/tectonic /usr/local/bin/tectonic \
    && rm /tmp/tectonic.tar.gz

# Đặt thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt các thư viện Python
COPY requirements.txt .
# Gunicorn cần được cài đặt ở đây
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của ứng dụng
COPY . .

# Mở cổng 8080
EXPOSE 8080

# Chạy ứng dụng bằng Gunicorn cho môi trường production
# Đây là cách chạy đúng đắn trên server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:app"]