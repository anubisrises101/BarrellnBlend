from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
import os, environ, openai, re
from .models import Drink
from django.conf import settings
from openai import OpenAI

openai.api_key = settings.OPENAI_API_KEY
# Create your views here.
client = OpenAI()


class Home(LoginView):
    template_name = "home.html"


def about(request):
    return render(request, "about.html")


def signup(request):
    error_message = ""
    if request.method == "POST":
        # This is how to create a 'user' form object
        # that includes the data from the browser
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This will add the user to the database
            user = form.save()
            # This is how we log a user in
            login(request, user)
            return redirect("home")
        else:
            error_message = "Invalid sign up - try again"
    # A bad POST or a GET request, so render signup.html with an empty form
    form = UserCreationForm()
    context = {"form": form, "error_message": error_message}
    return render(request, "signup.html", context)
    # Same as:
    # return render(
    #     request,
    #     'signup.html',
    #     {'form': form, 'error_message': error_message}
    # )


def generate_drink_prompt(user_input):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a cocktail recipe creator. Your task is to create a drink recipe based on the user's ingredients."},
            {
                "role": "user",
                "content": f"Create a cocktail using only: {user_input}. Include the drink name, ingredients, instructions, and garnish."
            },
        ],
        max_tokens=150,
    )
    print(response)
    return response.choices[0].message.content.strip()


@csrf_exempt
def generate_drink(request):
    if request.method == "POST":
        user_ingredients = request.POST.get("ingredients")
        if user_ingredients:
            drink_recipe = generate_drink_prompt(user_ingredients)
            # potentially remove markdown text
            drink_recipe = drink_recipe.replace("**", "").replace("*", "").replace("#", "").replace("##", "").replace("###", "").replace("####", "").replace("#####", "").replace("######", "").replace(">", "").replace("Ingredients:", "").replace("Instructions:", "").replace("Garnish:", "")
            drink_recipe = re.sub(r"\d+\. ", "<br>🍸 ", drink_recipe)
            drink_recipe = re.sub(r"- ", "<br>🥃 ", drink_recipe)
            
            # drink_recipe.replace(r"\d+\. ", "<br><br><br>")
            recipe_parts = drink_recipe.split("\n\n")
            recipe_name = recipe_parts[0] if len(recipe_parts) > 0 else ""
            recipe_ingredients = recipe_parts[1] if len(recipe_parts) > 1 else ""
            recipe_instructions = recipe_parts[2] if len(recipe_parts) > 2 else ""
            recipe_garnish = recipe_parts[3] if len(recipe_parts) > 3 else ""

            drink = Drink.objects.create(
                name=recipe_name,
                ingredients=recipe_ingredients,
                instructions=recipe_instructions,
                garnish=recipe_garnish,
                user=request.user,
            )
            return redirect("generate_drink")
        else:
            return render(
                request,
                "drinks/generate_drink.html",
                {"error": "Ingredients are required"},
            )
    else:
        drinks = Drink.objects.all()
        return render(request, "drinks/generate_drink.html", {"drinks": drinks})
