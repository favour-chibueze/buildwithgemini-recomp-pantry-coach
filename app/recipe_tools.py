# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Recipe search integration using TheMealDB public API."""

import json
import os
import urllib.parse
import urllib.request


def search_public_recipes(query: str) -> str:
    """Search for real recipes, ingredients, and cooking instructions via TheMealDB public API.

    Useful for finding meal preparation ideas and recipes that match ingredients available in the pantry.

    Args:
        query: Recipe name or main ingredient to search for (e.g. 'chicken', 'tuna', 'salad', 'salmon').

    Returns:
        Formatted recipe details including dish name, category, ingredients with measurements, and cooking instructions.
    """
    api_key = os.getenv("MEALDB_API_KEY", "1")
    clean_query = query.strip()
    encoded = urllib.parse.quote(clean_query)

    search_url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded}"
    req = urllib.request.Request(search_url, headers={"User-Agent": "RecompCoach/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"Error contacting recipe database: {e}"

    meals = data.get("meals")
    if not meals:
        # Fallback to search by ingredient
        filter_url = f"https://www.themealdb.com/api/json/v1/{api_key}/filter.php?i={encoded}"
        try:
            req_filter = urllib.request.Request(filter_url, headers={"User-Agent": "RecompCoach/1.0"})
            with urllib.request.urlopen(req_filter, timeout=10) as resp:
                filter_data = json.loads(resp.read().decode("utf-8"))
                filtered_meals = filter_data.get("meals")
                if filtered_meals:
                    names = [m.get("strMeal", "") for m in filtered_meals[:4] if m.get("strMeal")]
                    return (
                        f"Found recipes featuring '{clean_query}':\n"
                        + "\n".join(f"- {name}" for name in names)
                        + "\n\nTip: Call again with a specific dish name to get full preparation instructions."
                    )
        except Exception:
            pass
        return f"No recipes found for '{clean_query}' in the public database."

    results = []
    for meal in meals[:2]:
        name = meal.get("strMeal", "Unknown")
        category = meal.get("strCategory", "General")
        area = meal.get("strArea", "International")
        instructions = meal.get("strInstructions", "").strip()

        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}")
            meas = meal.get(f"strMeasure{i}")
            if ing and ing.strip():
                measure_str = f" ({meas.strip()})" if meas and meas.strip() else ""
                ingredients.append(f"{ing.strip()}{measure_str}")

        if len(instructions) > 350:
            instructions = instructions[:350] + "..."

        results.append(
            f"Dish: {name} ({category} - {area})\n"
            f"Ingredients: {', '.join(ingredients)}\n"
            f"Preparation: {instructions}"
        )

    return "\n\n---\n\n".join(results)
