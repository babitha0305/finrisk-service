"""Deploy the retriever with SageMaker local mode and check it matches the API."""
import sys
from pathlib import Path

from sagemaker.deserializers import JSONDeserializer
from sagemaker.local import LocalSession
from sagemaker.serializers import JSONSerializer
from sagemaker.sklearn.model import SKLearnModel

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from app.data import load_chunks  # noqa: E402
from app.retrieval import TfidfRetriever  # noqa: E402

session = LocalSession()
session.config = {"local": {"local_code": True}}

model = SKLearnModel(
    model_data="file://" + (HERE / "build" / "model.tar.gz").as_posix(),
    role="arn:aws:iam::111111111111:role/local-mode-dummy",  # not used in local mode
    entry_point="inference.py",
    source_dir=str(HERE),
    framework_version="1.2-1",
    py_version="py3",
    sagemaker_session=session,
)
predictor = model.deploy(initial_instance_count=1, instance_type="local",
                         serializer=JSONSerializer(), deserializer=JSONDeserializer())
try:
    ref = TfidfRetriever(load_chunks())
    for q in ["supply chain disruption", "ransomware attack", "interest rate exposure"]:
        sm = predictor.predict({"q": q, "k": 3})["results"]
        api = ref.search(q, k=3)
        # Compare only relevant hits: zero-score hits are ties, returned in arbitrary order.
        sm_rel = [(h["ticker"], round(h["score"], 4)) for h in sm if h["score"] > 0]
        api_rel = [(h.chunk["ticker"], round(h.score, 4)) for h in api if h.score > 0]
        same = sm_rel == api_rel
        print(f"{q!r}: top={sm[0]['ticker']} score={sm[0]['score']} matches_api={same}")
finally:
    predictor.delete_endpoint()
