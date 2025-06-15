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

def prompt_output_format():
    print("Choose output format:")
    print("1. Markdown (.md)")
    print("2. Markdown + RTF (.md + .rtf)")
    print("3. HTML")
    choice = input("Enter 1, 2, or 3: ").strip()
    if choice == '1':
        return 'md'
    if choice == '2':
        return 'md+rtf'
    if choice == '3':
        return 'html'
    print("Invalid choice. Exiting.")
    sys.exit(1)

if __name__ == "__main__":
    mode = prompt_mode()
    if mode == '2':
        run_step("llm_installer.py")  # No args, just installs, no URL input here

    root_url = input("Enter the root URL to scrape (e.g. https://docs.openwebui.com): ").strip()
    if not root_url.startswith("http"):
        print("Invalid URL, must start with http or https")
        sys.exit(1)

    output_format = prompt_output_format()

    output_folder = domain_to_folder(root_url)
    os.makedirs(output_folder, exist_ok=True)

    run_step("sitemap.py", [root_url, output_folder])
    run_step("scraper.py", [os.path.join(output_folder, "urls.txt"), output_folder])
    run_step("link_converter.py", [output_folder, "--format", output_format])
    run_step("cleaner.py", [output_folder])
    if output_format != 'md':
        run_step("format_converter.py", [output_folder, output_format])

    print("\nAll steps completed.")
