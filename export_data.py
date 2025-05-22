import os

import django
from django.core.management import call_command

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yumspot.settings')
django.setup()

# Dump dữ liệu từ app "store" ra file UTF-8
with open("backup_data.json", "w", encoding="utf-8") as f:
	call_command("dumpdata", "store", indent=2, stdout=f)
