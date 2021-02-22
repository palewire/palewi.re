from django.contrib.contenttypes.models import ContentType


def create_ticker_item(sender, instance, signal, *args, **kwargs):
    """
    When a new object is saved, it will be added to Ticker model and therefore the site's front page.
    """
    from coltrane.models import Ticker

    # Check to see if the object was just created for the first time
    if "created" in kwargs and instance.__class__.__name__ not in ["Comment", "Change"]:
        if kwargs["created"]:
            ctype = ContentType.objects.get_for_model(instance)
            pub_date = instance.pub_date
            Ticker.objects.get_or_create(
                content_type=ctype, object_id=instance.id, pub_date=pub_date
            )
    # Check to see if the object is a comment, and it has been approved
    elif instance.__class__.__name__ == "Comment":
        if instance.is_public:
            ctype = ContentType.objects.get_for_model(instance)
            pub_date = instance.submit_date
            Ticker.objects.get_or_create(
                content_type=ctype, object_id=instance.id, pub_date=pub_date
            )
    elif instance.__class__.__name__ == "Change":
        if instance.is_public:
            ctype = ContentType.objects.get_for_model(instance)
            Ticker.objects.get_or_create(
                content_type=ctype, object_id=instance.id, pub_date=instance.pub_date
            )


def delete_ticker_item(sender, instance, signal, *args, **kwargs):
    """
    When an object is deleted, its ticker item will also be wiped out.
    """
    from coltrane.models import Ticker

    # Figure out what type of object it is
    ctype = ContentType.objects.get_for_model(instance)

    # If it's a comment, we'll need some special treatment
    # since it has a different pub date field name
    if instance.__class__.__name__ == "Comment":
        pub_date = instance.submit_date
    else:
        pub_date = instance.pub_date

    # Look for any Ticker item and delete it if it exists
    try:
        t = Ticker.objects.get(
            content_type=ctype, object_id=instance.id, pub_date=pub_date
        )
        t.delete()
    except Ticker.DoesNotExist:
        pass


def category_count(sender, instance, signal, *args, **kwargs):
    """
    Count the number of live posts associated with each Category record -- and save it back to the model.
    """
    from coltrane.models import Category

    for cat in Category.objects.all():
        cat.post_count = cat.get_live_post_count()
        cat.save()
