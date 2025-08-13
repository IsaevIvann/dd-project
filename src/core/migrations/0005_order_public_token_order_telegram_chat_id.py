# src/core/migrations/0005_public_token_and_chatid.py
from django.db import migrations, models
from uuid import uuid4

def backfill_public_token(apps, schema_editor):
    Order = apps.get_model('core', 'Order')
    # заполним пустые токены уникальными значениями
    for obj in Order.objects.filter(public_token__isnull=True):
        obj.public_token = uuid4()
        obj.save(update_fields=['public_token'])

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_order_consent_order_consent_at'),
    ]

    operations = [
        # 1) добавляем поле без unique и с null=True
        migrations.AddField(
            model_name='order',
            name='public_token',
            field=models.UUIDField(
                null=True,
                editable=False,
                db_index=True,
                verbose_name='Публичный токен заказа'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='telegram_chat_id',
            field=models.CharField(
                verbose_name='Telegram chat ID',
                max_length=64,
                blank=True,
                default=''
            ),
        ),
        # 2) заполняем существующие строки
        migrations.RunPython(backfill_public_token, migrations.RunPython.noop),
        # 3) зажимаем ограничения
        migrations.AlterField(
            model_name='order',
            name='public_token',
            field=models.UUIDField(
                null=False,
                unique=True,
                editable=False,
                db_index=True,
                verbose_name='Публичный токен заказа'
            ),
        ),
    ]
