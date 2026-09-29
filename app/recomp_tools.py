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

"""Macro and energy balance calculation tools for body recomposition."""


def calculate_recomp_macros(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate",
    calorie_deficit: int = 400,
) -> str:
    """Calculate TDEE and daily target macros optimized for body recomposition (fat loss + muscle preservation).

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: 'male' or 'female'.
        activity_level: Daily activity: 'sedentary' (desk job), 'light' (1-3 days/wk),
            'moderate' (3-5 days/wk), or 'active' (6-7 days/wk).
        calorie_deficit: Daily calorie deficit below maintenance (default 400 kcal).

    Returns:
        Calculated BMR, maintenance TDEE, daily target calories, and macro breakdown (protein, carbs, fat).
    """
    # BMR via Mifflin-St Jeor formula
    if gender.strip().lower().startswith("m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }
    multiplier = multipliers.get(activity_level.strip().lower(), 1.55)
    tdee = round(bmr * multiplier)
    target_calories = max(1200, tdee - calorie_deficit)

    # Recomposition targets: 2.0g protein/kg to protect lean mass, 0.8g fat/kg, remainder carbs
    protein_g = round(weight_kg * 2.0)
    protein_kcal = protein_g * 4

    fat_g = round(weight_kg * 0.8)
    fat_kcal = fat_g * 9

    carb_kcal = max(0, target_calories - protein_kcal - fat_kcal)
    carb_g = round(carb_kcal / 4)

    return (
        f"Body Recomposition Targets:\n"
        f"- Basal Metabolic Rate (BMR): {round(bmr)} kcal\n"
        f"- Maintenance Calories (TDEE): {tdee} kcal\n"
        f"- Target Daily Intake ({calorie_deficit} kcal deficit): {target_calories} kcal\n"
        f"- Protein Target: {protein_g}g ({protein_kcal} kcal) [2.0g/kg body weight for muscle retention]\n"
        f"- Fat Target: {fat_g}g ({fat_kcal} kcal) [0.8g/kg for hormonal health]\n"
        f"- Carbohydrate Target: {carb_g}g ({carb_kcal} kcal) [Fuel for resistance training]\n"
        f"- Target per meal (assuming 3 meals): ~{target_calories // 3} kcal, ~{protein_g // 3}g protein"
    )
