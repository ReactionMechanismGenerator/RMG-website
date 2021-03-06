# Generated by Django 2.2.5 on 2020-02-13 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0004_auto_20200213_1617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solventselection',
            name='solvent',
            field=models.CharField(blank=True, choices=[('water', 'water'), ('1-octanol', '1-octanol'), ('benzene', 'benzene'), ('cyclohexane', 'cyclohexane'), ('dibutylether', 'dibutylether'), ('octane', 'octane'), ('butanol', 'butanol'), ('carbontet', 'carbontet'), ('chloroform', 'chloroform'), ('decane', 'decane'), ('dichloroethane', 'dichloroethane'), ('dimethylformamide', 'dimethylformamide'), ('dimethylsulfoxide', 'dimethylsulfoxide'), ('dodecane', 'dodecane'), ('ethanol', 'ethanol'), ('heptane', 'heptane'), ('hexadecane', 'hexadecane'), ('hexane', 'hexane'), ('isooctane', 'isooctane'), ('nonane', 'nonane'), ('pentane', 'pentane'), ('toluene', 'toluene'), ('undecane', 'undecane'), ('acetonitrile', 'acetonitrile'), ('ethylacetate', 'ethylacetate')], max_length=200, verbose_name='Solvent (Optional)'),
        ),
    ]
