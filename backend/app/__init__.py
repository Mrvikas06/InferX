"""InferX Backend Application Package."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path so 'backend.app' resolves from any working directory
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Also ensure backend directory is on sys.path so 'app.*' resolves
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
