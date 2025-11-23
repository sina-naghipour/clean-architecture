#!/usr/bin/env python3
"""
FastAPI Project Bundler
Creates a single text file containing the entire project structure and code.
"""

import os
import pathlib
import argparse
from datetime import datetime
import fnmatch

class FastAPIBundler:
    def __init__(self, project_root=".", output_file="fastapi_project_bundle.txt"):
        self.project_root = pathlib.Path(project_root).resolve()
        self.output_file = pathlib.Path(output_file)
        self.ignored_patterns = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.vscode',
            '.idea',
            'node_modules',
            'venv',
            'env',
            '.env',
            '*.log',
            'dist',
            'build',
            '*.egg-info',
            '.pytest_cache',
            '*.sqlite',
            '*.db',
            'coverage',
            '.coverage'
        ]
        
    def should_ignore(self, path):
        """Check if a path should be ignored based on patterns."""
        path_str = str(path)
        for pattern in self.ignored_patterns:
            if fnmatch.fnmatch(path.name, pattern) or pattern in path_str:
                return True
        return False
    
    def get_file_content(self, file_path):
        """Read file content, handling binary files gracefully."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return f"[BINARY FILE - {file_path}]\n"
        except Exception as e:
            return f"[ERROR READING FILE {file_path}: {str(e)}]\n"
    
    def generate_bundle(self):
        """Generate the project bundle."""
        bundle_content = []
        
        # Header
        bundle_content.append("=" * 80)
        bundle_content.append(f"FASTAPI PROJECT BUNDLE")
        bundle_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        bundle_content.append(f"Project Root: {self.project_root}")
        bundle_content.append("=" * 80)
        bundle_content.append("")
        
        # Project structure
        bundle_content.append("PROJECT STRUCTURE:")
        bundle_content.append("-" * 40)
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = pathlib.Path(root)
            
            # Filter ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
            
            # Calculate relative path for display
            try:
                rel_path = root_path.relative_to(self.project_root)
            except ValueError:
                rel_path = root_path
            
            # Add directory to structure
            indent = "  " * (len(rel_path.parts) if rel_path != pathlib.Path('.') else 0)
            bundle_content.append(f"{indent}{root_path.name}/")
            
            # Add files in this directory
            for file in files:
                file_path = root_path / file
                if not self.should_ignore(file_path):
                    file_indent = "  " * (len(rel_path.parts) + 1 if rel_path != pathlib.Path('.') else 1)
                    bundle_content.append(f"{file_indent}{file}")
        
        bundle_content.append("")
        bundle_content.append("FILE CONTENTS:")
        bundle_content.append("=" * 80)
        bundle_content.append("")
        
        # File contents
        for root, dirs, files in os.walk(self.project_root):
            root_path = pathlib.Path(root)
            
            # Filter ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                if not self.should_ignore(file_path):
                    try:
                        rel_path = file_path.relative_to(self.project_root)
                    except ValueError:
                        rel_path = file_path
                    
                    # Add file header
                    bundle_content.append(f"FILE: {rel_path}")
                    bundle_content.append("-" * 60)
                    
                    # Add file content
                    content = self.get_file_content(file_path)
                    bundle_content.append(content)
                    
                    # Add separator between files
                    bundle_content.append("\n" + "=" * 80 + "\n")
        
        return "\n".join(bundle_content)
    
    def save_bundle(self, content):
        """Save the bundle content to file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Bundle saved to: {self.output_file}")
        print(f"Total size: {len(content)} characters")

def main():
    parser = argparse.ArgumentParser(description='Bundle FastAPI project into a single text file')
    parser.add_argument('--root', '-r', default='.', 
                       help='Project root directory (default: current directory)')
    parser.add_argument('--output', '-o', default='fastapi_project_bundle.txt',
                       help='Output file name (default: fastapi_project_bundle.txt)')
    parser.add_argument('--ignore', '-i', nargs='*', 
                       help='Additional patterns to ignore')
    
    args = parser.parse_args()
    
    # Create bundler
    bundler = FastAPIBundler(project_root=args.root, output_file=args.output)
    
    # Add custom ignore patterns
    if args.ignore:
        bundler.ignored_patterns.extend(args.ignore)
    
    # Generate and save bundle
    print(f"Bundling FastAPI project from: {bundler.project_root}")
    print("This may take a moment...")
    
    bundle_content = bundler.generate_bundle()
    bundler.save_bundle(bundle_content)
    
    # Show some statistics
    lines = bundle_content.split('\n')
    files_count = bundle_content.count('FILE: ')
    print(f"Bundle contains {files_count} files and {len(lines)} lines")

if __name__ == "__main__":
    main()