# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rmg', '0005_auto_20170511_1713'),
    ]

    operations = [
        migrations.AddField(
            model_name='chemkin',
            name='name',
            field=models.CharField(default=b'no_account', max_length=20),
        ),
    ]
