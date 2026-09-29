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

"""Image generation tool for meals and fitness dishes using gemini-3.1-flash-lite-image."""

import logging
import re
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

logger = logging.getLogger(__name__)

# Hardcoded project ID and public Cloud Storage bucket
PROJECT_ID = "qwiklabs-gcp-03-676fa63982a3"
BUCKET_NAME = "recomp-pantry-coach-images-676fa639"

# Lazy-loaded clients
_genai_client = None
_storage_client = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
    return _genai_client


def _get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


async def generate_meal_image(prompt: str, tool_context: ToolContext) -> str:
    """Generate an image of a recomposition meal or dish using gemini-3.1-flash-lite-image in the global region.

    Saves the image as a session artifact for the Playground Artifacts panel and uploads it directly to the
    public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: A descriptive prompt for the meal image (e.g. 'high protein grilled chicken bowl with avocado and quinoa, food photography, appetizing').
        tool_context: The ADK tool execution context (automatically injected).

    Returns:
        The public HTTPS URL of the uploaded image.
    """
    try:
        client = _get_genai_client()
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return "Error: No image content returned by the image generation model."

        # Create unique filename / object name
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt.lower())[:25].strip("_")
        object_name = f"meal_{slug}_{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save as an artifact in the session (shows up in Playground Artifacts panel)
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=object_name, artifact=artifact_part)

        # 2. Upload image bytes directly to public Cloud Storage bucket (without writing to disk)
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"
        logger.info("Image successfully uploaded to %s", public_url)
        return public_url

    except Exception as e:
        logger.exception("Failed to generate or upload meal image: %s", e)
        return f"Error generating meal image: {e}"
