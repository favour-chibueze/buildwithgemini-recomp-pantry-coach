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

"""Firestore backend and function tools for pantry inventory management."""

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Hardcode project ID explicitly as required on Agent Platform to avoid project number issues
FIRESTORE_PROJECT = "qwiklabs-gcp-03-676fa63982a3"
COLLECTION_NAME = "pantry_items"

db = firestore.Client(project=FIRESTORE_PROJECT)


def list_pantry_items(category: str = "") -> str:
    """List food items currently in the home pantry inventory.

    Args:
        category: Optional category filter (e.g., 'Protein', 'Dairy', 'Vegetables', 'Grains', 'Healthy Fats').
            If empty, lists all items.

    Returns:
        A formatted summary of pantry items with their quantities and macro profiles.
    """
    try:
        col_ref = db.collection(COLLECTION_NAME)
        if category:
            query = col_ref.where(filter=FieldFilter("category", "==", category))
            docs = query.stream()
        else:
            docs = col_ref.stream()

        items = []
        for doc in docs:
            data = doc.to_dict()
            items.append(
                f"- {data.get('name', doc.id)} ({data.get('category', 'General')}): "
                f"Quantity: {data.get('quantity', 'N/A')}, "
                f"Per 100g: {data.get('calories_per_100g', 0)} kcal | "
                f"{data.get('protein_g_per_100g', 0)}g Protein | "
                f"{data.get('carbs_g_per_100g', 0)}g Carbs | "
                f"{data.get('fat_g_per_100g', 0)}g Fat"
                + (f" (Notes: {data.get('notes')})" if data.get("notes") else "")
            )

        if not items:
            cat_msg = f" in category '{category}'" if category else ""
            return f"No pantry items found{cat_msg}."

        header = f"Pantry Inventory ({len(items)} items" + (f" in '{category}'" if category else "") + "):\n"
        return header + "\n".join(items)
    except Exception as e:
        return f"Error listing pantry items: {str(e)}"


def get_pantry_item(name: str) -> str:
    """Retrieve details and nutritional information for a specific pantry item.

    Args:
        name: Name of the food item to search for.

    Returns:
        Nutritional information and stock quantity for the item, or a not-found message.
    """
    try:
        doc_id = name.strip().lower().replace(" ", "_")
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
        else:
            docs = list(db.collection(COLLECTION_NAME).stream())
            match = next((d.to_dict() for d in docs if d.to_dict().get("name", "").lower() == name.strip().lower()), None)
            if not match:
                return f"Item '{name}' was not found in the pantry."
            data = match

        return (
            f"Item: {data.get('name')}\n"
            f"Category: {data.get('category')}\n"
            f"Quantity on hand: {data.get('quantity')}\n"
            f"Macros (per 100g): {data.get('calories_per_100g')} kcal | "
            f"Protein: {data.get('protein_g_per_100g')}g | "
            f"Carbs: {data.get('carbs_g_per_100g')}g | "
            f"Fat: {data.get('fat_g_per_100g')}g\n"
            f"Notes: {data.get('notes', 'None')}"
        )
    except Exception as e:
        return f"Error retrieving pantry item: {str(e)}"


def add_or_update_pantry_item(
    name: str,
    quantity: str,
    category: str,
    calories_per_100g: int,
    protein_g_per_100g: float,
    carbs_g_per_100g: float = 0.0,
    fat_g_per_100g: float = 0.0,
    notes: str = "",
) -> str:
    """Add a new food item or update existing item details in the pantry inventory.

    Args:
        name: Name of the food item (e.g., 'Chicken Breast', 'Rolled Oats').
        quantity: Amount on hand (e.g., '500g', '4 cans', '1 kg').
        category: Food category ('Protein', 'Dairy', 'Grains', 'Vegetables', 'Healthy Fats', 'Supplements').
        calories_per_100g: Energy content in kcal per 100g.
        protein_g_per_100g: Protein in grams per 100g.
        carbs_g_per_100g: Carbohydrates in grams per 100g.
        fat_g_per_100g: Fat in grams per 100g.
        notes: Optional extra notes (e.g. brand, expiration, cooking advice).

    Returns:
        Confirmation message.
    """
    try:
        doc_id = name.strip().lower().replace(" ", "_")
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        doc_data = {
            "name": name.strip(),
            "quantity": quantity.strip(),
            "category": category.strip(),
            "calories_per_100g": calories_per_100g,
            "protein_g_per_100g": round(float(protein_g_per_100g), 1),
            "carbs_g_per_100g": round(float(carbs_g_per_100g), 1),
            "fat_g_per_100g": round(float(fat_g_per_100g), 1),
            "notes": notes.strip(),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(doc_data, merge=True)
        return (
            f"Successfully updated '{name}' in pantry: {quantity} on hand "
            f"({calories_per_100g} kcal, {protein_g_per_100g}g protein per 100g)."
        )
    except Exception as e:
        return f"Error adding/updating pantry item: {str(e)}"


def remove_pantry_item(name: str) -> str:
    """Remove a food item from the pantry inventory when used up.

    Args:
        name: Name of the food item to remove.

    Returns:
        Confirmation message.
    """
    try:
        doc_id = name.strip().lower().replace(" ", "_")
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return f"Removed '{name}' from pantry inventory."

        docs = list(db.collection(COLLECTION_NAME).stream())
        matched_doc = next((d for d in docs if d.to_dict().get("name", "").lower() == name.strip().lower()), None)
        if matched_doc:
            db.collection(COLLECTION_NAME).document(matched_doc.id).delete()
            return f"Removed '{name}' from pantry inventory."

        return f"Item '{name}' was not found in pantry inventory."
    except Exception as e:
        return f"Error removing pantry item: {str(e)}"
