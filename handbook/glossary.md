# Glossary — Software Terms in Plain English

You rarely need these to use Tracewright, but here they are whenever a word is unfamiliar.
Explained for electronics engineers.

| Term | In plain terms |
|---|---|
| **VS Code** | A free editor from Microsoft — the "desk" where you keep the project and where the AI assistant lives. |
| **AI assistant / AI agent** | A program (Claude Code, Codex, OpenCode…) that reads this repo's instructions and helps you design the board by driving the tools. Think "fast junior engineer." |
| **Repository (repo)** | A folder of files that also keeps its full history. This whole Tracewright folder is a repository. |
| **Git** | The tool that saves a project's history and lets you publish it online. The AI runs it for you. |
| **GitHub** | A website that hosts repositories online, so you can back them up and share them. |
| **Commit** | Saving a snapshot of your work into the project history, with a note about what changed. |
| **Push** | Uploading your saved snapshots to GitHub. |
| **Clone** | Making a local copy of a repository from GitHub onto your computer. |
| **Terminal** | A text box where you type commands. In Tracewright the AI uses it; you rarely do. |
| **Markdown (.md)** | Plain-text documents with simple formatting — every guide in this repo is Markdown. The AI reads these to learn the process. |
| **API** | The "control panel" a program exposes so other programs can operate it. The AI uses EasyEDA's and KiCad's APIs so it can draw and route for you. You never see this. |
| **Node.js / JavaScript / TypeScript** | Programming languages/tools the automation is built with. You don't write any of it. |
| **Script** | A small automated set of steps (e.g. "place these parts"). The AI writes and runs these; it hands you the ones you paste into EasyEDA. |
| **Automation** | Any task done by a program instead of by hand — here, drawing, placing, routing, checking. |
| **Browser automation** | The AI reading your live EasyEDA board through the browser to check it. Happens behind the scenes. |
| **CDP** | The specific channel the AI uses to read EasyEDA in the browser. Implementation detail; ignore it. |
| **CLI** | "Command-line interface" — running a tool by typing instead of clicking. Some AI assistants run this way. |
| **Extension** | An add-on for VS Code — for example, the AI assistant is installed as an extension. |
| **Prompt** | A message you send the AI. In Tracewright, just plain English describing what you want. |
| **DRC** | Design-Rule Check — the automatic check that copper spacing, widths, and holes meet the fab's rules. (Electronics term, listed here because it comes up constantly.) |
| **ERC** | Electrical-Rule Check — the schematic-level check for wiring errors. |
| **Gerber** | The standard file format factories use to make PCB layers. |
| **BOM** | Bill of Materials — the parts list. |
| **CPL / Pick-and-place** | The file telling an assembly machine where each part goes. |
| **DFM** | Design-for-Manufacturing — checking a design can actually be built. |
| **Stack-up** | The arrangement of copper and insulating layers in the board (2-layer, 4-layer…). |
| **Verdict** | The AI's checkpoint result: PASS, CONDITIONAL (with a fix list), or FAIL. |
| **Phase / Step** | One of the 12 stages of the Tracewright workflow. |
| **Manifest (`project.yaml`)** | The "cover sheet" of a project — records the current step and every decision. |

Missing a word? Ask the AI: *"explain [word] in plain terms."*

---
◀ [Handbook home](README.md)
