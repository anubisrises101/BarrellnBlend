from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
import os, environ, openai, re
from .models import Drink
from django.conf import settings
from openai import OpenAI
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy

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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        else:
            error_message = "Invalid sign up - try again"
    form = UserCreationForm()
    context = {"form": form, "error_message": error_message}
    return render(request, "signup.html", context)


def generate_drink_prompt(user_input):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a cocktail recipe creator. Your task is to create a drink recipe based on the user's ingredients.",
            },
            {
                "role": "user",
                "content": f"Create a cocktail using: {user_input}. Only create the drink name, ingredients, instructions. Please use complete sentences.",
            },
        ],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


# @csrf_exempt
@login_required(login_url="login")
def generate_drink(request):
    if request.method == "POST":
        user_ingredients = request.POST.get("ingredients")
        if user_ingredients:
            drink_recipe = generate_drink_prompt(user_ingredients)
            drink_recipe = (
                drink_recipe.replace("**", "")
                .replace("*", "")
                .replace("#", "")
                .replace("##", "")
                .replace("###", "")
                .replace("####", "")
                .replace("#####", "")
                .replace("######", "")
                .replace(">", "")
                .replace("Ingredients:", "")
                .replace("Instructions:", "")
                .replace("Cocktail name:", "")
                .replace("Cocktail Name:", "")
                .replace("Drink Name:", "")
                .replace("Name:", "")
                .replace("Drink name:", "")
            )
            drink_recipe = re.sub(r"\d+\. ", "<br>🍸 ", drink_recipe)
            drink_recipe = re.sub(r"- ", "<br>📍 ", drink_recipe)
            recipe_parts = drink_recipe.split("\n\n")
            recipe_name = recipe_parts[0] if len(recipe_parts) > 0 else ""
            recipe_ingredients = recipe_parts[1] if len(recipe_parts) > 1 else ""
            recipe_instructions = recipe_parts[2] if len(recipe_parts) > 2 else ""

            drink = Drink(
                name=recipe_name,
                ingredients=recipe_ingredients,
                instructions=recipe_instructions,
            )
            return render(request, "drinks/drink_detail.html", {"drink": drink})
        else:
            return render(
                request,
                "drinks/generate_drink.html",
                {"error": "Ingredients are required"},
            )
    else:
        drinks = Drink.objects.all()
        return render(request, "drinks/generate_drink.html", {"drinks": drinks})


@login_required(login_url="login")
def drink_detail(request, drink_id):
    drink = get_object_or_404(Drink, id=drink_id)
    is_user_in_bar = request.user.drinks.filter(id=drink_id).exists()
    return render(
        request,
        "drinks/drink_detail.html",
        {"drink": drink, "is_user_in_bar": is_user_in_bar},
    )


def drink_index(request):
    drinks = Drink.objects.all().order_by("-created_at")
    return render(request, "drinks/all_drinks.html", {"drinks": drinks})


@login_required
def add_to_bar(request):
    if request.method == "POST":
        name = request.POST.get("name")
        ingredients = request.POST.get("ingredients")
        instructions = request.POST.get("instructions")

        # Check if the drink already exists in the database with the same name, ingredients, and instructions
        drink = Drink.objects.filter(
            name=name, ingredients=ingredients, instructions=instructions
        ).first()

        if not drink:
            # If the drink does not exist, create it
            drink = Drink.objects.create(
                user=request.user,
                name=name,
                ingredients=ingredients,
                instructions=instructions,
            )

        # Add the new drink to the user's 'bar'
        request.user.drinks.add(drink)

        return redirect("bar")  # Redirect to the user's bar page
    return redirect("explore")


@login_required
def remove_from_bar(request, drink_id):
    request.user.drinks.remove(drink_id)
    return redirect("bar")


@login_required
def bar(request):
    drinks = request.user.drinks.all()
    print(drinks)
    return render(request, "drinks/bar.html", {"drinks": drinks})


class DrinkDelete(DeleteView):
    model = Drink
    success_url = reverse_lazy("bar")
