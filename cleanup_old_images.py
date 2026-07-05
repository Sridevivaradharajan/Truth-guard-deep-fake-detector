import os
import shutil

def main():
    # Step 1 — Check if sample_images folder exists:
    if not os.path.exists("sample_images"):
        print("sample_images folder not found — nothing to delete.")
        return

    # Step 2 — If it exists, print what is inside before deleting:
    found_items = []
    for root, dirs, files in os.walk("sample_images"):
        for d in dirs:
            dir_path = os.path.join(root, d).replace('\\', '/')
            found_items.append(dir_path)
        for f in files:
            file_path = os.path.join(root, f).replace('\\', '/')
            found_items.append(file_path)
    
    # Sort paths for consistent display order
    found_items.sort()
    for item in found_items:
        print(f"Found: {item}")

    # Step 3 — Delete the entire folder:
    shutil.rmtree("sample_images")
    print("Deleted: sample_images/ and all contents.")

    # Step 4 — Confirm deletion:
    if not os.path.exists("sample_images"):
        print("Old folder removed successfully. Ready for new structure.")
    else:
        print("ERROR: Folder could not be deleted. Check permissions.")

    # Step 5 — Update .gitignore:
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.splitlines()
        is_listed = any(line.strip() == "test_images/" or line.strip() == "test_images" for line in lines)
        
        if not is_listed:
            # Append to the end of the file, making sure there is a newline separation
            if content and not content.endswith("\n"):
                new_line_prefix = "\n"
            else:
                new_line_prefix = ""
            
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(new_line_prefix + "test_images/\n")
            print("Added test_images/ to .gitignore")
        else:
            print(".gitignore already contains test_images/ — no change needed.")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("test_images/\n")
        print("Added test_images/ to .gitignore")

if __name__ == "__main__":
    main()
