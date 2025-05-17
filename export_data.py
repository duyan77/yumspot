from django.core.management import call_command

with open("data.json", "w", encoding="utf-8") as f:
    call_command("dumpdata", "store", indent=2, stdout=f)
