import asyncio
import os
import glob
import subprocess
from playwright.async_api import async_playwright

OUTPUT_DIR = "/config/Desktop/BuildWithGemini/recomp-pantry-coach/demo_recordings"
FINAL_VIDEO = "/config/Desktop/BuildWithGemini/recomp-pantry-coach/demo_video.mp4"
DESKTOP_VIDEO = "/config/Desktop/demo_video.mp4"

async def record_demo():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Clean previous recordings
    for f in glob.glob(f"{OUTPUT_DIR}/*"):
        try:
            os.remove(f)
        except Exception:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/google-chrome",
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        print("Navigating to app...")
        await page.goto("http://localhost:8080", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Feature: Theme Toggle (Light -> Dark Gym Mode)
        print("Toggling Dark / Gym Mode...")
        theme_btn = page.locator("#themeToggleBtn")
        await theme_btn.hover()
        await page.wait_for_timeout(800)
        await theme_btn.click()
        await page.wait_for_timeout(1800)

        # 2. Feature: Quick Action Prompt Chips (Hover across chips)
        print("Hovering across prompt chips...")
        chips = page.locator(".prompt-chip")
        chip_count = await chips.count()
        for i in range(min(chip_count, 3)):
            await chips.nth(i).hover()
            await page.wait_for_timeout(400)

        # 3. Superpower 1: Body Recomposition Macro Target Calculation
        print("Submitting Prompt 1: Deficit Macro Targets...")
        macro_chip = page.locator(".prompt-chip >> text=Deficit Macro Targets")
        await macro_chip.hover()
        await page.wait_for_timeout(600)
        await macro_chip.click()

        # Let the viewer see the bouncing thinking indicator and dynamic stages
        print("Observing thinking status pill...")
        await page.wait_for_timeout(4000)

        # Wait for the coach response to complete
        print("Waiting for coach response...")
        await page.wait_for_function(
            "() => !document.querySelector('.typing-indicator') && document.querySelectorAll('.msg-row').length >= 2",
            timeout=60000
        )
        await page.wait_for_timeout(1500)

        # Feature: Hover over interactive Macro Visualizer and Copy Button
        print("Highlighting Macro Visualizer & Message Actions...")
        macro_bar = page.locator(".macro-bar").first
        if await macro_bar.count() > 0:
            await macro_bar.hover()
            await page.wait_for_timeout(1200)

        copy_btn = page.locator(".msg-action-btn").first
        if await copy_btn.count() > 0:
            await copy_btn.hover()
            await page.wait_for_timeout(800)

        # Scroll to view the full A2UI card
        await page.evaluate("() => { const log = document.getElementById('log'); log.scrollTop = log.scrollHeight; }")
        await page.wait_for_timeout(2500)

        # 4. Feature: Slide-out Firestore Pantry Drawer
        print("Opening Firestore Pantry Stock Drawer...")
        pantry_btn = page.locator("#pantryDrawerBtn")
        await pantry_btn.hover()
        await page.wait_for_timeout(600)
        await pantry_btn.click()
        await page.wait_for_timeout(1800)

        # Filter items in pantry drawer
        search_input = page.locator("#pantrySearch")
        await search_input.focus()
        await search_input.fill("Chicken")
        await page.wait_for_timeout(1200)

        # Insert chicken into prompt
        insert_btn = page.locator(".pantry-add-btn >> text=+ Insert in Prompt").first
        await insert_btn.hover()
        await page.wait_for_timeout(600)
        await insert_btn.click()
        await page.wait_for_timeout(1200) # Drawer slides closed automatically on insertion

        # 5. Superpower 2: Rich Tool Call, Pantry Lookup & Meal Photo Generation
        print("Submitting Prompt 2: Database Pantry Lookup & Image Gen Tool...")
        chat_input = page.locator("#input")
        additional_text = " and check my pantry database for what fresh ingredients I have to pair with it, calculate total macros, and generate an appetizing photo of the meal!"
        await chat_input.focus()
        await page.keyboard.type(additional_text, delay=15)
        await page.wait_for_timeout(600)

        # Submit via Send Button
        send_btn = page.locator(".send-btn")
        await send_btn.hover()
        await page.wait_for_timeout(400)
        await send_btn.click()

        # Observe the new dynamic thinking pill
        print("Observing dynamic thinking status steps...")
        await page.wait_for_timeout(5000)

        # Wait for agent response
        print("Waiting for database lookup, recipe & image generation...")
        await page.wait_for_function(
            "() => !document.querySelector('.typing-indicator') && document.querySelectorAll('.msg-row').length >= 4",
            timeout=95000
        )
        await page.wait_for_timeout(2000)

        # Smooth scroll to reveal recipe, macro visualizer, and generated meal photo
        print("Scrolling down to reveal full meal plan, database results, and generated photo...")
        for _ in range(6):
            await page.evaluate("() => { const log = document.getElementById('log'); log.scrollTop += 260; }")
            await page.wait_for_timeout(900)

        # Hover on the generated media card
        media_card = page.locator(".media-card").last
        if await media_card.count() > 0:
            await media_card.hover()
            await page.wait_for_timeout(1500)

        await page.wait_for_timeout(4000)

        print("Closing page and saving video...")
        await context.close()
        await browser.close()

    # Find the recorded .webm file
    webms = glob.glob(f"{OUTPUT_DIR}/*.webm")
    if not webms:
        raise RuntimeError("No recorded video found in output directory!")
    
    recorded_webm = webms[0]
    print(f"Recorded webm: {recorded_webm}")

    # Convert to MP4 using ffmpeg with high quality H.264
    cmd = [
        "ffmpeg", "-y",
        "-i", recorded_webm,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        FINAL_VIDEO
    ]
    subprocess.run(cmd, check=True)
    print(f"Final MP4 created at {FINAL_VIDEO}")

    # Also generate the looping demo.gif
    gif_path = "/config/Desktop/BuildWithGemini/recomp-pantry-coach/demo.gif"
    print("Generating optimized looping GIF...")
    gif_cmd = (
        f"ffmpeg -y -i {recorded_webm} "
        f"-vf 'fps=10,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer' "
        f"-loop 0 {gif_path}"
    )
    subprocess.run(gif_cmd, shell=True, check=True)
    print(f"Looping GIF created at {gif_path}")
    
    # Copy demo.gif to root
    try:
        import shutil
        shutil.copyfile(gif_path, "/config/Desktop/BuildWithGemini/demo.gif")
    except Exception:
        pass

    # Copy to Desktop as well for convenience
    try:
        import shutil
        shutil.copyfile(FINAL_VIDEO, DESKTOP_VIDEO)
        print(f"Copied to Desktop at {DESKTOP_VIDEO}")
    except Exception as e:
        print("Desktop copy notice:", e)

if __name__ == "__main__":
    asyncio.run(record_demo())
