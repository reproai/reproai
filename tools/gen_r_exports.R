#!/usr/bin/env Rscript
# Generates core/src/reproai_prep/rules/r_exports_db.json — the bundled R export snapshot behind
# A17-undefined-r-callable (issue #36).
#
# The detector fires ONLY when every library()/require() target in a script is a package in this
# snapshot; one unknown package silences the whole file. So coverage = how many real replication
# scripts the rule can assess at all, and the candidate list is curated toward econ/polisci
# replication packages, not raw CRAN downloads.
#
# Regenerate on each release (release-checklist step): Rscript tools/gen_r_exports.R
# Uninstalled candidates are WARNED and skipped — install them first for full coverage:
#   install.packages(<missing>, repos = "https://cloud.r-project.org")
#
# Staleness is a real, bounded false-flag channel: a package export added after this snapshot
# (e.g. dplyr::reframe in 1.1.0) would flag on valid code. Bounded by P2 + propose_only + the
# snapshot date being named in the finding text.

base_pkgs <- c("base", "stats", "utils", "graphics", "grDevices", "methods", "datasets",
               "tools", "parallel", "splines", "stats4", "grid", "compiler", "tcltk")

cran_pkgs <- c(
  # data wrangling / io
  "dplyr", "tidyr", "readr", "haven", "foreign", "data.table", "stringr", "purrr", "tibble",
  "lubridate", "janitor", "readxl", "writexl", "openxlsx", "glue", "magrittr", "forcats",
  "here",
  # estimation / econometrics
  "lfe", "fixest", "plm", "sandwich", "lmtest", "estimatr", "AER", "ivreg", "rdrobust",
  "did", "didimputation", "bacondecomp", "PanelMatch", "HonestDiD", "eventstudyr", "binsreg",
  "MASS", "Matrix", "zoo", "xts", "nlme", "lme4", "survival", "quantreg", "car",
  "multiwayvcov", "clubSandwich", "boot", "mice", "fect", "gsynth", "panelView", "interflex",
  "Synth", "statar", "misty",
  # output / tables / figures
  "stargazer", "texreg", "xtable", "broom", "modelsummary", "gt", "huxtable", "kableExtra",
  "ggplot2", "scales", "gridExtra", "patchwork", "ggrepel", "sf",
  # infrastructure
  "foreach", "doParallel", "doRNG", "future", "furrr", "Rcpp", "devtools", "remotes"
)

installed <- rownames(installed.packages())
grab <- function(pkgs) {
  out <- list()
  for (p in pkgs) {
    if (!(p %in% installed)) {
      warning(sprintf("candidate '%s' not installed — SKIPPED (install it and regenerate)", p),
              call. = FALSE, immediate. = TRUE)
      next
    }
    out[[p]] <- sort(getNamespaceExports(p))
  }
  out
}

db <- list(
  generated = format(Sys.Date()),
  r_version = paste(R.version$major, R.version$minor, sep = "."),
  base = grab(base_pkgs),
  cran = grab(cran_pkgs)
)

out_path <- file.path("core", "src", "reproai_prep", "rules", "r_exports_db.json")
if (!file.exists(dirname(out_path))) stop("run from the repo root: Rscript tools/gen_r_exports.R")
writeLines(jsonlite::toJSON(db, auto_unbox = TRUE, pretty = FALSE), out_path)

n_base <- length(unique(unlist(db$base)))
n_cran <- length(unique(unlist(db$cran)))
cat(sprintf("wrote %s: %d base pkgs (%d names), %d cran pkgs (%d names), %.0f KB\n",
            out_path, length(db$base), n_base, length(db$cran), n_cran,
            file.size(out_path) / 1024))
