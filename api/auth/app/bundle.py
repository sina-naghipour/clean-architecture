import os
from datetime import datetime

def create_simple_bundle(root_dir=".", output_file="project_bundle.txt"):
    """Simple version for quick bundling"""
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv'}
    exclude_files = {'.env', '.gitignore'}
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(f"Project Bundle - {datetime.now()}\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(f"\n{'='*60}\n")
                        outfile.write(f"FILE: {file_path}\n")
                        outfile.write(f"{'='*60}\n\n")
                        outfile.write(infile.read())
                        outfile.write("\n")
                except:
                    continue  # Skip binary files
    
    print(f"Bundle created: {output_file}")

if __name__ == "__main__":
    create_simple_bundle()