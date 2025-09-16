from __future__ import annotations

from typing import Dict, List, Any, Tuple

from .agents import ChatHelper, load_commissioning, TOCAgent, ChapterAgent, FactCheckAgent, EditorAgent


class Orchestrator:
    def __init__(self, commissioning_path: str, api_key: str | None = None) -> None:
        cfg = load_commissioning(commissioning_path)
        model = cfg.get("meta", {}).get("model", "mistral-small")
        if api_key is None:
            import os
            api_key = os.environ.get("MISTRAL_API_KEY", "")
        self.cfg = cfg
        self.chat = ChatHelper(api_key=api_key or "", model=model)
        self.toc_agent = TOCAgent(self.chat, cfg)
        self.chapter_agent = ChapterAgent(self.chat, cfg)
        self.fact_agent = FactCheckAgent(self.chat, cfg)
        self.editor = EditorAgent(self.chat, cfg)

    def build(self) -> Tuple[List[str], Dict[str, str]]:
        chapters_list = self.toc_agent.propose_toc()
        chapters: Dict[str, str] = {}

        for title in chapters_list:
            draft = self.chapter_agent.write_chapter(title, chapters_list)
            review = self.fact_agent.review(title, draft)
            if str(review.get("verdict", "fail")).lower() != "pass":
                guidance = review.get("guidance", "Please correct factual inaccuracies.")
                draft = self.fact_agent.request_rewrite(title, draft, guidance)
                review2 = self.fact_agent.review(title, draft)
                if str(review2.get("verdict", "fail")).lower() != "pass":
                    pass
            chapters[title] = draft

        chapters = self.editor.enforce_length(chapters)
        return chapters_list, chapters
