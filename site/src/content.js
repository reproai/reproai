/*
 * content.js — the single source of truth for ALL copy on the ReproAI Prep landing page.
 *
 * HOW TO EDIT
 *   Change any string below and save. `npm run dev` hot-reloads instantly; `npm run build`
 *   ships it. App.jsx only handles layout + animation — it reads every word of visible text
 *   from this file, so editing here is all you need. No sync step, nothing can drift.
 *
 * SYNTAX-HIGHLIGHTED BLOCKS are token lists rather than plain sentences:
 *   - usage.cli.runLines, contribute.cli.runLines  → the terminal demos
 *   - cite.entries[*].bibLines                      → the BibTeX blocks
 *   To edit them, change the text inside each token's  t: "..."  . The wrapper
 *   (P, CMD, SLASH, FLAG, OUT, TXT / AT, KEY, FLD, VAL, PUN) only sets the highlight color.
 *   Each "Copy" button copies text derived from its bibLines automatically — nothing to keep in sync.
 *   The usage demo's output lines are what the engine prints (shortened), so re-check them
 *   against `reproai check` / `reproai rehearse` when the output format changes.
 *
 * INLINE CODE: in plain prose, wrap a word in `backticks` to render it as <code> (monospace).
 *
 * NOT HERE: the browser tab title and the search/social-preview description live in
 *   site/index.html and site/changelog/index.html (they must be static HTML so crawlers and
 *   link unfurlers can read them). Keep them in step with the hero below.
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
    eyebrow: "Replication-package preparation · Leo Yang Yang & Yiqing Xu",
    headline: { lead: "Build a package", rest: "others can ", emph: "REPRODUCE", tail: "." },
    lede:
      "ReproAI Prep gets your replication package ready before a data editor or a certification service such as IQSS Certify runs it: it finds what would break a clean run, repairs a copy with your approval, and, when you ask, rehearses the copy the way the service will. It never judges your results.",
    ctaPrimary: "View on GitHub",
    ctaGhost: "How to install",
    meta: "Works with Claude Code, OpenAI Codex, or any AI assistant that can run commands",
  },

  engine: {
    title: "ReproAI Prep · one package, start to finish",
    runsTag: "runs code",
    working: "working…",
    inputLabel: "Input",
    inputText: "Your replication package (Stata, R, Python) + the draft paper",
    stages: [
      { name: "/reproai:check", note: "Static audit: rule set, journal profile, and Certify's entry requirements if you target it" },
      { name: "/reproai:fix", note: "Repairs you approve, made on a copy, then re-checked" },
      { name: "/reproai:debug", note: "Rehearsal: runs the copy twice under certification settings and compares the outputs", runs: true },
      { name: "reproai handoff", note: "Run order, libraries, what is still open, next steps for the destination" },
    ],
    outputLabel: "Output · findings graded by priority (examples)",
    advisory: [
      { cls: "p0", label: "P0", text: "A script reads a file from outside the package" },
      { cls: "p1", label: "P1", text: "The software version is never recorded" },
      { cls: "p2", label: "P2", text: "A results table is never saved to a file" },
      { cls: "p3", label: "P3", text: "No comment links each result to its table" },
      { cls: "p4", label: "P4", text: "README doesn't follow the journal's template" },
    ],
    advisoryNote: "Ranked from P0 blockers to P4 polish. With the Certify target, a readiness report too: blocked, needs attention, or no static obstacle.",
    // rows shown under the flow, each a command with a one-line note
    extras: [
      {
        cmd: "/reproai:prepare",
        note: "The whole flow in one pass: check, approved repairs, rehearsal and handoff. It asks before it runs your code or changes anything.",
      },
      {
        cmd: "/reproai:map",
        note: "Alongside the flow: maps the paper's figures and tables onto the code that produces them, flagging exhibits with no output and outputs with no exhibit. Advisory, LaTeX only.",
      },
    ],
  },

  install: {
    head: {
      lead: "Install & Update",
      emphasis: "ReproAI Prep",
      sub: "ReproAI Prep is a plugin for Claude Code and OpenAI Codex, backed by a small Python engine (3.10+) that the commands call. Install both once and it's available in every project. Using another assistant? Paste `PREP_INTAKE.txt` from the repository into it; it walks the assistant through the same steps.",
    },
    aiLabel: "Prompt",
    ai: {
      title: "Install or Update with your AI assistant",
      prompt: "Install or update the ReproAI Prep plugin for me. Fetch https://raw.githubusercontent.com/reproai/reproai/main/INSTALL_FOR_AI.md and follow it for my host (Claude Code or OpenAI Codex): if it isn't installed yet, install it; if it already is, update it to the latest. Run the commands and verify it works.",
      note: "Paste this into Claude Code or Codex and it installs or updates ReproAI Prep for you. Prefer to run the commands yourself? They're in the project README on GitHub.",
    },
  },

  usage: {
    head: {
      lead: "How to",
      emphasis: "use",
      sub: "Once installed, use ReproAI Prep from Claude Code in your terminal or from your AI assistant in the desktop app. Either way it audits your package and repairs a copy; the rehearsal runs your code only when you ask.",
    },
    cli: {
      title: "Command Line",
      runLines: [
        [P("❯ "), SLASH("/reproai:check"), TXT(" . "), FLAG("--venue aea --target certify")],
        [OUT("  advisory: 3 items (P0=2 P1=0 P2=0 P3=1 P4=0)")],
        [OUT("  venue (aea): 2 pass / 2 fail / 5 need author action")],
        [OUT("  target (IQSS Certify): blocked (2 run_fails)")],
        [P("❯ "), SLASH("/reproai:fix"), TXT(" . "), OUT("# approved repairs, on a copy")],
        [P("❯ "), SLASH("/reproai:debug"), TXT(" "), OUT("# rehearse: two runs, compared")],
        [OUT("  run 1: exit 0 · run 2: exit 0")],
        [OUT("  grade: identical (two runs wrote the same outputs)")],
      ],
      notes: [
        "Start `claude` in the folder that holds your code and data, so `.` points at the package.",
        "Swap `--venue aea` for your journal (`apsr`, `ajps`, `jop`, `econsoc`, …). Leave out `--target certify` if the package is not headed for IQSS Certify.",
        "`fix` always works on a copy; your original files are never touched. Or run everything at once with `/reproai:prepare`.",
      ],
    },
    app: {
      title: "App",
      intro: "In the Claude or Codex desktop app, open the folder with your code and data, then tell your AI assistant what you want:",
      speaker: "You",
      prompt: "Use ReproAI Prep to get my replication package ready for APSR and for IQSS Certify.",
      note: "It runs the same check, repair, rehearsal and handoff steps, asks before it runs your code or changes a file, and reports back what it changed. Every repair stays your call.",
    },
  },

  examples: {
    head: {
      lead: "Why ReproAI Prep can help you",
      emphasis: "fix",
      sub: "Recurring, author-preventable patterns that make a package harder for a data editor or a certification service to reproduce. We distilled them from a large body of real replication work and graded each from P0 to P4 by how much it raises the cost of a downstream run.",
    },
    items: [
      {
        title: "Wrong dataset loads silently",
        flow: ["Reads the data-load logic", "Finds a guarded fallback that never runs", "Flags P0: confirm the intended dataset"],
        out: "Catches a defect that would make every number run on the wrong data.",
      },
      {
        title: "Package won't run as shipped",
        flow: ["Scans entry points & dependencies", "Finds a referenced file that isn't there, or one read from outside the package", "Flags the missing data / broken include"],
        out: "Surfaces the blockers that stall a reproducibility run up front.",
      },
      {
        title: "Version-fragile code",
        flow: ["Detects deprecated syntax & removed packages", "Notes a missing version declaration or a run-time install", "Proposes the standard, durable form"],
        out: "Prevents cross-version drift before it costs a fix-loop round.",
      },
      {
        title: "Outputs change between runs",
        flow: ["Runs a copy twice, network blocked, fixed time zone and locale", "Compares every table and figure the runs wrote", "Identical, numerically close, or different, and which files moved"],
        out: "Catches unseeded randomness and time stamps written into outputs before a certification run does.",
      },
      {
        title: "Certify would refuse it",
        flow: ["Reads the package against IQSS Certify's entry requirements", "Finds a path outside the dataset, a run-time install, an empty folder", "Names each finding's effect: refuse, run fails, mark, warning, note"],
        out: "Clears what would stop Certify's closing before you start it.",
      },
      {
        title: "Venue compliance",
        flow: ["Loads the target-venue profile", "Checks README, structure, forms", "Lists what passes vs needs author action"],
        out: "Tells you what to do before depositing to AEA, APSR, AJPS, JOP…",
      },
    ],
  },

  contribute: {
    head: {
      lead: "You can",
      emphasis: "contribute",
      sub: "ReproAI Prep improves with use: tell us about a defect it missed, a false flag, or a venue it lacks, and we may turn it into a rule or venue profile everyone gets. It drafts a pre-filled GitHub issue you submit yourself, with your ==privacy== protected: your data and paths never leave your machine.",
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
      prompt: "We just got my replication package running. Summarize the lessons from this session (anything ReproAI Prep missed, or I had to fix by hand) and help me report them.",
      note: "It works straight from the session you just ran and drafts the summary. All you do is revise it, approve it, and submit it as a GitHub issue.",
    },
  },

  faq: {
    head: { lead: "Frequently asked", emphasis: "questions" },
    qa: [
      {
        q: "Does ReproAI Prep run my code?",
        a: "Only when you ask it to. `check`, `comply`, `fix` and `map` are static: they read your files, structure and dependencies but never execute your analysis. The rehearsal (`/reproai:debug`, or `reproai rehearse` on the command line) runs a copy of your package, never your original, and only with your permission.",
      },
      {
        q: "What does the rehearsal do?",
        a: "It runs a copy of your package twice the way a certification service will: from the package root, with the network blocked as far as your machine allows, a private empty home folder, a fixed time zone and locale, figures written to files, and each step's random generator seeded. Then it compares what the two runs wrote: identical, numerically close, or different. R and Python scripts are rehearsed; Stata scripts are run once in batch mode. If a step fails, it explains the likely cause, offers options, and asks you to choose; it never fixes a runtime error on its own.",
      },
      {
        q: "How does it relate to IQSS Certify?",
        a: "Certify (certify.iq.harvard.edu) certifies a replication dataset at publication. ReproAI Prep is independent of Certify and shares no code with it. With `--target certify` it checks, before you start Certify, the entry requirements we read from Certify's published program (24 rules), and writes a readiness report naming the effect of each finding at Certify: refuse, run fails, mark, warning or note. Prep never runs Certify's own steps; it tells you when you will need them. Certify's closing is the only authority on whether a package closes.",
      },
      {
        q: "Which venues does it support?",
        a: "It ships profiles for AEA (AER, AEJ, JEL, JEP), the Econometric Society (Econometrica, QE, TE), JASA (Journal of the American Statistical Association), JFQA (Journal of Financial and Quantitative Analysis), the World Bank Reproducible Research Repository, APSR, AJPS, and JOP, plus generic Dataverse and openICPSR fallbacks. Profiles are data files, so the list grows over time. IQSS Certify is a separate target (`--target certify`), not a venue.",
      },
      {
        q: "What does P0–P4 mean?",
        a: "Findings are graded by downstream reproducibility cost. P0 blocks reproduction. P1 imposes a large cost, often requiring many fix-loop rounds. P2 creates a moderate risk of misreading. P3 covers minor organization issues. P4 covers venue-specific polish. You can choose to fix only P0 issues, P0 and P1 issues, or all findings.",
      },
      {
        q: "Will fixing everything guarantee a first-try pass?",
        a: "No, and ReproAI Prep says so. It raises the chance of a first-try pass by removing known, avoidable failures before a data editor or a certification service runs the package. Agreement with the numbers in your paper, full environment reconstruction, and some runtime behavior only surface when the package is actually run, so a guarantee would not be honest. Prep never compares results with the paper and never issues a reproducibility verdict or a certificate.",
      },
      {
        q: "Does it change my files?",
        a: "Never your originals. Repairs are made on a copy, and only the ones you approve. A small set that clearly preserves what the code computes can be applied automatically; anything that could change a result is proposed for you to decide. With `/reproai:prepare`, each approved repair is recorded in the copy's `CERTIFICATION-NOTES.txt`, so a data editor or certifier can see what changed and who approved it.",
      },
      {
        q: "Which tools does it work with?",
        a: "It runs as a plugin in Claude Code and OpenAI Codex. For any other assistant that can run commands, paste `PREP_INTAKE.txt` from the repository; it points the assistant to `PREP_PROMPT.md`, which takes it through the same steps. The engine is a plain command-line tool (`reproai`), so you can also run it yourself.",
      },
    ],
  },

  cite: {
    head: {
      lead: "Cite",
      emphasis: "ReproAI Prep",
      sub: "If ReproAI Prep helps your research, please cite the software. The paper describes the large-scale replication workflow its rules were learned from.",
    },
    bibtexLabel: "BibTeX",
    copyIdle: "Copy",
    copyDone: "Copied",
    entries: [
      {
        referenceLabel: "Software",
        title: "ReproAI Prep: Preparing Replication Packages for Reproducibility Checks and Certification",
        meta: "Leo Yang Yang & Yiqing Xu · Software · 2026",
        linkText: "github.com/reproai/reproai →",
        linkUrl: GH,
        bibLines: [
          [AT("@software"), PUN("{"), KEY("yang2026reproaiprep"), PUN(",")],
          [TXT("  "), FLD("title"), TXT("  "), PUN("= {"), VAL("ReproAI Prep: Preparing Replication Packages for Reproducibility Checks and Certification"), PUN("},")],
          [TXT("  "), FLD("author"), TXT(" "), PUN("= {"), VAL("Yang, Leo Yang and Xu, Yiqing"), PUN("},")],
          [TXT("  "), FLD("year"), TXT("   "), PUN("= {"), VAL("2026"), PUN("},")],
          [TXT("  "), FLD("url"), TXT("    "), PUN("= {"), VAL("https://github.com/reproai/reproai"), PUN("}")],
          [PUN("}")],
        ],
      },
      {
        referenceLabel: "Paper",
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
    ],
  },

  footer: {
    links: [
      { label: "Changelog", href: "/changelog/" },
      { label: "Report a bug or ask for a feature", href: `${GH}/issues`, newTab: true },
    ],
    note: "By Leo Yang Yang and Yiqing Xu. Run it before you deposit.",
  },
};
