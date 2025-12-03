import os
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from fastapi import HTTPException


class AtomicWriter:
    @staticmethod
    @contextmanager
    def write_atomic(target_path: Path):
        temp_path = None
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(
                dir=target_path.parent,
                prefix=".tmp_",
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)
                yield temp_path
            
            os.replace(temp_path, target_path)
            temp_path = None
            
        except Exception as e:
            if temp_path and temp_path.exists():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")
    
    @staticmethod
    def read_atomic(file_path: Path) -> bytes:
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    @staticmethod
    def delete_atomic(file_path: Path) -> bool:
        try:
            if file_path.exists():
                os.unlink(file_path)
                return True
            return False
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")