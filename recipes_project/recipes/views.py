from django.db.models import Q, F
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404, render

from .models import Product, Recipe, RecipeProduct


def add_product_to_recipe(request, recipe_id, product_id, weight):
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        product = get_object_or_404(Product, id=product_id)

        recipe_product, created = RecipeProduct.objects.get_or_create(
            recipe=recipe, product=product, defaults={'weight': weight})

        if not created:
            recipe_product.weight = weight
            recipe_product.save()

        return JsonResponse({'status': 'success'})

    except (Recipe.DoesNotExist, Product.DoesNotExist) as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def cook_recipe(request, recipe_id):
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)

        with transaction.atomic():
            product_ids = RecipeProduct.objects.filter(
                recipe=recipe
                ).values_list('product_id', flat=True)

            Product.objects.filter(id__in=product_ids).update(
                preparation_count=F('preparation_count') + 1
            )

            return JsonResponse({'status': 'success'})

    except Recipe.DoesNotExist as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def show_recipes_without_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    recipes_with_low_weight = Recipe.objects.filter(
        recipeproduct__product=product,
        recipeproduct__weight__lt=10
    )

    recipes_without_product = Recipe.objects.exclude(
        Q(recipeproduct__product=product) & Q(recipeproduct__weight__gte=10)
    )

    recipes = recipes_without_product.union(recipes_with_low_weight)

    return render(
        request, 'recipes_without_product.html', {'recipes': recipes}
    )
