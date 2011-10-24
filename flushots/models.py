from django.db import models


class FreeFluVaccine(models.Model):
    """
    A time and place where you can get a free flu shot here in LA county.
    """
    name = models.CharField(max_length=500)
    address = models.CharField(max_length=750)
    date = models.DateField()
    time_range = models.CharField(max_length=500)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    class Meta:
        ordering = ("date",)
    
    def __unicode__(self):
        return '%s, %s' % (self.name, self.date)

    def get_static_map(self):
        base = 'http://maps.googleapis.com/maps/api/staticmap'
        args = '?center=%s,%s&zoom=9&size=200x120&maptype=roadmap&sensor=false&markers=color:red|label:|%s,%s'
        args = args % (self.latitude, self.longitude, self.latitude, self.longitude)
        return base + args
    static_map = property(get_static_map)

    def get_map_search(self):
        return 'http://maps.google.com/maps?q=%s' % self.address
    map_search = property(get_map_search)
