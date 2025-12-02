#!/usr/bin/env python3
"""
Simple Directory Bundler
"""

import os
from pathlib import Path
from datetime import datetime

def create_bundle():
    """Create a text bundle of all text files in current directory"""
    current_dir = Path.cwd()
    output_file = current_dir / "directory_bundle.txt"
    
    print(f"Creating bundle of: {current_dir}")
    
    with open(output_file, 'w', encoding='utf-8') as bundle:
        # Write header
        bundle.write(f"Directory Bundle - {datetime.now()}\n")
        bundle.write(f"Directory: {current_dir}\n")
        bundle.write("=" * 60 + "\n\n")
        
        # Walk through directory
        file_count = 0
        
        for root, dirs, files in os.walk(current_dir):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'docs', 'static', '.git', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip some file types
                if file_path.suffix in ['.pyc', '.pyo', '.so']:
                    continue
                
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                try:
                    # Write file header
                    bundle.write(f"\n{'='*40}\n")
                    bundle.write(f"File: {file_path.relative_to(current_dir)}\n")
                    bundle.write(f"{'='*40}\n\n")
                    
                    # Try to read and write file content
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            bundle.write(content)
                            if not content.endswith('\n'):
                                bundle.write('\n')
                        file_count += 1
                    except:
                        bundle.write("[Binary or unreadable file]\n")
                        
                except Exception as e:
                    bundle.write(f"[Error: {str(e)}]\n")
        
        # Write footer
        bundle.write(f"\n{'='*60}\n")
        bundle.write(f"Total files included: {file_count}\n")
        bundle.write(f"Bundle created: {datetime.now()}\n")
    
    print(f"✓ Bundle created: {output_file}")
    print(f"✓ Files included: {file_count}")

if __name__ == "__main__":
    create_bundle()