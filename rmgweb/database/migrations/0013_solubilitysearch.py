# Generated by Django 2.2.5 on 2022-02-08 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0012_auto_20210902_1652'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolubilitySearch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('solvent', models.CharField(blank=True, max_length=200, verbose_name='Solvent SMILES')),
                ('solute', models.CharField(blank=True, max_length=200, verbose_name='Solute SMILES')),
                ('temp', models.FloatField(blank=True, max_length=6, null=True, verbose_name='Temperature')),
                ('ref_solvent', models.CharField(blank=True, max_length=200, verbose_name='Ref. Solvent SMILES')),
                ('ref_solubility', models.FloatField(blank=True, max_length=10, null=True, verbose_name='Ref. Solubility')),
                ('ref_temp', models.FloatField(blank=True, max_length=6, null=True, verbose_name='Ref. Temperature')),
                ('hsub298', models.FloatField(blank=True, max_length=6, null=True, verbose_name='dHsub at 298K')),
                ('cp_gas_298', models.FloatField(blank=True, max_length=6, null=True, verbose_name='Cp_gas at 298K')),
                ('cp_solid_298', models.FloatField(blank=True, max_length=6, null=True, verbose_name='Cp_solid at 298K')),
            ],
        ),
    ]
