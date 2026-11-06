/*
 * changelog-data.js — the single source of truth for the public /changelog page.
 *
 * HOW TO EDIT
 *   Add a new release object at the TOP of `releases` (newest first) and save.
 *   `npm run dev` hot-reloads; `npm run build` ships it. Changelog.jsx only does layout —
 *   it reads every word from this file.
 *
 * WRITE FOR AUTHORS, NOT FOR US.
 *   This is the user-facing changelog. Describe what an author sees and can do:
 *   new commands, new venues, clearer checks. Do NOT paste from core/CHANGELOG.md —
 *   that file is developer-facing and carries internal rule IDs, pipeline terms, and
 *   test counts that should not appear here. Keep the register plain.
 *
 * SHAPE
 *   release = {
 *     version: "0.4.0"  | "Initial release",   // shown as-is; numbers are prefixed "v" by the page
 *     date:    "June 17, 2026",
 *     title:   "one-line theme of the release", // optional
 *     changes: [{ tag: "New" | "Improved" | "Fixed" | "Removed" | "Thanks", text: "..." }],
 *   }
 *   In `text`, wrap a `command` or `path` in backticks to render it as monospace code.
 */

export const changelog = {
  head: {
    lead: "What's",
    emphasis: "new",
    sub: "Every ReproAI Prep release, newest first; releases before 0.8 shipped under the name ReproAI. The rule set keeps evolving as more replication packages are seen; run `/reproai:update` to check your version and how to update.",
  },

  releases: [
    {
      version: "0.8.3",
      date: "November 6, 2026",
      title: "When you prepare for IQSS Certify, your assistant checks that Certify can start and walks you to its button.",
      changes: [
        {
          tag: "New",
          text: "`reproai certify-start` checks that IQSS Certify can start on your prepared copy: nothing that would make Certify refuse it, no Stata `.do` files (Certify 0.2.0 runs R and Python only), the runtimes your scripts need, a Python 3.12 or newer for Certify's own program, that Certify's service answers, and that its two published checksum lists agree. It writes `CERTIFY_START.md`, the steps from your draft dataset's Certify button. It reads public files only and never installs or runs Certify.",
        },
        {
          tag: "New",
          text: "`/reproai:prepare` ends a preparation for Certify with one question: start now, just the steps, or not now. Start now walks you to the Certify button on your draft dataset. Once you paste Certify's form, ReproAI Prep steps back and your assistant follows Certify's own instructions in the same chat.",
        },
        {
          tag: "Improved",
          text: "Your answers on the intake form carry through to Certify. \"Not sure\" prepares for your journal and offers Certify at the end. \"Do not run my code\" gets a reminder that Certify runs your scripts three times. \"Do not change any of my files\" still offers Certify, and `CERTIFY_START.md` tells you to tick the same box in Certify's form.",
        },
        {
          tag: "Improved",
          text: "The handoff points to the Certify button instead of listing Certify commands for you to type. The prepared copy is named `<name>-prepared`, since Certify names its work folder after the folder you give it.",
        },
        {
          tag: "Fixed",
          text: "The Claude Code commands no longer look for the engine inside the plugin, which does not carry it; they give the install line instead. The instructions for other assistants install the engine from the public repository.",
        },
      ],
    },
    {
      version: "0.8.2",
      date: "November 6, 2026",
      title: "The command that checks a run's output files is renamed for what it does.",
      changes: [
        {
          tag: "Improved",
          text: "`reproai verify` is renamed `reproai outputs`, for what it does: it checks that every expected table and figure file exists, is not empty and, with `--since`, was written by this run. It never compares results with the paper, which the old name suggested. `reproai verify` still works in this release and prints a note pointing to the new name.",
        },
        {
          tag: "Improved",
          text: "`/reproai:debug` calls `reproai outputs` after the rehearsal.",
        },
      ],
    },
    {
      version: "0.8.1",
      date: "November 5, 2026",
      title: "The Certify target reads paths the way Certify does, so it no longer calls a package blocked over paths Certify accepts.",
      changes: [
        {
          tag: "Fixed",
          text: "A path counts as outside the dataset only the way Certify's own reading audit counts it: the path a read, a `source()` or a folder change names, resolved from the folder an earlier `setwd()` moved to, then from the package root, then from the script's folder. A pattern inside `gsub()`, `na.strings = \"..\"`, or a fragment of a path still being assembled no longer counts.",
        },
        {
          tag: "Fixed",
          text: "A general path-style warning no longer blocks a package under the Certify target; the refusal belongs to the outside-the-dataset check above. LaTeX markup written with doubled backslashes in R or Python strings, such as a dagger in a table note, is no longer mistaken for a network-share path.",
        },
        {
          tag: "New",
          text: "A script in a subfolder that reads `../data/x.csv` is flagged under the Certify target: Certify runs every script from the package root, where that path leads nowhere.",
        },
        {
          tag: "Improved",
          text: "A text file in a non-UTF-8 encoding read without naming its encoding is a warning in R (it reads on and garbles the characters) and a run failure in Python (the decode error stops the step).",
        },
        {
          tag: "Fixed",
          text: "The engine starts on Python 3.10 and 3.11 again.",
        },
      ],
    },
    {
      version: "0.8.0",
      date: "November 5, 2026",
      title: "ReproAI is now ReproAI Prep, by Leo Yang Yang and Yiqing Xu, with IQSS Certify as a target and a rehearsal that runs your package the way a certification service will.",
      changes: [
        {
          tag: "New",
          text: "The new name is ReproAI Prep. The Python package is `reproai-prep`; the command stays `reproai` and the slash commands stay `/reproai:*`, so nothing you type changes. Cite it with the software reference at the bottom of the home page.",
        },
        {
          tag: "New",
          text: "`--target certify` checks a package against IQSS Certify's entry requirements before you start Certify: rules read from Certify's published program for paths outside the dataset, network reads, outside services, startup files, run-time installs, interactive calls, seeding Certify cannot re-map, missing output folders, file-tree problems and more. Each finding names its effect at Certify (refuse, run fails, mark, warning, note), and `target_readiness_report.json` sums it up: blocked, needs attention, or no static obstacle. Generic advice that Certify contradicts, such as install lines or files kept outside the package, is reworded for Certify.",
        },
        {
          tag: "New",
          text: "`reproai rehearse`, driven by `/reproai:debug`, runs a copy of your package twice the way a certification service will: from the root, with the network blocked as far as your machine allows, a private empty home folder, a fixed time zone and locale, figures written to files and every step seeded. It then compares the outputs: identical, numerically close, or different, naming the files that moved. R and Python are rehearsed; your original is never run.",
        },
        {
          tag: "New",
          text: "`/reproai:prepare` goes from a messy folder to a prepared copy in one pass: check, the repairs you approve, a rehearsal with your permission, and a handoff. `reproai handoff` writes the run order, the libraries, what is still open and the next steps for your destination; `reproai note` records each approved repair in the copy's `CERTIFICATION-NOTES.txt`.",
        },
        {
          tag: "New",
          text: "Not on Claude Code or Codex? Fill in `PREP_INTAKE.txt` and paste it into any assistant that can run commands; `PREP_PROMPT.md` takes it through the same steps.",
        },
        {
          tag: "Improved",
          text: "Absolute-path detection reads R and Python strings with their escapes, so LaTeX and regular-expression strings are no longer taken for network shares, and a drive path written with forward slashes (`D:/data`) is caught in every language.",
        },
        {
          tag: "Fixed",
          text: "Stata `use cohort` without the `.dta` extension, and `use v1 v2 using x.dta`, resolve to the right file instead of a false missing input. Code written inside a string is no longer read as a call, and a file written through a variable that holds its path is no longer reported missing.",
        },
        {
          tag: "Removed",
          text: "The run-certificate experiment that began in 0.5, and the certificate pages on this site. ReproAI Prep prepares packages; certifying them is the certification service's own step.",
        },
      ],
    },
    {
      version: "0.7.0",
      date: "September 2, 2026",
      title: "Checks for what breaks a closed, two-run certification, and Python coverage for randomness and missing inputs.",
      changes: [
        {
          tag: "New",
          text: "The clock, a date, or a temporary path written into an output file is flagged in Stata, R and Python: it makes two honest runs disagree.",
        },
        {
          tag: "Improved",
          text: "Unseeded randomness is caught in Python too (`random`, NumPy, PyTorch, scikit-learn's `random_state`), and a seed drawn from the clock or the process ID, such as `set.seed(as.numeric(Sys.time()))`, counts as no seed.",
        },
        {
          tag: "New",
          text: "A read whose path is assembled at run time (`paste0`, `file.path`, f-strings, `os.path.join`, or a `gzfile`, `unz` or `url` wrapper) is pointed out: no checker can follow it, so name the file directly where you can.",
        },
        {
          tag: "New",
          text: "A package larger than 1,000 MB is flagged before you deposit it.",
        },
        {
          tag: "Improved",
          text: "Missing inputs are found in Python as well: a literal `pd.read_csv` of a file the package does not ship is a blocker. A package with several unconnected entry scripts and no master script is flagged.",
        },
        {
          tag: "Fixed",
          text: "`do analysis` written without the `.do` suffix is followed as a call, so run-order, entry-point and orphan-file findings are right on packages written that way.",
        },
      ],
    },
    {
      version: "0.6.0",
      date: "September 1, 2026",
      title: "Ship your Stata commands inside the package; don't install them at run time.",
      changes: [
        {
          tag: "Improved",
          text: "An `ssc install` line no longer counts as declaring a user-written Stata command. A certification run has no network, so the command has to ship inside the package.",
        },
        {
          tag: "New",
          text: "Run-time installs inside analysis scripts are flagged as blockers: `ssc install` and `net install` in Stata, `install.packages`, devtools, remotes and pak in R. Wrapping them in `capture` makes it worse: offline, the install fails silently and the script stops later at first use.",
        },
        {
          tag: "New",
          text: "An `adopath` or `sysdir` pointing outside the package (a home folder or an absolute path) is flagged.",
        },
        {
          tag: "New",
          text: "On an approved repair, the user-written Stata commands your package uses can be copied into an `ado/` folder of the prepared copy. The files to copy come from your installation's `stata.trk` manifest, so shared library files are found too; the install lines are rewritten, and the repair stops to ask you rather than leave a partial fix.",
        },
      ],
    },
    {
      version: "0.4.10",
      date: "July 7, 2026",
      title: "Fewer false alarms on R Markdown and Stata-macro packages, and reports that show the whole picture at once.",
      changes: [
        {
          tag: "Fixed",
          text: "R Markdown files are no longer mistaken for broken R scripts. A `.Rmd` whose analysis lives in code chunks — normal R Markdown syntax — used to get a spurious highest-priority finding on every check. A chunk marker pasted into a plain `.R` script (a real error) is still caught.",
        },
        {
          tag: "Fixed",
          text: "Stata reads through a global macro now resolve. If your run-all sets `global dirdta \"data\"` and a script calls `use \"${dirdta}/survey.dta\"`, the checker follows the macro to the shipped file instead of reporting a missing input. Reads parameterized by a loop's local macro match the files you ship, too — while a read of a file that truly ships nowhere is still flagged.",
        },
        {
          tag: "Fixed",
          text: "The advisory scan and the journal-requirement check now share one absolute-path detector. Previously a path inside a comment could fail the journal check while the advisory list showed zero items — clean and failing at the same time. The journal check also now names the offending files.",
        },
        {
          tag: "Improved",
          text: "Documentation findings list every affected file the first time. The old report capped the list at 8, so fixing a large package took several check-and-fix rounds as new names kept surfacing; now the full set appears at once, with an explicit `(+N more)` note past 50.",
        },
        {
          tag: "Thanks",
          text: "All four reports came from real replication packages checked by `@aeshaansinghal` — filed with minimal reproducible patterns via `/reproai:contribute`.",
        },
      ],
    },
    {
      version: "0.4.9",
      date: "July 4, 2026",
      title: "Notebook, SAS, and R coverage, fewer Stata false alarms, and a first finance-journal profile.",
      changes: [
        {
          tag: "New",
          text: "Jupyter notebooks are now held to the same standard as scripts: a labeled exhibit (`#Table 1` in a code comment, `## Figure 2` in markdown) must be exported to a `tables/` or `figures/` folder. An unexported exhibit fails the check with an additive fix (add the `to_latex`/`savefig` line) — and a notebook that already exports correctly now passes verification instead of always failing.",
        },
        {
          tag: "New",
          text: "SAS programs are no longer invisible: hardcoded absolute paths in `.sas` files (like `libname x 'C:\\...'`) are now flagged, comment-aware, and count against a journal's no-absolute-paths requirement. Deeper SAS support (missing inputs, run order) is planned.",
        },
        {
          tag: "New",
          text: "R scripts that call a function which exists nowhere — not in the package, not in any loaded library — are now flagged before they crash with `could not find function`. The check knows the exports of ~90 common packages and stays silent rather than guessing when it sees one it doesn't know.",
        },
        {
          tag: "New",
          text: "A Stata `.do` that is really a pasted console session (lines starting `. `, comments starting `#`) is now flagged instead of passing silently; it would stop on its first line when run.",
        },
        {
          tag: "New",
          text: "Added `jfqa`, a profile for the Journal of Financial and Quantitative Analysis and the first finance venue. Its finance-specific expectations (pseudo vs. real proprietary data, per-source access, run order) are author-confirmed, never silently passed.",
        },
        {
          tag: "Improved",
          text: "A data file read by an absolute path (like `/restricted/panel.dta`) that is not in the package is now reported as a missing input, not just a path-portability warning.",
        },
        {
          tag: "Fixed",
          text: "`drop if ...`, which deletes rows rather than variables, no longer triggers a false \"variable used after it was dropped\" warning.",
        },
        {
          tag: "Fixed",
          text: "A file saved inside a `forvalues` or `foreach` loop is no longer reported as missing when read back; reproai now follows the loop's actual values.",
        },
        {
          tag: "Fixed",
          text: "A comment ending in a colon inside a Jupyter notebook (`.ipynb`) no longer triggers a false \"absolute path\" warning; reproai now reads the notebook's cells, not its raw JSON.",
        },
        {
          tag: "Fixed",
          text: "A macro-built export path like `esttab using \"$ROOT/tables/table1.csv\"` is now credited as a valid table or figure output.",
        },
        {
          tag: "Thanks",
          text: "Thanks to `@aeshaansinghal`, whose detailed reports drove this release.",
        },
      ],
    },
    {
      version: "0.4.8",
      date: "July 2, 2026",
      title: "Handles GUI-only and qualitative deposits, and stops a few false alarms on R packages.",
      changes: [
        {
          tag: "New",
          text: "A package that ships data but no runnable code (for example a SmartPLS, SPSS, or JASP point-and-click analysis) is now flagged clearly, instead of passing with zero issues as if it were fine. reproai tells you to add the script that produces your results, or document the exact steps to reproduce each table and figure.",
        },
        {
          tag: "New",
          text: "If a package has no runnable code and also ships no result tables or figures, reproai points out that a reproduction has nothing to compare against.",
        },
        {
          tag: "New",
          text: "If your package ships data generated by a language model (for example GPT or Claude), reproai now reminds you to record which model and version produced it, along with the temperature and seed (or the raw responses), so the generation step can be reproduced. Ordinary survey fields that happen to be named `prompt` no longer trip this.",
        },
        {
          tag: "Fixed",
          text: "A script that only makes figures — running models just to draw predicted-probability plots — is no longer asked to also save a coefficient table it never produces. As long as the figure is saved, it passes.",
        },
        {
          tag: "Fixed",
          text: "A LaTeX label such as `\\tau_{1|2}` in a regression table's coefficient names is no longer mistaken for an absolute file path, so it no longer fails the no-absolute-paths check at submission.",
        },
        {
          tag: "Fixed",
          text: "Table exports written across several lines (with `file =` on its own line) and `screenreg` outputs are now recognized, so a package that already saves its tables passes without you having to reformat the call.",
        },
        {
          tag: "Improved",
          text: "A run-all script with a non-standard name (for example `meta.R`) is now recognized as your master script, matching what the package map already shows.",
        },
        {
          tag: "Improved",
          text: "Qualitative and document-only deposits (interviews, primary sources, no code) no longer receive code-only checklist items they could never complete; README, data-citation, and license checks still apply.",
        },
        {
          tag: "Thanks",
          text: "Thanks to `@aeshaansinghal`, who reported the issues fixed in this release, and `@molloyzak13`, who independently sent a fix for the `screenreg` export gap. Spotted something reproai gets wrong? `/reproai:contribute` turns it into a ready-to-file issue.",
        },
      ],
    },
    {
      version: "0.4.7",
      date: "June 27, 2026",
      title: "Maps your exhibits to your code, and catches missing inputs and unseeded draws.",
      changes: [
        {
          tag: "New",
          text: "`/reproai:map` lines up your paper's figures and tables (from the LaTeX source) with the code that produces them, and points out an exhibit with no producing output, or an output no exhibit uses. It is advisory and never runs your code.",
        },
        {
          tag: "Improved",
          text: "The package scan now follows file-path helpers like `file.path()` and `here()` and tracks which files each script reads and writes. So it can flag a script that reads an input the package does not ship (and that no step creates), or a filename that matches two different shipped files.",
        },
        {
          tag: "New",
          text: "A check for unseeded randomness: if a script samples, bootstraps, or imputes without setting a seed, it points that out so your numbers come out the same on every run, and tells you the right way to set the seed for how your code is parallelized.",
        },
        {
          tag: "New",
          text: "A codebook check: if a variable used in your estimation is not described in a codebook you ship, it points it out. Plus fewer false alarms on the absolute-path and README path checks.",
        },
      ],
    },
    {
      version: "0.4.6",
      date: "June 19, 2026",
      title: "Clearer update instructions.",
      changes: [
        {
          tag: "Fixed",
          text: "Refreshing reproai in Claude Code takes two commands, because the rules and venue profiles live in a small Python engine separate from the plugin commands: `/plugin update` updates the commands, then `pip install -U` updates the engine. The `/reproai:update` guide and the website now spell out both steps — earlier they implied `/plugin update` alone pulled new rules.",
        },
      ],
    },
    {
      version: "0.4.5",
      date: "June 19, 2026",
      title: "An honest pre-submission checklist, plus three new static checks.",
      changes: [
        {
          tag: "New",
          text: "A clear pre-submission checklist. Venue requirements that reproai cannot confirm by reading your package — signing a form, depositing to a repository, requesting a verification — are now shown as their own \"things to do before you submit\" list, each with what to do, how to do it, how to check you've done it, and the official source. reproai never marks these as passed for you; you complete them.",
        },
        {
          tag: "New",
          text: "A check for a Data Availability Statement: it looks in your README for a statement saying whether the data are public, partly restricted, or not public, and points it out if it's missing.",
        },
        {
          tag: "New",
          text: "A check for data citations: it looks for a persistent identifier (a DOI or handle, or a Dataverse/Zenodo/ICPSR link) so a replicator can fetch the exact data you used.",
        },
        {
          tag: "Improved",
          text: "The reproducible-parallel-results check now reads your R code directly: if a parallel loop draws random numbers without a fixed, reproducible stream, it tells you to switch to doRNG and regenerate the affected tables.",
        },
      ],
    },
    {
      version: "0.4.4",
      date: "June 19, 2026",
      title: "World Bank venue: completing the reproducibility checklist.",
      changes: [
        {
          tag: "Improved",
          text: "World Bank venue: completes the checklist with the rights statement confirming you had legitimate access to the data, the final manuscript, the paper's tables and figures in raw form, and the expectation that code creates every exhibit and in-text number. Gaps suggested by Mateo Servent (World Bank).",
        },
      ],
    },
    {
      version: "0.4.3",
      date: "June 19, 2026",
      title: "A venue for the World Bank Reproducible Research Repository.",
      changes: [
        {
          tag: "New",
          text: "World Bank venue profile (`worldbank`): the internal reproducibility check World Bank staff and consultants go through before journal submission. It looks for a main script that runs everything after you change only the top-level folder, a README that gives the run order and states the software and version used, a map from each output to the script that makes it, the line(s) to edit to run on another machine, code that starts from the original data, a data availability statement, and the verification request itself. Suggested by Mateo Servent (World Bank).",
        },
      ],
    },
    {
      version: "0.4.2",
      date: "June 19, 2026",
      title: "Contribute back: send lessons and new venues as GitHub issues.",
      changes: [
        {
          tag: "New",
          text: "`/reproai:contribute` turns a lesson into a structured GitHub issue: a defect reproai missed, a false flag, or a journal we don't support yet with its replication rules. reproai never posts on your behalf — it hands you a pre-filled issue to review and submit, and never includes your data, results, or file paths.",
        },
        {
          tag: "New",
          text: "Suggesting a venue: you give the journal's official policy URL and its requirements (each with a verbatim quote); reproai drafts and validates a venue profile, and a maintainer verifies every requirement against the policy before it ships.",
        },
      ],
    },
    {
      version: "0.4.1",
      date: "June 18, 2026",
      title: "A venue for JASA, plus reproducible runs and README tools.",
      changes: [
        {
          tag: "New",
          text: "JASA venue profile (Journal of the American Statistical Association): its README template with a results-to-be-replicated map, the data and code availability form, a master script, the computing environment, a license, and where to deposit the package.",
        },
        {
          tag: "New",
          text: "A check for reproducible parallel results: it flags a parallel loop that draws random numbers without a fixed, reproducible stream, so your bootstrap and simulation numbers come out the same on every run.",
        },
        {
          tag: "Improved",
          text: "README tooling: the checks now read PDF READMEs (not just Markdown), flag duplicate or divergent README files, warn when a README points to a file that is not in the package, and a new helper drafts a README from your package's own structure.",
        },
      ],
    },
    {
      version: "0.4.0",
      date: "June 17, 2026",
      title: "Smoke-testing, and a venue for the Econometric Society.",
      changes: [
        {
          tag: "New",
          text: "`/reproai:debug` trial-runs a copy of your package end to end to confirm it executes and that its tables and figures are actually written. If it hits an error, it explains the cause, offers a few options, and asks how you want to proceed, then re-runs. It only ever touches the copy, and it never judges whether your numbers are correct.",
        },
        {
          tag: "New",
          text: "Econometric Society venue profile, covering Econometrica, Quantitative Economics, and Theoretical Economics.",
        },
        {
          tag: "Improved",
          text: "`/reproai:check` now flags when a reported table or figure is never saved to an output folder, when a multi-script package does not document its run order, and when an intermediate dataset is read by one script but not shipped with the package.",
        },
      ],
    },
    {
      version: "0.3.0",
      date: "June 16, 2026",
      title: "Guided fixes, and five more venues.",
      changes: [
        {
          tag: "New",
          text: "`/reproai:fix` rewrites the recommended changes on a copy of your package, re-checks, and hands you the diff. Only clearly safe edits are applied for you; anything that could change a result is left for you to approve. Your original files are never touched.",
        },
        {
          tag: "New",
          text: "Venue profiles for APSR, AJPS, and JOP, plus generic Harvard Dataverse and openICPSR fallbacks for journals without a dedicated profile.",
        },
        {
          tag: "Improved",
          text: "Stronger detection of deprecated Stata and R syntax that breaks on current software versions, so an old command does not stall a reproducibility run.",
        },
      ],
    },
    {
      version: "Initial release",
      date: "June 15, 2026",
      title: "Static pre-diagnose for replication packages.",
      changes: [
        {
          tag: "New",
          text: "`/reproai:check` scans a working directory, applies the author rule set and a venue profile, and writes a priority-graded advisory, from P0 (blocks reproduction) to P4 (venue polish), of what to fix before you submit. It never runs your code.",
        },
        {
          tag: "New",
          text: "`/reproai:comply` checks a package against a target venue's replication-package rules on its own, without the full pre-diagnose.",
        },
        {
          tag: "New",
          text: "AEA venue profile (AER, AEJ, JEL, JEP), plus a normalized Stata and R style guide. Ships as a plugin for Claude Code and OpenAI Codex.",
        },
      ],
    },
  ],
};
