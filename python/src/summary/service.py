import datetime
import os

import requests
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

server = Flask(__name__)
server.config["MONGO_URI"] = os.getenv(
    "MONGO_URI", "mongodb://host.minikube.internal:27017/videos"
)

mongo = PyMongo(server)

AI_SUMMARY_URL = os.getenv("AI_SUMMARY_URL", "").strip()
AI_SUMMARY_API_KEY = os.getenv("AI_SUMMARY_API_KEY", "").strip()
AI_SUMMARY_TIMEOUT = float(os.getenv("AI_SUMMARY_TIMEOUT", "20"))
AI_SUMMARY_MAX_CHARS = int(os.getenv("AI_SUMMARY_MAX_CHARS", "12000"))


def _truncate_context(context: str) -> tuple[str, bool]:
    if len(context) <= AI_SUMMARY_MAX_CHARS:
        return context, False
    return context[:AI_SUMMARY_MAX_CHARS], True


def request_ai_summary(context: str, filename: str | None) -> tuple[str, str]:
    if not AI_SUMMARY_URL:
        raise RuntimeError("AI_SUMMARY_URL is not configured")

    prompt = (
        "You are a concise technical writer. Create a 5-6 sentence summary "
        "based on the provided file context. Infer a single category label "
        "(1-3 words) that best fits the content. Return JSON with keys "
        "'summary' and 'category'."
    )

    payload = {
        "prompt": prompt,
        "context": context,
        "filename": filename,
        "format": {"summary_sentences": "5-6", "category": "single_label"},
    }

    headers = {"Content-Type": "application/json"}
    if AI_SUMMARY_API_KEY:
        headers["Authorization"] = f"Bearer {AI_SUMMARY_API_KEY}"

    resp = requests.post(
        AI_SUMMARY_URL,
        json=payload,
        headers=headers,
        timeout=AI_SUMMARY_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    summary = (
        data.get("summary")
        or data.get("data", {}).get("summary")
        or data.get("result", {}).get("summary")
    )
    category = (
        data.get("category")
        or data.get("data", {}).get("category")
        or data.get("result", {}).get("category")
    )

    if not summary or not category:
        raise ValueError("AI response missing summary/category")

    return summary.strip(), category.strip()


@server.route("/summaries", methods=["POST"])
def create_summary():
    body = request.get_json(silent=True) or {}
    context = body.get("context")
    filename = body.get("filename")
    file_id = body.get("file_id")

    if not context:
        return jsonify({"error": "context is required"}), 400

    context, truncated = _truncate_context(context)
    summary, category = request_ai_summary(context, filename)

    doc = {
        "file_id": file_id,
        "filename": filename,
        "summary": summary,
        "category": category,
        "context_truncated": truncated,
        "created_at": datetime.datetime.utcnow(),
    }

    res = mongo.db.summaries.insert_one(doc)

    return (
        jsonify(
            {
                "id": str(res.inserted_id),
                "summary": summary,
                "category": category,
            }
        ),
        201,
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5002, debug=True)
