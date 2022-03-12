from django.db import models


class Award(models.Model):
    """
    An award I have received or been nominated for.
    """

    title = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000, blank=True)

    class Meta:
        pass

    def __str__(self):
        return self.title


class Clip(models.Model):
    """
    A story, app or other thing I've published.
    """

    title = models.CharField(max_length=1000)
    CLIP_CHOICES = (
        ("app", "App"),
        ("lesson-plan", "Lesson plan"),
        ("story", "Story"),
        ("software", "Software"),
    )
    type = models.CharField(max_length=100, choices=CLIP_CHOICES)
    date = models.DateField()
    url = models.CharField(max_length=1000, unique=True)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return u"{}: {}".format(self.get_type_display(), self.title)

    def get_archive_url(self):
        return self.url


class SocialMediaProfile(models.Model):
    """
    A link to a social media profile I have on another site.
    """

    title = models.CharField(max_length=250)
    url = models.CharField(max_length=1000)

    class Meta:
        pass

    def __str__(self):
        return self.title


class Skill(models.Model):
    """
    A technical skill I have and will mention about on my bio page.
    """

    title = models.CharField(max_length=250)

    class Meta:
        pass

    def __str__(self):
        return self.title


class Talk(models.Model):
    """
    A public speech.
    """

    title = models.CharField(max_length=1000, help_text="The title of the talk")
    venue = models.CharField(max_length=1000, help_text="The host of the talk")
    location = models.CharField(max_length=1000, help_text="The location of the venue")
    date = models.DateField(help_text="The date of the talk")
    video_url = models.CharField(max_length=1000, blank=True)
    slides_url = models.CharField(max_length=1000, blank=True)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return self.title


class Doc(models.Model):
    """
    A tutorial or other documentation site.
    """

    title = models.CharField(max_length=1000)
    DOC_CHOICES = (
        ("lesson-plan", "Lesson plan"),
        ("software", "Software"),
    )
    type = models.CharField(max_length=100, choices=DOC_CHOICES)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000, unique=True)

    class Meta:
        ordering = ("type", "title")

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"
