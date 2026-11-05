/*
 * content.js — the single source of truth for ALL copy on the ReproAI landing page.
 *
 * HOW TO EDIT
 *   Change any string below and save. `npm run dev` hot-reloads instantly; `npm run build`
 *   ships it. App.jsx only handles layout + animation — it reads every word of visible text
 *   from this file, so editing here is all you need. No sync step, nothing can drift.
 *
 * SYNTAX-HIGHLIGHTED BLOCKS are token lists rather than plain sentences:
 *   - usage.cli.runLines                           → the command-line terminal demo
 *   - cite.bibLines                                → the BibTeX block
 *   To edit them, change the text inside each token's  t: "..."  . The wrapper
 *   (P, CMD, SLASH, FLAG, OUT, TXT / AT, KEY, FLD, VAL, PUN) only sets the highlight color.
 *   The "Copy" button copies text derived from bibLines automatically — nothing to keep in sync.
 *
 * INLINE CODE: in plain prose, wrap a word in `backticks` to render it as <code> (monospace).
 *
 * NOT HERE: the browser tab title and the search/social-preview description live in
 *   site/index.html (they must be static HTML so crawlers and link unfurlers can read them).
 *   Those two strings are the only page copy outside this file.
 */

export const GH = "https://github.com/reproai/reproai";

// color helpers for the terminal demos + BibTeX (each sets the token's highlight class only)
const P = (t) => ({ t, c: "prompt" });
const CMD = (t) => ({ t, c: "cmd" });
const SLASH = (t) => ({ t, c: "slash" });
const FLAG = (t) => ({ t, c: "flag" });
const OUT = (t) => ({ t, c: "out" });
const TXT = (t) => ({ t });
const AT = (t) => ({ t, c: "bib-at" });
const KEY = (t) => ({ t, c: "bib-key" });
const FLD = (t) => ({ t, c: "bib-field" });
const VAL = (t) => ({ t, c: "bib-val" });
const PUN = (t) => ({ t, c: "bib-pun" });

