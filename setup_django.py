import os
import subprocess

# Thiết lập biến
PROJECT_NAME = "yumspot"
APP_NAME = "yumspot"
SUPERUSER = "admin"
SUPERUSER_EMAIL = "admin@example.com"
SUPERUSER_PASS = "123"

print("🔹 Bắt đầu thiết lập Django...")

# 1️⃣ Kiểm tra & Tạo Virtual Environment với tên .venv
if not os.path.exists(".venv"):
    print("🚀 Tạo virtual environment...")
    subprocess.run(["python", "-m", "venv", ".venv"], check=True)

# 2️⃣ Kích hoạt Virtual Environment
venv_activate = os.path.join(".venv", "Scripts", "activate")
print("🔹 Kích hoạt virtual environment...")
os.system(f"{venv_activate} && echo Virtual environment activated")

# 3️⃣ Cài đặt requirements
if os.path.exists("requirements.txt"):
    print("📦 Cài đặt các thư viện từ requirements.txt...")
    subprocess.run([".venv\\Scripts\\pip", "install", "-r", "requirements.txt"], check=True)
else:
    print("⚠️ Không tìm thấy requirements.txt, cài đặt mặc định...")
    subprocess.run([".venv\\Scripts\\pip", "install", "django", "djangorestframework", "psycopg2"], check=True)

# 4️⃣ Kiểm tra thư mục chứa `manage.py`
if not os.path.exists("manage.py"):
    print("❌ Không tìm thấy manage.py! Kiểm tra lại thư mục dự án.")
    exit()

# 5️⃣ Chạy migrations
print("⚙️ Chạy migrations...")
subprocess.run([".venv\\Scripts\\python", "manage.py", "migrate"], check=True)

# 6️⃣ Kiểm tra & Tạo Superuser nếu chưa tồn tại
print("👤 Tạo Superuser...")
create_superuser_script = f"""
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='{SUPERUSER}').exists():
    User.objects.create_superuser('{SUPERUSER}', '{SUPERUSER_EMAIL}', '{SUPERUSER_PASS}')
"""
subprocess.run([".venv\\Scripts\\python", "manage.py", "shell", "-c", create_superuser_script], check=True)

# 7️⃣ Chạy server
print("🚀 Chạy server...")
subprocess.run([".venv\\Scripts\\python", "manage.py", "runserver"], check=True)
