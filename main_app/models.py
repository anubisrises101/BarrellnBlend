from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

# Create your models here.

# Drink Model
class Drink(models.Model):
    name = models.CharField(max_length=100)
    ingredients = models.TextField(max_length=250)
    instructions = models.TextField(max_length=500)
    garnish = models.TextField(max_length=100)
    img_url = models.URLField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.id})'

    def get_absolute_url(self):
        return reverse('detail', kwargs={'drink_id': self.id})