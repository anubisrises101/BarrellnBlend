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
    name = models.CharField(max_length=100)
    ingredients = models.TextField(max_length=250)
    instructions = models.TextField(max_length=500)
    garnish = models.TextField(max_length=100)
    img_url = models.URLField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_absolute_url(self):
        return reverse("detail", kwargs={"drink_id": self.id})


client = OpenAI()

class DrinkForm(forms.ModelForm):
  class Meta:
    model = Drink
    fields = ['name', 'ingredients', 'instructions', 'garnish', 'img_url']

def generate_drink_prompt(user_input):
  response = client.Completion.create(
    model="gpt-4o",
    prompt=f"Create a cocktail drink recipe with the following ingredients: {user_input}",
    max_tokens=150,
  )
  return response.choices[0].text.strip()

@csrf_exempt
def generate_drink(request):
  if request.method == "POST":
    user_ingredients = request.POST.get("ingredients")
    drink_recipe = generate_drink_prompt(user_ingredients)
    return JsonResponse({"recipe": drink_recipe})

# In your urls.py, you would add a URL pattern for this view:
# from django.urls import path
# from . import views
# urlpatterns = [
#     path('generate_drink/', views.generate_drink, name='generate_drink'),
# ]
