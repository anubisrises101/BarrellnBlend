from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from openai import OpenAI
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your models here.


# Drink Model
class Drink(models.Model):
    name = models.CharField(max_length=255)
    ingredients = models.TextField()
    instructions = models.TextField()
    img_url = models.URLField(max_length=300, blank=True, null=True)
    user = models.ForeignKey(User, related_name='drinks_in_bar', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_absolute_url(self):
        return reverse("detail", kwargs={"drink_id": self.id})