export const content = {
  brand: { mark: "R", name: "ReproAI Prep" },

  nav: {
    // each label also doubles as its scroll-anchor (lowercased must match a section id below)
    links: ["Overview", "Install", "Usage", "Examples", "Contribute", "FAQ", "Cite"],
  },

  hero: {
    eyebrow: "Author-facing preparation of replication packages · by Leo Yang Yang and Yiqing Xu",
    headline: { lead: "Build a package", rest: "others can ", emph: "REPRODUCE", tail: "." },
    lede:
      "ReproAI is a plugin for agentic AI. It helps authors prepare cleaner, more readable replication packages before making them public, so journal data editors, replicators, and their AI assistants can reproduce the results with less friction. ReproAI diagnoses common package issues and rewrites a copy for clarity and consistency. An optional rehearsal then runs a copy twice, the way a certification service will, to check that the revised package actually runs and gives the same outputs. Headed for IQSS Certify? ReproAI Prep checks Certify's entry requirements first and hands you the next steps. The scientific judgment behind the findings remains the authors' own.",
    ctaPrimary: "View on GitHub",
    ctaGhost: "How to install",
    meta: "Works with Claude Code, OpenAI Codex CLI, or any AI assistant (PREP_PROMPT.md)",
  },

  engine: {
    title: "ReproAI Prep · the per-package workflow",
    runsTag: "runs code",
    working: "working…",
    inputLabel: "Input",
    inputText: "A messy working directory + the draft paper",
    stages: [
      { name: "/reproai:check", note: "Static pre-diagnose — scans, applies rules + venue, writes the advisory" },
      { name: "/reproai:comply", note: "Venue compliance checklist (AER, APSR, AJPS, JASA…)" },
      { name: "/reproai:fix", note: "Rewrites the recommended fixes to a copy, re-checks" },
      { name: "/reproai:debug", note: "Smoke-tests: does it run? Are tables/figures emitted?", runs: true },
    ],
    outputLabel: "Output · priority-graded advisory (examples)",
    advisory: [
      { cls: "p0", label: "P0", text: "Code falls back to the wrong dataset" },
      { cls: "p1", label: "P1", text: "The software version is never recorded" },
      { cls: "p2", label: "P2", text: "A results table is never saved to a file" },
      { cls: "p3", label: "P3", text: "No comment links each result to its table" },
      { cls: "p4", label: "P4", text: "README doesn't follow the journal's template" },
    ],
    advisoryNote: "Ranked by priority, from P0 blockers to P4 polish.",
    map: {
      cmd: "/reproai:map",
      note: "Alongside the flow: maps the paper's figures and tables onto the code that produces them, flagging exhibits with no output and outputs with no exhibit. Advisory, LaTeX, never part of check.",
    },
    update: {
      cmd: "/reproai:update",
      note: "Outside the per-package flow — the rule set keeps evolving as more packages are seen.",
    },
  },

  install: {
    head: {
      lead: "Install & Update",
      emphasis: "ReproAI",
      sub: "ReproAI is a plugin for Claude Code and OpenAI Codex, backed by a small Python engine (3.10+) that the commands call. Install both once and it's available in every project.",
    },
    aiLabel: "Prompt",
    ai: {
      title: "Install or Update with your AI assistant",
      prompt: "Install or update the ReproAI plugin for me. Fetch https://raw.githubusercontent.com/reproai/reproai/main/INSTALL_FOR_AI.md and follow it for my host (Claude Code or OpenAI Codex): if ReproAI isn't installed yet, install it; if it already is, update it to the latest. Run the commands and verify it works.",
      note: "Paste this into Claude Code or Codex and it installs or updates ReproAI for you. Prefer to run the commands yourself? They're in the project README on GitHub.",
    },
  },

  usage: {
    head: {
      lead: "How to",
      emphasis: "use",
      sub: "Once installed, use ReproAI from the command line or straight from your AI assistant in the desktop app. Either way it diagnoses your package and rewrites a copy; the optional smoke test then runs it.",
    },
    cli: {
      title: "Command Line",
      runLines: [
        [P("❯ "), SLASH("/reproai:check"), TXT(" . "), FLAG("--venue aea")],
        [OUT("  advisory: P0=1 P1=2 P2=1 P3=3 P4=1")],
        [OUT("  venue (aea): 2 pass / 2 fail / 5 action")],
        [P("❯ "), SLASH("/reproai:fix"), TXT(" . "), OUT("# rewrite to a copy")],
        [P("❯ "), SLASH("/reproai:debug"), TXT(" "), OUT("# smoke-test the copy: does it run?")],
        [OUT("  ✓ runs clean · tables + figures emitted")],
      ],
      notes: [
        "Start `claude` in the folder that holds your code and data, so `.` points at the package.",
        "Swap `--venue aea` for your target journal, such as `apsr`, `ajps`, or `jop`.",
        "`fix` always rewrites to a copy; your original files are never touched.",
      ],
    },
    app: {
      title: "App",
      intro: "In the Claude or Codex desktop app, open the folder with your code and data, then tell your AI assistant what you want:",
      speaker: "You",
      prompt: "Use the ReproAI plugin to reorganize my replication package for APSR.",
      note: "It runs the same `check`, `fix`, and `debug` steps and reports back what it changed. Every fix stays your call.",
    },
  },

  examples: {
    head: {
      lead: "Why ReproAI can help you",
      emphasis: "fix",
      sub: "Recurring, author-preventable patterns that make a package harder for a data editor to reproduce. We learned these patterns from a large corpus and graded each issue from P0 to P4 based on how much it raises the cost of a downstream run.",
    },
    items: [
      {
        title: "Wrong dataset loads silently",
        flow: ["Reads the data-load logic", "Finds a guarded fallback that never runs", "Flags P0 — confirm the intended dataset"],
        out: "Catches a defect that would make every number run on the wrong data.",
      },
      {
        title: "Package won't run as shipped",
        flow: ["Scans entry points & dependencies", "Finds a referenced file that isn't there", "Flags the missing data / broken include"],
        out: "Surfaces the blockers that stall a reproducibility run up front.",
      },
      {
        title: "Version-fragile code",
        flow: ["Detects deprecated syntax & removed packages", "Notes a missing version declaration", "Proposes the standard, durable form"],
        out: "Prevents cross-version drift before it costs a fix-loop round.",
      },
      {
        title: "Venue compliance",
        flow: ["Loads the target-venue profile", "Checks README, structure, forms", "Lists what passes vs needs author action"],
        out: "Tells you exactly what to do before depositing to AEA, APSR, AJPS, JOP…",
      },
    ],
  },

  contribute: {
    head: {
      lead: "You can",
      emphasis: "contribute",
      sub: "ReproAI improves by crowdsourcing: send back a defect it missed, a false flag, or a venue it lacks, and it becomes a rule or venue everyone gets. It drafts a pre-filled GitHub issue you submit yourself, with your ==privacy== protected: your data and paths never leave your machine.",
    },
    cli: {
      title: "Command Line",
      runLines: [
        [P("❯ "), SLASH("/reproai:contribute"), TXT("   "), OUT("# pick what you found")],
        [OUT("  · a missed rule · a false flag · a new venue")],
        [],
        [OUT("  › a new venue: Quarterly Journal of Economics")],
        [OUT("  › paste its data & code policy URL")],
        [OUT("  ✓ drafted the qje profile: 6 checks, runs clean")],
        [OUT("  → a pre-filled GitHub issue opens; you click Submit")],
      ],
      notes: [
        "`/reproai:contribute` walks you through it and drafts the profile.",
        "It validates the draft locally before the pre-filled issue opens.",
      ],
    },
    app: {
      title: "App",
      intro: "Or just ask your AI assistant in the Claude or Codex desktop app:",
      speaker: "You",
      prompt: "We just got my replication package running. Summarize the lessons from this session (anything ReproAI missed, or I had to fix by hand) and help me contribute them back.",
      note: "It works straight from the session you just ran and drafts the summary. All you do is revise it, approve it, and submit it as a GitHub issue.",
    },
  },

  faq: {
    head: { lead: "Frequently asked", emphasis: "questions" },
    qa: [
      {
        q: "Does ReproAI run my code?",
        a: "Only when you ask it to. The three core commands — `check`, `comply`, and `fix` — are static: they inspect your files, structure, and dependencies but never execute your analysis. The `debug` command runs your code, but only as a smoke test (see below).",
      },
      {
        q: "What does the debug command do?",
        a: "It trial-runs a copy of your package as a smoke test: does the package execute end to end, and are the table and figure outputs actually written? If a runtime error occurs, it explains the root cause to you, offers a few options, and asks you to choose. It only runs the copy, never your original.",
      },
      {
        q: "Which venues does it support?",
        a: "It ships profiles for AEA (AER, AEJ, JEL, JEP), the Econometric Society (Econometrica, QE, TE), JASA (Journal of the American Statistical Association), APSR, AJPS, and JOP, plus generic Dataverse and openICPSR fallbacks. Profiles are data files, so the list grows over time.",
      },
      {
        q: "What does P0–P4 mean?",
        a: "Findings are graded by downstream reproducibility cost. P0 blocks reproduction. P1 imposes a large cost, often requiring many fix-loop rounds. P2 creates a moderate risk of misreading. P3 covers minor organization issues. P4 covers venue-specific polish. You can choose to fix only P0 issues, P0 and P1 issues, or all findings.",
      },
      {
        q: "Will fixing everything guarantee a first-try pass?",
        a: "No, and ReproAI says so. The plugin increases the chance of a first-try pass by removing known, avoidable failures before a data editor runs the package. Numerical match, full environment reconstruction, and runtime behavior only surface at execution, so a guarantee would not be honest.",
      },
      {
        q: "Does it auto-fix my files?",
        a: "Only for the small set of fixes that are clearly semantics-preserving, and only on a copy. ReproAI never changes your original files, and dry-run is the default. Anything that could change a result is propose-only and left for you to apply.",
      },
      {
        q: "Which tools does it work with?",
        a: "It runs as a plugin in Claude Code and OpenAI Codex CLI, and the engine is a plain command-line tool, so any host that can call a shell can use it.",
      },
    ],
  },

  cite: {
    head: { lead: "Cite", emphasis: "ReproAI", sub: "If ReproAI helps your research, consider citing our work." },
    referenceLabel: "Reference",
    bibtexLabel: "BibTeX",
    copyIdle: "Copy",
    copyDone: "Copied",
    title: "Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Replication and Reanalysis",
    meta: "Yiqing Xu & Leo Yang Yang · arXiv:2602.16733 · 2026",
    linkText: "arxiv.org/abs/2602.16733 →",
    linkUrl: "https://arxiv.org/abs/2602.16733",
    bibLines: [
      [AT("@article"), PUN("{"), KEY("xu2026scaling"), PUN(",")],
      [TXT("  "), FLD("title"), TXT("   "), PUN("= {"), VAL("Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Replication and Reanalysis"), PUN("},")],
      [TXT("  "), FLD("author"), TXT("  "), PUN("= {"), VAL("Xu, Yiqing and Yang, Leo Yang"), PUN("},")],
      [TXT("  "), FLD("year"), TXT("    "), PUN("= {"), VAL("2026"), PUN("},")],
      [TXT("  "), FLD("journal"), TXT(" "), PUN("= {"), VAL("arXiv preprint arXiv:2602.16733"), PUN("},")],
      [TXT("  "), FLD("url"), TXT("     "), PUN("= {"), VAL("https://arxiv.org/abs/2602.16733"), PUN("}")],
      [PUN("}")],
    ],
  },

  footer: {
    links: [
      { label: "Changelog", href: "/changelog/" },
      { label: "Report a bug or ask for a feature", href: `${GH}/issues`, newTab: true },
    ],
    note: "The plugin authors run before submission.",
  },
};
