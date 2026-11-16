"""Deploy the retriever to Amazon SageMaker Serverless Inference.

Usage (from the project root, after `python sagemaker/package_model.py`):
    python sagemaker/deploy_aws.py deploy   # upload model to S3, create serverless endpoint
    python sagemaker/deploy_aws.py test     # query the live endpoint, check parity with the API
    python sagemaker/deploy_aws.py delete   # remove endpoint, endpoint config and model

Serverless endpoints scale to zero: no charge while idle, billed per request duration.
"""
import json
import sys
import time
from pathlib import Path

import boto3

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

ENDPOINT = "finrisk-retriever"
ROLE_NAME = "finrisk-sagemaker-role"
QUERIES = ["supply chain disruption", "ransomware attack", "interest rate exposure"]


def deploy() -> None:
    import sagemaker
    from sagemaker.deserializers import JSONDeserializer
    from sagemaker.serializers import JSONSerializer
    from sagemaker.serverless import ServerlessInferenceConfig
    from sagemaker.sklearn.model import SKLearnModel

    session = sagemaker.Session()
    account = boto3.client("sts").get_caller_identity()["Account"]
    model_data = session.upload_data(str(HERE / "build" / "model.tar.gz"),
                                     key_prefix="finrisk/model")
    print("uploaded model to", model_data)

    model = SKLearnModel(
        model_data=model_data,
        role=f"arn:aws:iam::{account}:role/{ROLE_NAME}",
        entry_point=str(HERE / "inference.py"),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )
    model.deploy(
        endpoint_name=ENDPOINT,
        serverless_inference_config=ServerlessInferenceConfig(memory_size_in_mb=2048,
                                                              max_concurrency=1),
        serializer=JSONSerializer(),
        deserializer=JSONDeserializer(),
    )
    print(f"endpoint '{ENDPOINT}' is InService")


def test() -> None:
    from app.data import load_chunks
    from app.retrieval import TfidfRetriever

    runtime = boto3.client("sagemaker-runtime")
    ref = TfidfRetriever(load_chunks())
    for q in QUERIES:
        start = time.perf_counter()
        resp = runtime.invoke_endpoint(EndpointName=ENDPOINT, ContentType="application/json",
                                       Body=json.dumps({"q": q, "k": 3}))
        ms = (time.perf_counter() - start) * 1000
        sm = json.loads(resp["Body"].read())["results"]
        # Compare only relevant hits: zero-score hits are ties, returned in arbitrary order.
        sm_rel = [(h["ticker"], round(h["score"], 4)) for h in sm if h["score"] > 0]
        api_rel = [(h.chunk["ticker"], round(h.score, 4)) for h in ref.search(q, k=3) if h.score > 0]
        print(f"{q!r}: top={sm[0]['ticker']} score={sm[0]['score']} "
              f"matches_api={sm_rel == api_rel} latency={ms:.0f}ms")


def delete() -> None:
    sm = boto3.client("sagemaker")
    config = sm.describe_endpoint(EndpointName=ENDPOINT)["EndpointConfigName"]
    models = [v["ModelName"] for v in
              sm.describe_endpoint_config(EndpointConfigName=config)["ProductionVariants"]]
    sm.delete_endpoint(EndpointName=ENDPOINT)
    sm.delete_endpoint_config(EndpointConfigName=config)
    for m in models:
        sm.delete_model(ModelName=m)
    print(f"deleted endpoint '{ENDPOINT}', its config and {len(models)} model(s)")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    {"deploy": deploy, "test": test, "delete": delete}.get(
        action, lambda: sys.exit(__doc__))()
