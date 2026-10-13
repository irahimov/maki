"""
title: MAKI Crew
author: makish
version: 0.2
description: planner -> coder -> ruff/pytest pipeline (ai-env agent)
"""
import os
import re
import subprocess

from pydantic import BaseModel, Field

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LOGO = set("█╗╔╝╚║═")


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
            yield "Tapşırıq boşdur."
            return
        if not os.path.isdir(self.valves.PROJECT_DIR):
            yield f"Qovluq tapılmadı: {self.valves.PROJECT_DIR}"
            return

        env = dict(os.environ, PYTHONUNBUFFERED="1")
        env["MAKI_REVIEW"] = "1" if self.valves.REVIEW else "0"
        yield f"📁 `{self.valves.PROJECT_DIR}`\n\n```\n"
        proc = subprocess.Popen(
            [self.valves.AI_ENV, "agent", task],
            cwd=self.valves.PROJECT_DIR,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
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
            yield "✅ Bitdi. Terminalda `cd ~/maki-projects/playground && ai-env accept` (və ya `ai-env reject`)."
        else:
            yield f"❌ Xəta (kod {rc})."
