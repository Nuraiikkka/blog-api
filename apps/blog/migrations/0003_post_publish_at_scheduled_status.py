from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='publish_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='publish at'),
        ),
        migrations.AlterField(
            model_name='post',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published'), ('scheduled', 'Scheduled')],
                default='draft',
                max_length=20,
                verbose_name='status',
            ),
        ),
    ]
