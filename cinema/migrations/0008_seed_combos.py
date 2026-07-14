from django.db import migrations

def seed_combos(apps, schema_editor):
    Combo = apps.get_model('cinema', 'Combo')
    Combo.objects.create(
        name="Combo Solo",
        description="1 Bắp Ngọt Vừa + 1 Nước Ngọt (Medium)",
        price=75000
    )
    Combo.objects.create(
        name="Combo Đôi",
        description="1 Bắp Lớn + 2 Nước Ngọt (Medium)",
        price=105000
    )
    Combo.objects.create(
        name="Combo Gia Đình",
        description="2 Bắp Ngọt Vừa + 3 Nước Ngọt (Medium)",
        price=155000
    )
    Combo.objects.create(
        name="Combo Siêu Cấp VIP",
        description="1 Bắp Lớn Đặc Biệt + 2 Nước Ngọt Lớn + 1 Khoai Tây Chiên",
        price=135000
    )

class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0007_combo_bookingitem_quantity_alter_bookingitem_seat_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_combos),
    ]
