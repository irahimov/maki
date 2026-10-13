"""
title: MAKI Crew
author: makish
version: 0.3
description: planner -> coder -> ruff/pytest pipeline (ai-env agent)
"""
import os
import re
import subprocess

from pydantic import BaseModel, Field

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LOGO = set("\u2588\u2557\u2554\u255d\u255a\u2551\u2550")


class Pipe:
    class Valves(BaseModel):
        PROJECT_DIR: str = Field(default="/home/makish/maki-projects/playground")
        AI_ENV: str = Field(default="/home/makish/.local/bin/ai-env")
        REVIEW: bool = Field(default=False)

    def __init__(self):
        self.name = "MAKI Crew"
        self.valves = self.Valves()

    @staticmethod
    def _last_user_text(body: dict) -> str:
        for m in reversed(body.get("messages", [])):
            if m.get("role") != "user":
                continue
            c = m.get("content", "")
            if isinstance(c, list):
                c = " ".join(p.get("text", "") for p in c if p.get("type") == "text")
            return str(c).strip()
        return ""

    def pipe(self, body: dict, __task__=None):
        if __task__:
            return
        task = self._last_user_text(body)
        if not task:
            yield "Tap\u015f\u0131r\u0131q bo\u015fdur."
            return
        if not os.path.isdir(self.valves.PROJECT_DIR):
            yield f"Qovluq tap\u0131lmad\u0131: {self.valves.PROJECT_DIR}"
            return

        env = dict(os.environ, PYTHONUNBUFFERED="1")
        env["MAKI_REVIEW"] = "1" if self.valves.REVIEW else "0"
        yield f"\U0001F4C1 `{self.valves.PROJECT_DIR}`\n\n```\n"
        proc = subprocess.Popen(
            [self.valves.AI_ENV, "agent", task],
            cwd=self.valves.PROJECT_DIR,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        for line in proc.stdout:
            line = ANSI.sub("", line)
            if any(ch in LOGO for ch in line) or not line.strip():
                continue
            yield line
        rc = proc.wait()
        yield "```\n\n"
        if rc == 0:
            yield (
                "\u2705 Bitdi. Terminalda `cd ~/maki-projects/playground "
                "&& ai-env accept` (v\u0259 ya `ai-env reject`)."
            )
        else:
            yield f"\u274c X\u0259ta (kod {rc})."
