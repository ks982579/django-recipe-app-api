# Generated by Django 3.2.15 on 2022-09-26 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20220926_0729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(blank=True, null=True, to='core.Tag'),
        ),
    ]
