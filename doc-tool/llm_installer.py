import subprocess
import sys
import os
import json
import requests

MODELS = {
    "1": {
        "name": "TinyLlama-7B",
        "index_url": "https://huggingface.co/TinyLlama/TinyLlama_v1.1/resolve/main/model.safetensors.index.json"
    },
    "2": {
        "name": "Llama-2-13B",
        "index_url": "https://huggingface.co/meta-llama/Llama-2-13b-hf/resolve/main/model.safetensors.index.json"
    },
    "3": {
        "name": "Qwen2.5-Coder-32B",
        "index_url": "https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct/resolve/main/model.safetensors.index.json"
    }
}

MODEL_DIR = "./models"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def run_cmd(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0

def download_file(url, dest_path):
    ensure_dir(os.path.dirname(dest_path))
    if shutil.which("aria2c"):
        cmd = ["aria2c", "-x16", "-s16", "-k1M", "-o", os.path.basename(dest_path), "-d", os.path.dirname(dest_path), url]
        if run_cmd(cmd):
            return True
        print("aria2c failed, trying wget...")
    if shutil.which("wget"):
        cmd = ["wget", "-O", dest_path, url]
        if run_cmd(cmd):
            return True
        print("wget failed, trying curl...")
    if shutil.which("curl"):
        cmd = ["curl", "-L", "-o", dest_path, url]
        if run_cmd(cmd):
            return True
        print("curl failed.")
    print(f"All download methods failed for {url}")
    return False

def fetch_and_download_index(index_url, model_name):
    print(f"Fetching index from {index_url}")
    try:
        r = requests.get(index_url)
        r.raise_for_status()
        index_json = r.json()
    except Exception as e:
        print(f"Failed to fetch index: {e}")
        return False

    base_url = index_url.rsplit("/", 1)[0]
    files = index_json.get("weight_map", {}).values()

    if not files:
        print(f"No files listed in index for {model_name}.")
        return False

    for file in set(files):
        file_url = f"{base_url}/{file}"
        dest_path = f"{MODEL_DIR}/{model_name}/{file}"
        print(f"Downloading {file_url} -> {dest_path}")
        if not download_file(file_url, dest_path):
            print(f"Failed to download {file_url}")
            return False

    print(f"All parts downloaded for {model_name}")
    return True

def prompt_model_choice():
    print("Select LLM model to install:")
    for k, v in MODELS.items():
        print(f"{k}. {v['name']}")
    choice = input(f"Enter 1-{len(MODELS)}: ").strip()
    if choice not in MODELS:
        print("Invalid selection. Exiting.")
        sys.exit(1)
    return MODELS[choice]

def main():
    import shutil
    ensure_dir(MODEL_DIR)
    model = prompt_model_choice()
    model_name = model["name"]
    index_url = model["index_url"]

    print(f"Starting installation for {model_name}...")
    if not fetch_and_download_index(index_url, model_name):
        print(f"Failed to download model {model_name}.")
        sys.exit(1)

    print(f"Installation complete for {model_name}. Returning to main program.")

if __name__ == "__main__":
    main()
