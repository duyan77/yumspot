# Thiết lập biến
$PROJECT_NAME = "yumspot"
$APP_NAME = "yumspot"
$SUPERUSER = "admin"
$SUPERUSER_EMAIL = "admin@example.com"
$SUPERUSER_PASS = "123"

Write-Host "🔹 Bắt đầu thiết lập Django..."

# 1️⃣ Kiểm tra & Tạo Virtual Environment với tên .venv
if (!(Test-Path ".venv")) {
    Write-Host "🚀 Tạo virtual environment..."
    python -m venv .venv
}

# 2️⃣ Kích hoạt Virtual Environment
Write-Host "🔹 Kích hoạt virtual environment..."
. .\.venv\Scripts\Activate

# 3️⃣ Cài đặt requirements
if (Test-Path "requirements.txt") {
    Write-Host "📦 Cài đặt các thư viện từ requirements.txt..."
    pip install -r requirements.txt
} else {
    Write-Host "⚠️ Không tìm thấy requirements.txt, cài đặt mặc định..."
    pip install django djangorestframework psycopg2
}

# 4️⃣ Kiểm tra thư mục chứa `manage.py`
if (!(Test-Path "manage.py")) {
    Write-Host "❌ Không tìm thấy manage.py! Kiểm tra lại thư mục dự án."
    exit
}

# 5️⃣ Chạy migrations
Write-Host "⚙️ Chạy migrations..."
python manage.py migrate

# 6️⃣ Kiểm tra & Tạo Superuser nếu chưa tồn tại
Write-Host "👤 Tạo Superuser..."
$script = @"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$SUPERUSER').exists():
    User.objects.create_superuser('$SUPERUSER', '$SUPERUSER_EMAIL', '$SUPERUSER_PASS')
"@
python manage.py shell -c $script

# 7️⃣ Chạy server
python manage.py runserver
