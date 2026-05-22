import os

def find_files(target_name, search_path):
    found = []
    for root, dirs, files in os.walk(search_path):
        # Skip common heavy/system directories to speed up
        if any(p in root for p in ["AppData", ".git", "venv", "node_modules", "3d Objects", "Searches"]):
            continue
        if target_name in files:
            found.append(os.path.join(root, target_name))
    return found

if __name__ == "__main__":
    search_dir = "C:\\Users\\dmbolfarini\\Documents"
    print(f"Searching in: {search_dir}")
    
    db_files = find_files("database.py", search_dir)
    print("\nFound database.py:")
    for f in db_files:
        print(f)
        
    services_files = find_files("services.py", search_dir)
    print("\nFound services.py:")
    for f in services_files:
        print(f)
