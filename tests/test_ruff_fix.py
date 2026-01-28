import ast
import tempfile
import pytest
from pathlib import Path

from single_spec.utils import ruff_fix, get_needed_imports


@pytest.fixture
def sample_code():
    return """import torch
import requests
from PIL import Image
from io import BytesIO
from transformers import pipeline
from typing import List, Any, Dict
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from single_spec import required_cls


class Grounding(BaseTool):
    name: str = "grounding"
    description: str = "Return bounding boxes for target entities in the image."
    args_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "image_url": {"type": "string", "description": "image url"},
            "labels": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "threshold": {
                "type": "number",
                "default": 0.3,
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
        "required": ["image_url", "labels"],
    }
    _detector: Any = None

    def _get_detector(self):
        if self._detector is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._detector = pipeline(
                model="IDEA-Research/grounding-dino-tiny",
                task="zero-shot-object-detection",
                device=device,
            )
        return self._detector

    def _run(
        self,
        image_url: str,
        labels: List[str],
        threshold: float = 0.3,
    ):
        img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
        labels = [label if label.endswith(".") else label + "." for label in labels]
        detector = self._get_detector()
        results = detector(img, candidate_labels=labels, threshold=threshold)
        return [result["box"] for result in results]
"""


def test_ruff_fix(sample_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "example_out.py"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(sample_code)
        ruff_fix(tmp_file)

        with open(tmp_file, "r", encoding="utf-8") as f:
            fixed_code = f.read()
            # Verify unused imports were removed
            assert "ChatOllama" not in fixed_code
            assert "create_agent" not in fixed_code

            # Verify used imports are still present
            assert "import torch" in fixed_code
            assert "from PIL import Image" in fixed_code


def test_get_needed_imports(sample_code):
    needed = get_needed_imports(
        ast.parse(sample_code).body[10],  # The Grounding class
        [
            ast.parse("import torch").body[0],
            ast.parse("import requests").body[0],
            ast.parse("from PIL import Image").body[0],
            ast.parse("from io import BytesIO").body[0],
            ast.parse("from transformers import pipeline").body[0],
            ast.parse("from typing import List, Any, Dict").body[0],
            ast.parse("from langchain.tools import BaseTool").body[0],
            ast.parse("from langchain_ollama import ChatOllama").body[0],
            ast.parse("from langchain.agents import create_agent").body[0],
            ast.parse("from single_spec import required_cls").body[0],
        ],
    )
    # Should have 7 imports (removed ChatOllama, create_agent, required_cls)
    assert len(needed) == 7
    assert "import torch" in needed
    assert "import requests" in needed
    assert "from PIL import Image" in needed
    assert "from io import BytesIO" in needed
    assert "from transformers import pipeline" in needed
    assert "from typing import List, Any, Dict" in needed
    assert "from langchain.tools import BaseTool" in needed

    # Verify unused imports were removed
    assert "ChatOllama" not in str(needed)
    assert "create_agent" not in str(needed)
    assert "required_cls" not in str(needed)
