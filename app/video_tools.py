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

"""Video generation tool for meals and fitness items using Google's Omni model (gemini-omni-flash-preview)."""

import base64
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


async def generate_meal_video(prompt: str, tool_context: ToolContext) -> str:
    """Generate a short video for an item in the coach's domain (meals, recipes, exercise form) using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video as a session artifact for the Playground's Artifacts panel and uploads it directly to the
    public Cloud Storage bucket, returning the public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>).

    Args:
        prompt: A descriptive prompt for the video (e.g. 'cinematic 3-second video of plating a high-protein grilled chicken and quinoa bowl' or '3-second video of steaming seasoned broccoli and salmon').
        tool_context: The ADK tool execution context (automatically injected).

    Returns:
        The public HTTPS URL of the uploaded video (https://storage.googleapis.com/<bucket>/<object>).
    """
    try:
        client = _get_genai_client()
        logger.info("Generating video with gemini-omni-flash-preview for prompt: %s", prompt)

        # Call Google's Omni model via Interactions API in global region
        response = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            response_format=[{"type": "video", "duration": "3s"}],
        )

        video_bytes = None
        mime_type = "video/mp4"

        # Extract output video bytes from response
        output_video = getattr(response, "output_video", None)
        if output_video is None and isinstance(response, dict):
            output_video = response.get("output_video")

        if output_video:
            raw_data = getattr(output_video, "data", None) or (output_video.get("data") if isinstance(output_video, dict) else None)
            if raw_data:
                if isinstance(raw_data, str):
                    video_bytes = base64.b64decode(raw_data)
                elif isinstance(raw_data, bytes):
                    video_bytes = raw_data
            mtype = getattr(output_video, "mime_type", None) or (output_video.get("mime_type") if isinstance(output_video, dict) else None)
            if mtype:
                mime_type = mtype

        # Fallback: scan steps if output_video attribute wasn't populated
        if not video_bytes:
            steps = getattr(response, "steps", None) or (response.get("steps") if isinstance(response, dict) else [])
            for step in steps or []:
                content = getattr(step, "content", None) or (step.get("content") if isinstance(step, dict) else [])
                for part in content or []:
                    part_type = getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)
                    if part_type == "video":
                        part_data = getattr(part, "data", None) or (part.get("data") if isinstance(part, dict) else None)
                        if part_data:
                            if isinstance(part_data, str):
                                video_bytes = base64.b64decode(part_data)
                            elif isinstance(part_data, bytes):
                                video_bytes = part_data
                            mtype = getattr(part, "mime_type", None) or (part.get("mime_type") if isinstance(part, dict) else None)
                            if mtype:
                                mime_type = mtype
                            break
                if video_bytes:
                    break

        if not video_bytes:
            return "Error: No video content returned by gemini-omni-flash-preview."

        # Create unique filename / object name
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt.lower())[:25].strip("_")
        object_name = f"meal_video_{slug}_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save as an artifact in the session (shows up in Playground Artifacts panel)
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=object_name, artifact=artifact_part)

        # 2. Upload video bytes directly to public Cloud Storage bucket (without writing to disk)
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"
        logger.info("Video successfully uploaded to %s", public_url)
        return public_url

    except Exception as e:
        logger.exception("Failed to generate or upload meal video: %s", e)
        return f"Error generating meal video: {e}"
