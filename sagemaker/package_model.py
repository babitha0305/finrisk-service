"""Package risk-factor passages (with theme tags) into model.tar.gz for SageMaker."""
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.data import load_chunks  # noqa: E402

out = ROOT / "sagemaker" / "build"
out.mkdir(exist_ok=True)
(out / "chunks.json").write_text(json.dumps(load_chunks()), encoding="utf-8")
with tarfile.open(out / "model.tar.gz", "w:gz") as tar:
    tar.add(out / "chunks.json", arcname="chunks.json")
print("wrote", out / "model.tar.gz")
