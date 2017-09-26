# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('rmg', '0004_chemkin_userid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chemkin',
            name='userid',
            field=models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
