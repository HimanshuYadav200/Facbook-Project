import requests
import json
import base64
import os
import sys
import time
import random
from PIL import Image
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ImageGenAgent:
    def __init__(self, manual_mode=False):
        # User requested Imagen 3 Fast, but in 2026 we use Imagen 4 Fast
        self.model_name = "imagen-4.0-fast-generate-001" 
        
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.has_access = bool(self.api_key)
        
        # Manual mode flag - once quota is hit, stay in manual mode for ALL remaining images
        self.manual_mode = manual_mode
        if self.manual_mode:
             print("[ImageGenAgent] ⚠️ STARTED IN MANUAL MODE (API Bypassed)")
        
        if not self.has_access:
            print("[!] No GOOGLE_API_KEY found. Image generation disabled.")

    def generate_image(self, prompt, output_path):
        """
        Generates an image from prompt using Google REST API and saves to output_path.
        Retries up to 3 times for transient errors.
        """
        if not self.has_access:
            print("[!] Cannot generate image: No API Access")
            return False
        
        # If already in manual mode (quota exhausted), skip API entirely
        if self.manual_mode:
            print(f"    > [MANUAL MODE] Waiting for upload: {os.path.basename(output_path)}")
            return self._wait_for_manual_upload(output_path)

        print(f"    > Generative request: {prompt[:60]}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:predict?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "safetyFilterLevel": "warning" 
            }
        }
        
        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    # Parse predictions
                    if 'predictions' in data and len(data['predictions']) > 0:
                        b64_data = data['predictions'][0]['bytesBase64Encoded']
                        img_data = base64.b64decode(b64_data)
                        
                        image = Image.open(BytesIO(img_data))
                        image.save(output_path)
                        print(f"      [OK] Saved to {os.path.basename(output_path)}")
                        return output_path
                    else:
                        print(f"      [!] API returned 200 but no predictions: {data}")
                        
                elif response.status_code == 429: # Quota
                    if attempt < 2:
                        print("      [!] Quota limit (429). Waiting 15s...")
                        time.sleep(15)
                    else:
                        # Final attempt failed - switch to manual mode PERMANENTLY
                        print("\n" + "="*60)
                        print("⚠️  QUOTA EXHAUSTED - SWITCHING TO MANUAL UPLOAD MODE")
                        print("    (All remaining images will use manual upload)")
                        print("="*60)
                        self.manual_mode = True  # Stay in manual mode for ALL remaining images
                        return self._wait_for_manual_upload(output_path)
                elif response.status_code == 404: # Model not found
                     print(f"      [!] Model {self.model_name} not found (404). Switching...")
                     if "fast" in self.model_name:
                         # Fallback to standard
                         self.model_name = self.model_name.replace("fast-", "")
                         url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:predict?key={self.api_key}"
                         print(f"      [*] Switched to: {self.model_name}")
                     else:
                         print("      [!] Both models failed.")
                         return self._wait_for_manual_upload(output_path)
                else:
                    print(f"      [!] API Error {response.status_code}: {response.text}")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"      [!] Request Exception (Attempt {attempt+1}): {e}")
                time.sleep(2)
        
        # All retries failed - switch to manual mode
        print("\n" + "="*60)
        print("⚠️  ALL RETRIES FAILED - SWITCHING TO MANUAL UPLOAD MODE")
        print("="*60)
        return self._wait_for_manual_upload(output_path)
    
    def _wait_for_manual_upload(self, expected_path):
        """
        Waits for user to manually upload an image.
        Watches the output directory for new files and auto-renames to expected filename.
        
        Args:
            expected_path: The path where the image should be saved (e.g., visual_071.png)
            
        Returns:
            expected_path if successful, False if user cancels
        """
        output_dir = os.path.dirname(expected_path)
        expected_filename = os.path.basename(expected_path)
        
        print(f"\n📁 PLEASE UPLOAD AN IMAGE TO: {output_dir}")
        print(f"   Expected filename: {expected_filename}")
        print(f"   (Drag any image file into the folder)")
        print(f"\n   [Press Ctrl+C to skip this image]\n")
        
        # Get initial file list
        initial_files = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()
        
        # Valid image extensions
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        
        try:
            while True:
                time.sleep(1)  # Check every second
                
                # Check if expected file now exists (user might rename manually)
                if os.path.exists(expected_path) and os.path.getsize(expected_path) > 1000:
                    print(f"   ✅ Found: {expected_filename}")
                    return expected_path
                
                # Check for new files
                current_files = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()
                new_files = current_files - initial_files
                
                for new_file in new_files:
                    # Skip if it's a system file or non-image
                    _, ext = os.path.splitext(new_file)
                    if ext.lower() not in valid_extensions:
                        continue
                    
                    # Skip if it's already a visual_XXX file (might be from parallel processing)
                    if new_file.startswith("visual_"):
                        continue
                    
                    new_file_path = os.path.join(output_dir, new_file)
                    
                    # Wait a moment for file to finish copying
                    time.sleep(0.5)
                    
                    # Check file is complete (not still being copied)
                    try:
                        initial_size = os.path.getsize(new_file_path)
                        time.sleep(0.3)
                        final_size = os.path.getsize(new_file_path)
                        
                        if initial_size == final_size and final_size > 1000:
                            # File is ready - rename it
                            print(f"   📥 Detected: {new_file}")
                            print(f"   🔄 Renaming to: {expected_filename}")
                            
                            # Rename the file
                            os.rename(new_file_path, expected_path)
                            print(f"   ✅ Done! Continuing...")
                            return expected_path
                    except Exception as e:
                        print(f"   [!] Error checking file: {e}")
                        continue
                
                # Update initial files to include new visual files
                initial_files = current_files
                    
        except KeyboardInterrupt:
            print("\n   ⏭️  Skipping this image...")
            return False

    def generate_batch(self, prompts, output_dir, use_parallel=True):
        """
        Generates images for a list of prompts.
        Supports both sequential (legacy) and parallel execution.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not self.has_access:
            print("[!] Skipping Image Generation: No Valid API Key found.")
            return

        if use_parallel and len(prompts) > 1:
             return self.generate_batch_parallel(prompts, output_dir)
            
        print(f"\n>>> IMAGE GENERATION ({len(prompts)} Files) using {self.model_name}")
        
        success_count = 0
        for i, p_data in enumerate(prompts):
            filename = p_data['filename']
            prompt = p_data.get('prompt', 'Abstract background')
            
            # Enforce PNG extension if not already
            base, ext = os.path.splitext(filename)
            if ext.lower() not in ['.png', '.jpg', '.jpeg']:
                filename = f"{base}.png"
                p_data['filename'] = filename
            
            path = os.path.join(output_dir, filename)
            
            # Skip if exists
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                print(f"    [SKIP] Exists: {filename}")
                success_count += 1
                continue
            
            # Generate
            if self.generate_image(prompt, path):
                success_count += 1
            else:
                print(f"    [FAIL] Could not generate {filename}")
            
            # Rate limiting / polite delay
            time.sleep(1)
            
        return success_count

    
    def generate_batch_parallel(self, prompts, output_dir, max_workers=2):
        """
        Generates images in parallel (Speed improvement).
        Workers limited to 2 to prevent '429 Quota Exceeded' on standard tier.
        """
        import concurrent.futures
        
        print(f"\n>>> PARALLEL IMAGE GENERATION ({len(prompts)} images, {max_workers} workers)")
        
        def generate_single(prompt_obj):
            filename = prompt_obj['filename']
            # Enforce PNG
            base, ext = os.path.splitext(filename)
            if ext.lower() not in ['.png', '.jpg', '.jpeg']:
                 filename = f"{base}.png"
                 prompt_obj['filename'] = filename
            
            path = os.path.join(output_dir, filename)
            
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                print(f"    [SKIP] Exists: {filename}")
                return (filename, True, "EXISTS")
            
            # Call the core generate method
            success = self.generate_image(prompt_obj['prompt'], path)
            return (filename, success, "GENERATED" if success else "FAILED")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all
            future_to_prompt = {executor.submit(generate_single, p): p for p in prompts}
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_prompt):
                completed_count += 1
                try:
                    filename, success, status = future.result()
                    results.append((filename, success))
                except Exception as e:
                    print(f"    [!] Worker Exception: {e}")
                    results.append(("unknown", False))
        
        success_count = sum(1 for _, s in results if s)
        print(f"\n[*] Parallel Generation Complete: {success_count}/{len(prompts)} images")
        return success_count

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    agent = ImageGenAgent()
    agent.generate_image("A futuristic city", "test_out.png")

