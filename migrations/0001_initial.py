# Generated by Django 2.2.2 on 2019-10-10 08:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Parallel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('description', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Witness',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intf_id', models.IntegerField(default=None, null=True)),
                ('year_min', models.IntegerField(default=None, null=True)),
                ('year_max', models.IntegerField(default=None, null=True)),
            ],
            options={
                'verbose_name_plural': 'Witnesses',
            },
        ),
        migrations.CreateModel(
            name='VerseLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50)),
                ('parallel', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='dcodex_carlson.Parallel')),
            ],
        ),
        migrations.CreateModel(
            name='Suppression',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parallel', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='dcodex_carlson.Parallel')),
                ('witness', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.Witness')),
            ],
        ),
        migrations.CreateModel(
            name='SubLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.Location')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Siglum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('witness', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.Witness')),
            ],
            options={
                'verbose_name_plural': 'Sigla',
            },
        ),
        migrations.CreateModel(
            name='Reading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=200)),
                ('order', models.IntegerField()),
                ('sublocation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.SubLocation')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Macro',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(default='', max_length=200)),
                ('mode', models.CharField(default='', max_length=1)),
                ('parallel', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='dcodex_carlson.Parallel')),
                ('witnesses', models.ManyToManyField(to='dcodex_carlson.Witness')),
            ],
        ),
        migrations.AddField(
            model_name='location',
            name='macros',
            field=models.ManyToManyField(to='dcodex_carlson.Macro'),
        ),
        migrations.AddField(
            model_name='location',
            name='verse_labels',
            field=models.ManyToManyField(to='dcodex_carlson.VerseLabel'),
        ),
        migrations.CreateModel(
            name='Collation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=200)),
                ('locations', models.ManyToManyField(to='dcodex_carlson.Location')),
                ('parallels', models.ManyToManyField(to='dcodex_carlson.Parallel')),
                ('suppressions', models.ManyToManyField(to='dcodex_carlson.Suppression')),
                ('witnesses', models.ManyToManyField(to='dcodex_carlson.Witness')),
            ],
        ),
        migrations.CreateModel(
            name='Attestation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=1)),
                ('corrector', models.IntegerField(default=None, null=True)),
                ('parallel', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='dcodex_carlson.Parallel')),
                ('sublocation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.SubLocation')),
                ('witness', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_carlson.Witness')),
            ],
        ),
    ]
