# Generated manually — state-only removal of the Slogan model.
#
# The production `coltrane_slogan` table is intentionally left untouched so
# that a rollback can restore the previous state without data loss. This
# migration simply tells Django's migration framework to stop tracking the
# model, removing it from the ORM and admin without dropping the table.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("coltrane", "0006_alter_beer_id_alter_book_id_alter_category_id_and_more"),
    ]

    operations = [
        # database_operations is empty: the table is preserved for rollback safety.
        # state_operations removes the model from Django's ORM and migration state.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="Slogan",
                ),
            ],
        ),
    ]
