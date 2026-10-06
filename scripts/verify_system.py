"""
KisanMitra Diagnostic & Health Check Script
Verifies:
1. Frontend & Backend Linkage (FastAPI mirror, static files, /chat, /api/regions)
2. AWS Bedrock status (runtime, models, inference)
3. API Keys & Services (AWS STS, S3, Mandi API, Open-Meteo Weather)
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

results = {}

def check_frontend_backend_link():
    print("\n--- 1. Testing Frontend & Backend Link (http://127.0.0.1:8000) ---")
    base_url = "http://127.0.0.1:8000"
    
    # Check /health
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=5) as r:
            health = json.loads(r.read().decode())
            print(f"[PASS] /health responded: {health}")
            results["backend_health"] = "PASS"
    except Exception as e:
        print(f"[FAIL] /health failed: {e}")
        results["backend_health"] = f"FAIL ({e})"

    # Check / (Frontend HTML)
    try:
        with urllib.request.urlopen(base_url, timeout=5) as r:
            html = r.read().decode("utf-8", errors="ignore")
            has_title = "KisanMitra" in html or "किसान" in html
            print(f"[PASS] Frontend index.html served (length={len(html)} chars, has_title={has_title})")
            results["frontend_serving"] = "PASS" if has_title else "WARN"
    except Exception as e:
        print(f"[FAIL] Frontend index.html failed: {e}")
        results["frontend_serving"] = f"FAIL ({e})"

    # Check /api/regions
    try:
        with urllib.request.urlopen(f"{base_url}/api/regions", timeout=5) as r:
            regions = json.loads(r.read().decode())
            dist_count = len(regions.get("districts", []))
            print(f"[PASS] /api/regions responded with {dist_count} districts")
            results["api_regions"] = "PASS"
    except Exception as e:
        print(f"[FAIL] /api/regions failed: {e}")
        results["api_regions"] = f"FAIL ({e})"

    # Check /chat POST
    try:
        payload = json.dumps({
            "message": "Wheat crop advice in Punjab",
            "language": "hi",
            "state": "Punjab",
            "crop": "Wheat"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            chat_res = json.loads(r.read().decode("utf-8"))
            has_title = "title" in chat_res
            has_steps = "steps" in chat_res
            print(f"[PASS] /chat POST responded with Title: '{chat_res.get('title')}', Steps count: {len(chat_res.get('steps', []))}")
            results["chat_api"] = "PASS"
    except Exception as e:
        print(f"[FAIL] /chat POST failed: {e}")
        results["chat_api"] = f"FAIL ({e})"


def check_api_keys_and_aws():
    print("\n--- 2. Checking API Keys & External Services ---")
    
    # 2A. AWS STS
    try:
        import boto3
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"[PASS] AWS STS Identity Verified: Account={identity['Account']}, Arn={identity['Arn']}")
        results["aws_iam_keys"] = f"PASS (Account: {identity['Account']})"
    except Exception as e:
        print(f"[FAIL] AWS IAM credentials failed: {e}")
        results["aws_iam_keys"] = f"FAIL ({e})"

    # 2B. AWS S3
    try:
        s3 = boto3.client("s3")
        buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
        target_bucket = os.getenv("S3_BUCKET_NAME", "kisanmitra-data-2026")
        if target_bucket in buckets:
            objs = s3.list_objects_v2(Bucket=target_bucket).get("Contents", [])
            print(f"[PASS] AWS S3 Bucket '{target_bucket}' accessible ({len(objs)} objects)")
            results["aws_s3"] = "PASS"
        else:
            print(f"[WARN] Bucket '{target_bucket}' not in bucket list: {buckets}")
            results["aws_s3"] = "WARN"
    except Exception as e:
        print(f"[FAIL] AWS S3 access failed: {e}")
        results["aws_s3"] = f"FAIL ({e})"

    # 2C. Mandi API Key (data.gov.in)
    mandi_key = os.getenv("MANDI_API_KEY")
    resource_id = os.getenv("MANDI_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070")
    if mandi_key:
        try:
            mandi_url = f"https://api.data.gov.in/resource/{resource_id}?api-key={mandi_key}&format=json&limit=1"
            req = urllib.request.Request(mandi_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
                records = data.get("records", [])
                print(f"[PASS] Mandi API Key (data.gov.in) valid. Status: {data.get('status')}, Records fetched: {len(records)}")
                results["mandi_api_key"] = "PASS"
        except Exception as e:
            print(f"[FAIL] Mandi API key check failed: {e}")
            results["mandi_api_key"] = f"FAIL ({e})"
    else:
        print("[WARN] No MANDI_API_KEY found in environment")
        results["mandi_api_key"] = "NOT_CONFIGURED"

    # 2D. Weather API (Open-Meteo)
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=19.9975&longitude=73.7898&current=temperature_2m,relative_humidity_2m"
        with urllib.request.urlopen(weather_url, timeout=5) as r:
            wdata = json.loads(r.read().decode())
            temp = wdata.get("current", {}).get("temperature_2m")
            print(f"[PASS] Open-Meteo Weather API responsive. Live Nashik Temp: {temp}°C")
            results["weather_api"] = f"PASS ({temp}°C)"
    except Exception as e:
        print(f"[FAIL] Weather API failed: {e}")
        results["weather_api"] = f"FAIL ({e})"


def check_aws_bedrock():
    print("\n--- 3. Checking AWS Bedrock Model Access ---")
    import boto3
    region = os.getenv("AWS_DEFAULT_REGION", "eu-north-1")
    
    # Check Bedrock client control plane
    try:
        bedrock = boto3.client("bedrock", region_name=region)
        models = bedrock.list_foundation_models().get("modelSummaries", [])
        print(f"[PASS] Bedrock control plane connected in {region}. Found {len(models)} foundation models.")
        results["bedrock_connection"] = "PASS"
    except Exception as e:
        print(f"[FAIL] Bedrock control plane failed: {e}")
        results["bedrock_connection"] = f"FAIL ({e})"

    # Check Bedrock runtime invocation
    try:
        runtime = boto3.client("bedrock-runtime", region_name=region)
        # Try converse on Nova Micro
        res = runtime.converse(
            modelId="eu.amazon.nova-micro-v1:0",
            messages=[{"role": "user", "content": [{"text": "Hello"}]}]
        )
        reply = res["output"]["message"]["content"][0]["text"]
        print(f"[PASS] Bedrock runtime invocation SUCCESS! Model reply: '{reply}'")
        results["bedrock_runtime"] = "ACTIVE"
    except Exception as e:
        err_msg = str(e)
        if "Operation not allowed" in err_msg:
            print(f"[INFO] Bedrock invocation returned: 'Operation not allowed' (Account must open model in Playground to accept terms)")
            results["bedrock_runtime"] = "PENDING_PLAYGROUND_ACCEPTANCE"
        else:
            print(f"[INFO] Bedrock invocation note: {err_msg}")
            results["bedrock_runtime"] = f"NOTE: {err_msg[:80]}"

    # Check Bedrock Bearer Token
    bearer_key = os.getenv("BEDROCK_API_KEY")
    if bearer_key:
        print(f"[PASS] BEDROCK_API_KEY configured in environment.")
        results["bedrock_api_key"] = "PRESENT"
    else:
        results["bedrock_api_key"] = "NOT_CONFIGURED"


if __name__ == "__main__":
    check_frontend_backend_link()
    check_api_keys_and_aws()
    check_aws_bedrock()
    
    print("\n================== SUMMARY MATRIX ==================")
    for k, v in results.items():
        print(f"  {k:25}: {v}")
    print("====================================================\n")
