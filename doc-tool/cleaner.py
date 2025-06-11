import sys
import os

def clean_markdown(folder):
    print(f"Cleaning markdown files in {folder}")
    removed_files = []
    removed_dirs = []

    for root, _, files in os.walk(folder, topdown=False):
        for file in files:
            if not file.endswith('.md'):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean trailing whitespace
            cleaned = '\n'.join(line.rstrip() for line in content.splitlines())

            # Normalize content to check for deletion
            normalized = cleaned.strip().lower()

            if not normalized or normalized in ['#', '# untitled_page']:
                os.remove(filepath)
                removed_files.append(filepath)
                continue  # skip saving cleaned content for deleted files

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned)

        # Clean up any now-empty directories
        if not os.listdir(root):
            os.rmdir(root)
            removed_dirs.append(root)

    print(f"Deleted {len(removed_files)} empty/untitled files.")
    print(f"Deleted {len(removed_dirs)} empty folders.")
    print("Cleanup complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cleaner.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]
    clean_markdown(folder)
