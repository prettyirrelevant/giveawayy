# Generated by Django 3.2.7 on 2021-10-08 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('giveaways', '0003_add_is_eligible_column_to_participant_model'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set(),
        ),
    ]
