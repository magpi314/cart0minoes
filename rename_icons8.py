import os
import sys

def rename_files_in_directory(directory):
    try:
        if not os.path.isdir(directory):
            print(f"Error: The directory '{directory}' does not exist.")
            return
        for filename in os.listdir(directory):
            if filename.startswith("icons8-") and "-50" in filename:
                base_name, extension = os.path.splitext(filename)
                new_name = base_name.replace("icons8-", "", 1).replace("-50", "") + extension
                
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} -> {new_name}")
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rename_files.py <directory>")
        sys.exit(1)
    target_directory = sys.argv[1]
    rename_files_in_directory(target_directory)
