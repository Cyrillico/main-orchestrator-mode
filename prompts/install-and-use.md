# Short prompt for AI — install & use `orch`

Copy-paste this to Claude Code / Codex:

```text
Install and wire the Main Orchestrator Mode skill from this repo:

REPO: <path-or-github-url-to-main-orchestrator-mode>

Follow AGENTS.md strictly.
Detect host (Claude Code and/or Codex).
Install adapter files into the correct skill root:
- Claude: ~/.claude/skills/orch
- Codex: ${CODEX_HOME:-~/.codex}/skills/orch

Requirements:
1) Copy host adapter SKILL.md + shared references/
2) Claude: also copy adapters/claude/workflows/main-orchestrator-mode.js
3) Codex: also copy scripts/partition_write_tasks.py
4) Remove any hardcoded /Users/... personal paths; use skill-local/relative paths only
5) Do not modify the orchestration contract while installing
6) Verify files exist; for Codex run a quick partition script smoke test
7) Report only: installed, host, dest, files, invoke, notes

After install, when I say /orch <goal> or ask for multi-file orchestration:
- parent only schedules/locks/merges
- workers return short digests only
- one writer per file
- poll active workers ~every 3 min; bare wait-timeout is not dead
```

## Even shorter one-liner

```text
按这个仓库的 AGENTS.md 安装 orch 技能到当前 host（Claude/Codex），去掉个人绝对路径，装完只回报 installed/host/dest/invoke。
```
