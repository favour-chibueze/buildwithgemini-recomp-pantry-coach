# My agent: Recomp & Pantry Coach

One-liner: A conversational agent that helps users achieve body recomposition and fat loss with customized workouts and high-protein meal plans crafted from ingredients they have at home.

Tool coverage:
- Memory: User profile (body stats, recomposition goals, daily calorie deficit and high-protein targets), equipment access/injuries, and currently available home pantry/fridge ingredients.
- Tools: `generate_meal_from_pantry` (creates high-protein, calorie-capped meals using home ingredients), `update_pantry` (adds/removes ingredients in stock), `lookup_workout` (retrieves hypertrophy routines for muscle retention), and `log_intake` (tracks daily calorie and protein totals).
- Catalog/UI: Rich Meal Cards (total calories, protein/carb/fat breakdown, ingredients used, prep instructions) and Workout Routine Cards/Tables (target muscle group, sets, reps, form cues).
- Image gen: Generates plated visuals of the custom pantry-crafted meals so users can see appetizing presentations of their deficit recipes.
- Sandbox: Calculates precise TDEE, calorie deficit targets, optimal protein ratios (e.g. g/lb or g/kg of lean mass), and exact calorie/macro totals from ingredient portions.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): code sandbox for precise macro and TDEE calculations, live nutritional API (e.g. USDA FoodData Central)
