# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rmg', '0002_chemkin_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chemkin',
            name='user',
        ),
    ]
