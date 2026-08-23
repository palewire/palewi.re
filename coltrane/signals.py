def category_count(sender, instance, signal, *args, **kwargs):
    """
    Count the number of live posts associated with each Category record -- and save it back to the model.
    """
    from coltrane.models import Category

    for cat in Category.objects.all():
        cat.post_count = cat.get_live_post_count()
        cat.save()
