import json
import math
import re
from pathlib import Path
from docx import Document as DocxDocument
from openai import OpenAI
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import settings


def client(user_config: str | dict | None = None) -> OpenAI | None:
    api_key = user_config.get("api_key") if isinstance(user_config, dict) else user_config
    api_key = api_key or settings.openai_api_key
    if not api_key:
        return None
    base_url = user_config.get("base_url") if isinstance(user_config, dict) else None
    return OpenAI(api_key=api_key, base_url=base_url or None)


def configured_model(user_config: str | dict | None, kind: str) -> str:
    if kind == "text" and isinstance(user_config, dict) and user_config.get("model"):
        return user_config["model"]
    if isinstance(user_config, dict) and user_config.get(f"{kind}_model"):
        return user_config[f"{kind}_model"]
    return getattr(settings, f"openai_{kind}_model")


def transcribe(path: Path, user_api_key: str | None = None) -> str:
    api = client(user_api_key)
    if not api:
        return "[演示模式] 这是上传会议录音的模拟转写文本。团队讨论了产品迭代计划、知识库权限和本周交付目标。"
    with path.open("rb") as audio:
        result = api.audio.transcriptions.create(model=configured_model(user_api_key, "transcribe"), file=audio)
    return result.text


def json_response(instructions: str, content: str, user_api_key: str | None = None) -> dict:
    api = client(user_api_key)
    if not api:
        return {}
    response = api.responses.create(
        model=configured_model(user_api_key, "text"),
        instructions=instructions + " 仅返回有效 JSON，不要使用 Markdown 代码块。",
        input=content,
    )
    return json.loads(response.output_text)


def summarize(transcript: str, user_api_key: str | None = None) -> dict:
    result = json_response(
        "你是企业会议秘书。输出字段 overview(string)、key_points(string[])、decisions(string[])、action_items({task,owner,due_date}[])、risks(string[])。",
        transcript, user_api_key,
    )
    return result or {
        "overview": "团队完成了产品迭代计划、知识库权限和本周交付目标的同步。",
        "key_points": ["确认会议总结流程", "推进知识库权限设计", "本周完成上传体验"],
        "decisions": ["优先交付会议与知识库闭环"],
        "action_items": [{"task": "完善知识库权限方案", "owner": "产品团队", "due_date": "本周五"}],
        "risks": ["企业文档权限边界需要进一步验证"],
        "demo": True,
    }


def generate_report(meeting_context: str, notes: str, user_api_key: str | None = None) -> dict:
    result = json_response(
        "你是工作日报助手。输出字段 accomplishments(string[])、pending_items(string[])、next_plans(string[])、blockers(string[])、summary(string)。",
        f"会议资料：\n{meeting_context}\n\n用户补充：\n{notes}", user_api_key,
    )
    return result or {
        "summary": "今日围绕 AI Work OS 核心流程推进产品设计与交付。",
        "accomplishments": ["完成会议总结功能梳理", "确认知识库权限设计方向"],
        "pending_items": ["补充真实业务文档进行问答验证"],
        "next_plans": ["联调上传与 AI 处理链路"],
        "blockers": [],
        "demo": True,
    }


def extract_text(path: Path, mime_type: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if suffix == ".docx":
        return "\n".join(p.text for p in DocxDocument(path).paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")


def split_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap, separators=["\n\n", "\n", "。", "；", " ", ""])
    return [chunk for chunk in splitter.split_text(text) if chunk.strip()]


def embed(texts: list[str], user_api_key: str | None = None) -> list[list[float]]:
    # Custom single-model endpoints often do not expose an embeddings model.
    # Keep retrieval local and deterministic for broad compatibility.
    api = None if isinstance(user_api_key, dict) else client(user_api_key)
    if api:
        response = api.embeddings.create(model=configured_model(user_api_key, "embedding"), input=texts)
        return [item.embedding for item in response.data]
    # Deterministic local embedding for a fully runnable demo without an API key.
    vectors = []
    for text in texts:
        vector = [0.0] * 128
        for i, char in enumerate(text):
            vector[(ord(char) + i) % 128] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1
        vectors.append([v / norm for v in vector])
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x*x for x in a)) or 1) * (math.sqrt(sum(y*y for y in b)) or 1))


def lexical_score(question: str, content: str) -> float:
    """Simple Chinese-friendly relevance score used only without an API key."""
    def terms(value: str) -> set[str]:
        normalized = re.sub(r"\s+", "", value.lower())
        latin = set(re.findall(r"[a-z0-9]{2,}", normalized))
        han = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
        return latin | {han[i:i + 2] for i in range(max(0, len(han) - 1))}
    query_terms = terms(question)
    if not query_terms:
        return 0.0
    content_terms = terms(content)
    return len(query_terms & content_terms) / len(query_terms)


def answer(question: str, contexts: list[dict], user_api_key: str | None = None) -> str:
    api = client(user_api_key)
    sources = "\n\n".join(f"[{i+1}] {c['content']}" for i, c in enumerate(contexts))
    if not api:
        if not contexts:
            return "知识库中没有找到与这个问题直接相关的内容。请补充更具体的关键词、制度名称或业务场景。"
        excerpt = contexts[0]["content"][:240].strip()
        return f"根据知识库中最相关的资料：\n\n{excerpt}\n\n这是演示模式下的本地检索结果；配置 OpenAI API Key 后可生成更完整的归纳答案。"
    response = api.responses.create(
        model=configured_model(user_api_key, "text"),
        instructions="你是企业知识库助手。只根据提供的资料回答；资料不足时明确说明。引用资料时使用 [1] 格式。",
        input=f"资料：\n{sources}\n\n问题：{question}",
    )
    return response.output_text
