#!/usr/bin/env python3
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

"""Seed script to populate Firestore with initial pantry items for Recomp & Pantry Coach."""

from google.cloud import firestore

# Hardcoded project ID as required for Agent Platform deployment compatibility
FIRESTORE_PROJECT = "qwiklabs-gcp-03-676fa63982a3"
COLLECTION_NAME = "pantry_items"

INITIAL_PANTRY_ITEMS = [
    {
        "id": "chicken_breast",
        "name": "Boneless Skinless Chicken Breast",
        "quantity": "600g",
        "category": "Protein",
        "calories_per_100g": 165,
        "protein_g_per_100g": 31.0,
        "carbs_g_per_100g": 0.0,
        "fat_g_per_100g": 3.6,
        "notes": "Lean protein staple for muscle preservation in deficit",
    },
    {
        "id": "egg_whites",
        "name": "Liquid Egg Whites",
        "quantity": "500ml",
        "category": "Protein",
        "calories_per_100g": 52,
        "protein_g_per_100g": 11.0,
        "carbs_g_per_100g": 0.7,
        "fat_g_per_100g": 0.2,
        "notes": "Pure high-volume protein with virtually zero fat",
    },
    {
        "id": "greek_yogurt",
        "name": "Non-Fat Plain Greek Yogurt",
        "quantity": "750g",
        "category": "Dairy",
        "calories_per_100g": 59,
        "protein_g_per_100g": 10.0,
        "carbs_g_per_100g": 3.6,
        "fat_g_per_100g": 0.4,
        "notes": "Creamy, casein-rich protein; great for breakfast or snack bowls",
    },
    {
        "id": "canned_tuna",
        "name": "Canned Wild Tuna in Water",
        "quantity": "3 cans (360g)",
        "category": "Protein",
        "calories_per_100g": 116,
        "protein_g_per_100g": 26.0,
        "carbs_g_per_100g": 0.0,
        "fat_g_per_100g": 1.0,
        "notes": "Ultra-lean, shelf-stable protein source",
    },
    {
        "id": "rolled_oats",
        "name": "Whole Rolled Oats",
        "quantity": "1000g",
        "category": "Grains",
        "calories_per_100g": 389,
        "protein_g_per_100g": 16.9,
        "carbs_g_per_100g": 66.0,
        "fat_g_per_100g": 6.9,
        "notes": "Complex slow-digesting carbohydrates for pre-workout energy",
    },
    {
        "id": "black_beans",
        "name": "Organic Canned Black Beans",
        "quantity": "2 cans (800g)",
        "category": "Grains",
        "calories_per_100g": 91,
        "protein_g_per_100g": 6.0,
        "carbs_g_per_100g": 16.0,
        "fat_g_per_100g": 0.5,
        "notes": "High dietary fiber to maximize fullness during a cut",
    },
    {
        "id": "baby_spinach",
        "name": "Fresh Baby Spinach",
        "quantity": "300g",
        "category": "Vegetables",
        "calories_per_100g": 23,
        "protein_g_per_100g": 2.9,
        "carbs_g_per_100g": 3.6,
        "fat_g_per_100g": 0.4,
        "notes": "High micronutrient density, adds meal volume for minimal calories",
    },
    {
        "id": "broccoli_florets",
        "name": "Broccoli Florets",
        "quantity": "500g",
        "category": "Vegetables",
        "calories_per_100g": 34,
        "protein_g_per_100g": 2.8,
        "carbs_g_per_100g": 7.0,
        "fat_g_per_100g": 0.4,
        "notes": "Cruciferous vegetable, essential for meal satiety",
    },
    {
        "id": "whey_isolate",
        "name": "Whey Protein Isolate (Vanilla)",
        "quantity": "900g",
        "category": "Supplements",
        "calories_per_100g": 370,
        "protein_g_per_100g": 85.0,
        "carbs_g_per_100g": 3.0,
        "fat_g_per_100g": 1.5,
        "notes": "Rapidly absorbing post-workout muscle protein synthesis boost",
    },
    {
        "id": "olive_oil",
        "name": "Extra Virgin Olive Oil",
        "quantity": "500ml",
        "category": "Healthy Fats",
        "calories_per_100g": 884,
        "protein_g_per_100g": 0.0,
        "carbs_g_per_100g": 0.0,
        "fat_g_per_100g": 100.0,
        "notes": "Heart-healthy fats; measure strictly by tsp/tbsp during deficit",
    },
]


def seed_database():
    print(f"Connecting to Firestore project: '{FIRESTORE_PROJECT}'...")
    db = firestore.Client(project=FIRESTORE_PROJECT)
    collection = db.collection(COLLECTION_NAME)

    print(f"Seeding {len(INITIAL_PANTRY_ITEMS)} items into '{COLLECTION_NAME}'...")
    batch = db.batch()
    for item in INITIAL_PANTRY_ITEMS:
        item_id = item["id"]
        doc_ref = collection.document(item_id)
        data = {k: v for k, v in item.items() if k != "id"}
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        batch.set(doc_ref, data)
        print(f"  -> Prepared item: {item['name']} ({item['category']})")

    batch.commit()
    print("Database seeding completed successfully!")

    # Verify count
    docs = list(collection.stream())
    print(f"Verified: {len(docs)} documents found in '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    seed_database()
