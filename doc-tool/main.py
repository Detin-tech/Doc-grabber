import subprocess
import sys
import os
from utils import domain_to_folder

def run_step(script, args=[]):
    print(f"\n--- Running {script} ---")
    result = subprocess.run([sys.executable, script] + args)
    if result.returncode != 0:
        print(f"Error: {script} exited with code {result.returncode}")
        sys.exit(result.returncode)

def prompt_mode():
    print("Choose mode:")
    print("1. Raw (no model, just URL processing)")
    print("2. Raw + LLM model (launch installer script)")
    choice = input("Enter 1 or 2: ").strip()
    if choice not in ('1', '2'):
        print("Invalid choice. Exiting.")
        sys.exit(1)
    return choice

if __name__ == "__main__":
    mode = prompt_mode()
    if mode == '2':
        run_step("llm_installer.py")  # No args, just installs, no URL input here

    root_url = input("Enter the root URL to scrape (e.g. https://docs.openwebui.com): ").strip()
    if not root_url.startswith("http"):
        print("Invalid URL, must start with http or https")
        sys.exit(1)

    output_folder = domain_to_folder(root_url)
    os.makedirs(output_folder, exist_ok=True)

    run_step("sitemap.py", [root_url, output_folder])
    run_step("scraper.py", [os.path.join(output_folder, "urls.txt"), output_folder])
    run_step("link_converter.py", [output_folder])
    run_step("cleaner.py", [output_folder])

    print("\nAll steps completed.")
