from django.db import models


class DefaultModel(models.Model):
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    class Meta:
        abstract = True


class City(DefaultModel):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    country_code = models.CharField(max_length=2)
    country = models.CharField(max_length=255)
    timezone = models.CharField(max_length=255)
    data = models.JSONField(default=dict)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'country_code'], name='unique_city')
        ]
        indexes = [
            models.Index(fields=["name", "country_code"]),
            models.Index(fields=["latitude", "longitude"]),
        ]


class WeatherDataset(DefaultModel):
    city = models.ForeignKey(City, related_name='datasets', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.city} ({self.start_date} - {self.end_date})"

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['city', 'start_date', 'end_date'], name='unique_dataset')
        ]
        indexes = [
            models.Index(fields=["city", "start_date", "end_date"]),
        ]


class WeatherHour(DefaultModel):
    dataset = models.ForeignKey(WeatherDataset, related_name='hours', on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    temperature = models.FloatField()
    precipitation = models.FloatField()

    def __str__(self):
        return f"{self.dataset} [{self.timestamp}]"

    class Meta:
        ordering = ['-timestamp']
        constraints = [
            models.UniqueConstraint(fields=['dataset', 'timestamp'], name='unique_hour')
        ]
        indexes = [
            models.Index(fields=["dataset", "timestamp"]),
        ]
