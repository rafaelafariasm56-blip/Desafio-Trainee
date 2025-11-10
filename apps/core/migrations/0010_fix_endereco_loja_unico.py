from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_produto_atualizada_em_produto_disponivel_and_more'),
        ('users', '0006_remove_endereco_user_endereco_complemento_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                PRAGMA foreign_keys=off;

                CREATE TABLE IF NOT EXISTS core_lojaperfil_temp AS
                SELECT * FROM core_lojaperfil;

                DROP TABLE core_lojaperfil;

                CREATE TABLE core_lojaperfil (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    nome VARCHAR(255) NOT NULL,
                    endereco_id INTEGER NULL,
                    aberta BOOLEAN NOT NULL CHECK(aberta IN (0,1)),
                    FOREIGN KEY(user_id) REFERENCES users_user(id) ON DELETE CASCADE,
                    FOREIGN KEY(endereco_id) REFERENCES users_endereco(id) ON DELETE CASCADE
                );

                INSERT INTO core_lojaperfil (id, user_id, nome, endereco_id, aberta)
                SELECT id, user_id, nome, endereco_id, aberta FROM core_lojaperfil_temp;

                DROP TABLE core_lojaperfil_temp;

                PRAGMA foreign_keys=on;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        migrations.AlterField(
            model_name='lojaperfil',
            name='endereco',
            field=models.ForeignKey(
                to='users.Endereco',
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                blank=True,
                related_name='lojas',
            ),
        ),
    ]
