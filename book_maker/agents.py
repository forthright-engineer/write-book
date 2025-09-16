from __future__ import annotations

from typing import List, Dict, Any

import yaml
from mistralai import Mistral, SystemMessage, UserMessage


class ChatHelper:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Mistral(api_key=api_key)
        self.model = model

    def complete(self, messages: List[Any]) -> str:
        resp = self.client.chat.complete(model=self.model, messages=messages)
        return resp.choices[0].message.content


def load_commissioning(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TOCAgent:
    def __init__(self, chat: ChatHelper, cfg: Dict[str, Any]):
        self.chat = chat
        self.cfg = cfg

    def propose_toc(self) -> List[str]:
        meta = self.cfg.get("meta", {})
        commission = self.cfg.get("commission", {})
        structure = self.cfg.get("structure", {})
        target_chapters = structure.get("target_chapters", 10)
        must_cover = structure.get("must_cover", [])

        system = SystemMessage(content=(
            "You are a senior book architect. Design a clear, logical Table of Contents "
            "for a non-fiction book."
        ))
        user = UserMessage(content=(
            f"Title: {meta.get('title','Untitled')}\n"
            f"Subject: {commission.get('subject','')}\n"
            f"Goals for reader: {commission.get('goals_for_reader','')}\n"
            f"Target audience: {commission.get('target_audience','')}\n"
            f"Tone and style: {commission.get('tone_and_style','')}\n"
            f"Must cover topics: {', '.join(must_cover) if must_cover else 'None'}\n"
            f"Target chapter count: {target_chapters}\n\n"
            "Return only a numbered JSON array of chapter titles, no descriptions."
        ))
        text = self.chat.complete([system, user])

        try:
            data = yaml.safe_load(text)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return data
        except Exception:
            pass

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        chapters: List[str] = []
        for ln in lines:
            clean = ln
            while clean and (clean[0].isdigit() or clean[0] in "-*)•"):
                clean = clean[1:].lstrip(" .)•-")
            if clean:
                chapters.append(clean)
        return chapters


class ChapterAgent:
    def __init__(self, chat: ChatHelper, cfg: Dict[str, Any]):
        self.chat = chat
        self.cfg = cfg

    def write_chapter(self, chapter_title: str, toc: List[str], context_notes: str = "") -> str:
        commission = self.cfg.get("commission", {})
        constraints = self.cfg.get("constraints", {})
        words_per_page = constraints.get("words_per_page", 100)
        total_pages = constraints.get("total_pages", 160)
        max_words = self.cfg.get("meta", {}).get("max_words", words_per_page * total_pages)

        system = SystemMessage(content=(
            "You are an expert non-fiction author. Write a clear, accurate, engaging chapter. "
            "Use a didactic, practical style with examples. Format as MultiMarkdown."
        ))
        user = UserMessage(content=(
            f"Chapter title: {chapter_title}\n"
            f"Book subject: {commission.get('subject','')}\n"
            f"Goals for reader: {commission.get('goals_for_reader','')}\n"
            f"Target audience: {commission.get('target_audience','')}\n"
            f"Tone and style: {commission.get('tone_and_style','')}\n"
            f"Table of Contents: {toc}\n"
            f"Global max words: {max_words}. Aim for balance across chapters.\n"
            f"Additional context: {context_notes}\n\n"
            "Return only the chapter content in MultiMarkdown."
        ))
        return self.chat.complete([system, user])


class FactCheckAgent:
    def __init__(self, chat: ChatHelper, cfg: Dict[str, Any]):
        self.chat = chat
        self.cfg = cfg

    def review(self, chapter_title: str, content: str) -> Dict[str, Any]:
        system = SystemMessage(content=(
            "You are a rigorous fact-checker. Identify factual claims. Verify them using your knowledge. "
            "Return a JSON object with keys: 'verdict' (pass|fail), 'issues' (list), 'guidance' (string)."
        ))
        user = UserMessage(content=(
            f"Chapter: {chapter_title}\n\n"
            "CONTENT START\n" + content + "\nCONTENT END\n"
        ))
        text = self.chat.complete([system, user])
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"verdict": "fail", "issues": ["Unparseable fact-check output"], "guidance": text}

    def request_rewrite(self, chapter_title: str, content: str, guidance: str) -> str:
        system = SystemMessage(content=(
            "You are an author revising a chapter to correct factual issues. Keep structure and tone."
        ))
        user = UserMessage(content=(
            f"Chapter: {chapter_title}\n\n"
            "Please revise to address these fact-check notes:\n" + guidance + "\n\n"
            "CONTENT START\n" + content + "\nCONTENT END\n\n"
            "Return only the corrected chapter in MultiMarkdown."
        ))
        return self.chat.complete([system, user])


class EditorAgent:
    def __init__(self, chat: ChatHelper, cfg: Dict[str, Any]):
        self.chat = chat
        self.cfg = cfg

    @staticmethod
    def word_count(text: str) -> int:
        return len([w for w in text.split() if w.strip()])

    def enforce_length(self, chapters: Dict[str, str]) -> Dict[str, str]:
        max_words = self.cfg.get("meta", {}).get("max_words", 16000)
        total = sum(self.word_count(c) for c in chapters.values())
        if total <= max_words:
            return chapters

        factor = max_words / max(total, 1)
        new_chapters: Dict[str, str] = {}
        for title, content in chapters.items():
            current = self.word_count(content)
            target = int(current * factor)
            guidance = (
                "Tighten prose, remove redundancy, keep core facts and examples. "
                f"Target words: {target}. Preserve headings."
            )
            system = SystemMessage(content=(
                "You are a precise copy editor. Shorten text to meet target without losing clarity."
            ))
            user = UserMessage(content=(
                f"Chapter: {title}\n{guidance}\n\nCONTENT START\n{content}\nCONTENT END\n"
                "Return only the shortened chapter in MultiMarkdown."
            ))
            shortened = self.chat.complete([system, user])
            new_chapters[title] = shortened
        return new_chapters
