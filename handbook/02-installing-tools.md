# 02 — Installing the Tools

**For:** electronics engineers · **Software knowledge needed:** a little, explained here.

You install five things once. After that, you mostly just open VS Code and talk to
the AI. Do them in this order.

## 1. VS Code (your workspace)

VS Code is a free editor from Microsoft. Here, it's the "desk" where you keep your
project and where the AI assistant lives.

- Download: <https://code.visualstudio.com> → install like any app.

## 2. An AI assistant

Pick **one** AI assistant that runs inside VS Code. Any of these work with Tracewright —
they all read the same instructions in this repository:

| Assistant | What it is | Get it |
|---|---|---|
| **Claude Code** | Anthropic's assistant (recommended) | install the Claude Code extension / CLI |
| **Codex** | OpenAI's coding assistant | install its VS Code extension |
| **OpenCode** | an open-source assistant | follow its install guide |

You'll need to sign in to the assistant with your account. That's all the "setup"
there is — the assistant reads the `CLAUDE.md`/`AGENTS.md` files in this repo
automatically and knows how to help.

## 3. EasyEDA Pro (schematic + placement)

- Make a free account at <https://easyeda.com> and install **EasyEDA Pro**.
- You'll sign in once; the AI reads your board from the running EasyEDA window.

## 4. KiCad (routing + verification)

- Download the free installer: <https://www.kicad.org/download/>.
- You don't need to learn KiCad's interface deeply — the AI drives it for routing
  and checks. It helps to know where the DRC (design-rule check) report appears.

## 5. Git (saves and publishes your work)

Git is a tool that saves the history of your project and lets you publish it online.
You rarely type Git commands — the AI does it for you — but it must be installed.

- Download: <https://git-scm.com/downloads>.
- One-time identity setup (paste into VS Code's terminal, using your own name/email):
  ```
  git config --global user.name  "Your Name"
  git config --global user.email "you@example.com"
  ```

> **New words?** *Git*, *repository*, *terminal*, *extension* are all in the
> [glossary](glossary.md). You don't need to master them — just have the tools
> installed.

## Final check — run the doctor

Tracewright includes a one-command check that confirms everything above at once. In VS
Code's terminal, from the Tracewright folder:

```
python3 tools/doctor.py
```

It lists each tool with ✅ / ⚠️ / ❌ and tells you exactly how to fix anything
missing. All green (or only ⚠️ notes for tools you don't need yet, like KiCad) means
you're ready to start.

## What good looks like

- `python3 tools/doctor.py` shows no ❌ items.
- VS Code opens.
- Your AI assistant appears inside VS Code and you can type a message to it.
- EasyEDA Pro and KiCad both open.
- Typing `git --version` in VS Code's terminal prints a version number.

## Common mistakes

- Installing two AI assistants and getting confused — **pick one** to start.
- Forgetting to sign in to EasyEDA — the AI can't read a signed-out board.
- Skipping the Git identity setup — the AI can't save your work under your name.

## Checklist

- [ ] VS Code installed.
- [ ] One AI assistant installed and signed in.
- [ ] EasyEDA Pro installed and signed in.
- [ ] KiCad installed.
- [ ] Git installed and identity set.

---
◀ [01 — Introduction](01-introduction.md) · Next ▶ [03 — VS Code & your AI assistant](03-vscode-and-ai.md)
