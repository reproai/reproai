## How Government Reactions to Violence Worsen Social Welfare: Evidence from Peru
## Sexton, Wellhausen and Findley
## Non-parametric combination for Appendix
## R Sexton, March 2018

## Set working directory
# setwd("~/Downloads")
# install.packages("NPC")

library(foreign)
.regout_safe_library("NPC")
library(plm)
library(magrittr)

## R only likes older Stata files
# === REGOUT PROLOG (auto-injected by Janitor — replication-first mode) ===
# Uses trace() to intercept estimation functions in their package namespaces.
# trace() survives rm(list=ls()) and library() masking because it modifies
# the function in-place within the package namespace.
if (!exists(".regout_env", envir=globalenv())) {
  .regout_env <- new.env(parent=emptyenv())
  .regout_env$.counter <- 0L
  .regout_env$.log_file <- file.path(getwd(), "regout_capture.log")
  assign(".regout_env", .regout_env, envir=globalenv())
}
.regout_env <- get(".regout_env", envir=globalenv())
if (!file.exists(.regout_env$.log_file)) file.create(.regout_env$.log_file)
if (!exists("recode", mode="function")) {
  tryCatch({ recode <- function(x, recodes, ...) car::recode(x, recodes, ...) },
           error=function(e) NULL)
}
.regout_optional_packages <- c("renv", "hrbrthemes", "xtablem", "LARF", "pryr", "Zelig", "xlsx", "geojsonio", "qdap", "dgo", "kableExtra", "flextable", "gt", "huxtable", "formattable")
.regout_safe_library <- function(pkg) {
  if (requireNamespace(pkg, quietly=TRUE)) {
    suppressPackageStartupMessages(library(pkg, character.only=TRUE))
  } else {
    message("REGOUT_OPTIONAL_PACKAGE_SKIP: ", pkg)
  }
}
.regout_safe_p_load <- function(...) {
  pkgs <- unlist(list(...))
  for (pkg in pkgs) {
    if (pkg %in% .regout_optional_packages) {
      .regout_safe_library(pkg)
    } else {
      suppressPackageStartupMessages(library(pkg, character.only=TRUE))
    }
  }
}

# Build the exit handler expression once; trace() injects it into the function.
# returnValue() gives the fitted model object inside the exit handler.
.regout_exit_expr <- function(CMD_NAME) {
  bquote({
    tryCatch({
      .renv <- get(".regout_env", envir=globalenv())
      .fit <- returnValue()
      .renv$.counter <- .renv$.counter + 1L
      .cmd_id <- paste0("cmd_", .renv$.counter)
      .lf <- .renv$.log_file
      .wf <- function(...) cat(..., file=.lf, append=TRUE)
      # Script name detection
      .sn <- tryCatch({
        .sf <- sys.frames(); .found <- "unknown"
        for (.i in rev(seq_along(.sf))) {
          .of <- get0("ofile", envir=.sf[[.i]])
          if (!is.null(.of)) { .found <- basename(.of); break }
        }; .found
      }, error=function(e) "unknown")
      .ln <- tryCatch({
        .sc <- sys.call(sys.parent()); .sr <- attr(.sc, "srcref")
        if (!is.null(.sr)) .sr[1] else NA_integer_
      }, error=function(e) NA_integer_)
      .wf(sprintf("REGOUT_START %s TYPE=%s SCRIPT=%s LINE=%s\n", .cmd_id, .(CMD_NAME), .sn, ifelse(is.na(.ln), "", as.character(.ln))))
      .wf("REGOUT_CMD ", .(CMD_NAME), "\n")
      tryCatch({
        .cf <- if (inherits(.fit, "polr")) {
          tryCatch({
            .beta <- coef(.fit); .zeta <- .fit$zeta
            .all_coef <- c(.beta, .zeta)
            .se <- tryCatch({
              .vc <- solve(.fit$Hessian); sqrt(diag(.vc))
            }, error=function(e) rep(NA_real_, length(.all_coef)))
            .tval <- .all_coef / .se
            cbind(Value = .all_coef, `Std. Error` = .se, `t value` = .tval)
          }, error=function(e) {
            tryCatch(cbind(Value = coef(.fit), `Std. Error` = NA_real_),
                     error=function(e2) NULL)
          })
        } else if (inherits(.fit, "rms")) {
          tryCatch({
            .b <- coef(.fit)
            .se <- tryCatch(sqrt(diag(vcov(.fit))), error=function(e) rep(NA_real_, length(.b)))
            cbind(Estimate=.b, `Std. Error`=.se[seq_along(.b)])
          }, error=function(e) {
            tryCatch(cbind(Estimate = coef(.fit), `Std. Error` = NA_real_),
                     error=function(e2) NULL)
          })
        } else if (inherits(.fit, "felm")) {
          tryCatch({
            .b <- coef(.fit)
            .se <- tryCatch(sqrt(diag(vcov(.fit))), error=function(e) rep(NA_real_, length(.b)))
            cbind(Estimate=.b, `Std. Error`=.se[seq_along(.b)])
          }, error=function(e) {
            tryCatch(cbind(Estimate = coef(.fit), `Std. Error` = NA_real_),
                     error=function(e2) NULL)
          })
        } else if (inherits(.fit, "rdrobust")) {
          # rdrobust returns a $coef and $se matrix with 3 rows
          # (Conventional / Bias-Corrected / Robust). Treat each row as a
          # distinct "variable" so the matcher can look up by row name and
          # bind the paper's reported estimator (often "Robust").
          tryCatch({
            .b <- as.numeric(.fit$coef[, 1])
            .s <- as.numeric(.fit$se[, 1])
            .nm <- rownames(.fit$coef)
            if (is.null(.nm) || length(.nm) != length(.b))
              .nm <- c("Conventional", "Bias-Corrected", "Robust")[seq_along(.b)]
            .out <- cbind(Estimate = .b, `Std. Error` = .s)
            rownames(.out) <- .nm
            .out
          }, error=function(e) {
            tryCatch(cbind(Estimate = .fit$coef, `Std. Error` = .fit$se),
                     error=function(e2) NULL)
          })
        } else if (inherits(.fit, "Match")) {
          # Matching::Match() returns a single ATT (or vector when multiple
          # outcomes were requested via cluster columns). The estimate
          # lives in $est, SE in $se; there is no formula() interface.
          # Treat the ATT as a single "treat" coefficient so block_matcher
          # can fingerprint it like any other regression cell. AI-bias-
          # adjusted variants (Match(..., BiasAdjust=TRUE)) and standard
          # GenMatch reuses both flow through this branch.
          tryCatch({
            .b <- as.numeric(.fit$est)
            .s <- as.numeric(.fit$se)
            if (length(.s) == 0 || is.na(.s[1])) {
              .s <- tryCatch(as.numeric(.fit$se.standard), error=function(e) rep(NA_real_, length(.b)))
            }
            .nm <- if (length(.b) > 1) paste0("treat_", seq_along(.b)) else "treat"
            .out <- cbind(Estimate = .b, `Std. Error` = .s[seq_along(.b)])
            rownames(.out) <- .nm
            .out
          }, error=function(e) NULL)
        } else {
          tryCatch(coef(summary(.fit)), error=function(e) {
            tryCatch({
              .fe <- lme4::fixef(.fit); .se <- sqrt(diag(as.matrix(vcov(.fit))))
              cbind(Estimate=.fe, `Std. Error`=.se[seq_along(.fe)])
            }, error=function(e2) coef(summary(.fit)))
          })
        }
        .wf("REGOUT_COEFS\n")
        capture.output(print(.cf), file=.lf, append=TRUE)
        # Match() has no nobs() method; fall back to length of matched Y.
        .n <- if (inherits(.fit, "Match")) {
          tryCatch(length(.fit$mdata$Y), error=function(e) {
            tryCatch(nrow(.fit$index.treated) + nrow(.fit$index.control),
                     error=function(e2) NA)
          })
        } else {
          tryCatch(nobs(.fit), error=function(e) NA)
        }
        .wf("REGOUT_N ", .n, "\n")
        .r2 <- tryCatch(if (inherits(.fit, "polr") || inherits(.fit, "Match")) NA else summary(.fit)$r.squared, error=function(e) NA)
        .wf("REGOUT_R2 ", .r2, "\n")
        # Match()'s "DV" is the Y argument from the original call. There
        # is no formula() — extract via call object instead.
        .dv <- if (inherits(.fit, "Match")) {
          tryCatch({
            .y_arg <- .fit$call$Y
            if (is.null(.y_arg)) "unknown" else deparse(.y_arg, width.cutoff=500)
          }, error=function(e) "unknown")
        } else {
          tryCatch(deparse(formula(.fit)[[2]], width.cutoff=500), error=function(e) "unknown")
        }
        .wf("REGOUT_DEPVAR ", .dv, "\n")
        .fml <- if (inherits(.fit, "Match")) {
          tryCatch(paste("Match: Y =", deparse(.fit$call$Y, width.cutoff=500),
                         "Tr =", deparse(.fit$call$Tr, width.cutoff=500)),
                   error=function(e) "")
        } else {
          tryCatch(deparse(formula(.fit), width.cutoff=500), error=function(e) "")
        }
        .fml <- paste(.fml, collapse=" ")
        .wf("REGOUT_FORMULA ", .fml, "\n")
        # IV fields extraction
        tryCatch({
          .instd <- ""; .insts <- ""
          if (.(CMD_NAME) == "felm" && inherits(.fit, "felm")) {
            .ff <- paste(deparse(formula(.fit), width.cutoff=500), collapse=" ")
            .pp <- strsplit(.ff, "\\|")[[1]]
            if (length(.pp) >= 3) {
              .iv <- trimws(.pp[3])
              if (.iv != "0" && .iv != "" && grepl("~", .iv)) {
                .ic <- gsub("[\\(\\)]", "", .iv)
                .is <- strsplit(.ic, "~")[[1]]
                if (length(.is)==2) { .instd <- trimws(.is[1]); .insts <- trimws(.is[2]) }
              }
            }
          } else if (.(CMD_NAME) == "ivreg" && inherits(.fit, "ivreg")) {
            .it <- tryCatch({
              .mt <- terms(.fit, "regressors"); .mi <- terms(.fit, "instruments")
              .rv <- attr(.mt, "term.labels"); .iv <- attr(.mi, "term.labels")
              list(endog=setdiff(.rv,.iv), excl=setdiff(.iv,.rv))
            }, error=function(e) NULL)
            if (!is.null(.it)) { .instd <- paste(.it$endog,collapse=" + "); .insts <- paste(.it$excl,collapse=" + ") }
          } else if (.(CMD_NAME) == "iv_robust" && inherits(.fit, "iv_robust")) {
            .ff <- paste(deparse(.fit$call$formula, width.cutoff=500), collapse=" ")
            .pp <- strsplit(.ff, "\\|")[[1]]
            if (length(.pp) >= 2) {
              .lr <- strsplit(trimws(.pp[1]), "~")[[1]]
              if (length(.lr)==2) {
                .regs <- trimws(strsplit(trimws(.lr[2]),"\\+")[[1]])
                .inst <- trimws(strsplit(trimws(.pp[2]),"\\+")[[1]])
                .instd <- paste(setdiff(.regs,.inst),collapse=" + ")
                .insts <- paste(setdiff(.inst,.regs),collapse=" + ")
              }
            }
          }
          if (nchar(.instd) > 0) .wf("REGOUT_INSTD ", .instd, "\n")
          if (nchar(.insts) > 0) .wf("REGOUT_INSTS ", .insts, "\n")
        }, error=function(e) NULL)
      }, error = function(e) .wf("REGOUT_PARTIAL ", conditionMessage(e), "\n"))
      .wf(sprintf("REGOUT_END %s\n", .cmd_id))
      tryCatch({
        .mf <- if (inherits(.fit, "Match")) {
          # Match()'s "analysis data" is the matched-data subset. mdata$Y/X/Tr
          # carry the matched observations used to compute the ATT.
          tryCatch(data.frame(Y = .fit$mdata$Y, Tr = .fit$mdata$Tr),
                   error=function(e) NULL)
        } else {
          model.frame(.fit)
        }
        if (!is.null(.mf))
          write.csv(.mf, paste0("analysis_data_", .cmd_id, ".csv"), row.names=FALSE)
      }, error=function(e) NULL)
    }, error=function(e) NULL)
  })
}

.regout_wrapped <- 0L
for (.fn_spec in list(
  list(pkg="stats",     fn="lm"),
  list(pkg="stats",     fn="glm"),
  list(pkg="lme4",      fn="lmer"),
  list(pkg="lme4",      fn="glmer"),
  list(pkg="blme",      fn="blmer"),
  list(pkg="blme",      fn="bglmer"),
  list(pkg="AER",       fn="ivreg"),
  list(pkg="ivreg",     fn="ivreg"),
  list(pkg="fixest",    fn="feols"),
  list(pkg="fixest",    fn="feglm"),
  list(pkg="fixest",    fn="fenegbin"),
  list(pkg="fixest",    fn="fepois"),
  list(pkg="lfe",       fn="felm"),
  list(pkg="estimatr",  fn="iv_robust"),
  list(pkg="estimatr",  fn="lm_robust"),
  list(pkg="estimatr",  fn="lm_lin"),
  list(pkg="plm",       fn="plm"),
  list(pkg="nnet",      fn="multinom"),
  list(pkg="arm",       fn="bayesglm"),
  list(pkg="MASS",      fn="polr"),
  list(pkg="survival",  fn="coxph"),
  list(pkg="survival",  fn="survreg"),
  list(pkg="dynlm",     fn="dynlm"),
  list(pkg="econet",    fn="net_dep"),
  list(pkg="list",      fn="ictreg"),
  list(pkg="rms",       fn="lrm"),
  list(pkg="rms",       fn="ols"),
  list(pkg="rms",       fn="orm"),
  list(pkg="rms",       fn="cph"),
  list(pkg="rms",       fn="Glm"),
  list(pkg="rms",       fn="psm"),
  list(pkg="rms",       fn="bj"),
  list(pkg="betareg",   fn="betareg"),
  list(pkg="pscl",      fn="zeroinfl"),
  list(pkg="pscl",      fn="hurdle"),
  list(pkg="VGAM",      fn="vglm"),
  list(pkg="survey",    fn="svyglm"),
  list(pkg="survey",    fn="svyolr"),
  list(pkg="survey",    fn="svycoxph"),
  list(pkg="rdrobust",  fn="rdrobust"),
  list(pkg="Matching",  fn="Match")
)) {
  tryCatch({
    if (requireNamespace(.fn_spec$pkg, quietly=TRUE)) {
      .exit_expr <- .regout_exit_expr(.fn_spec$fn)
      .where_env <- if (.fn_spec$pkg %in% c("stats","base"))
                      .GlobalEnv else asNamespace(.fn_spec$pkg)
      suppressMessages(trace(.fn_spec$fn, exit=.exit_expr, print=FALSE,
                              where=.where_env))
      .regout_wrapped <- .regout_wrapped + 1L
    }
  }, error=function(e) NULL)
}
# Global-env wrappers: trace() exit handlers do not fire for bare (unqualified)
# function calls like felm(), ivreg(), feols(). Only pkg::fn() triggers the
# trace. To capture bare calls, create global wrappers that shadow the package
# functions. The wrapper calls the original, then runs the same capture logic.
.regout_gw <- 0L
for (.fn_spec in list(
  list(pkg="lme4",      fn="lmer"),
  list(pkg="lme4",      fn="glmer"),
  list(pkg="blme",      fn="blmer"),
  list(pkg="blme",      fn="bglmer"),
  list(pkg="AER",       fn="ivreg"),
  list(pkg="fixest",    fn="feols"),
  list(pkg="fixest",    fn="feglm"),
  list(pkg="fixest",    fn="fenegbin"),
  list(pkg="fixest",    fn="fepois"),
  list(pkg="fixest",    fn="feNmlm"),
  list(pkg="lfe",       fn="felm"),
  list(pkg="estimatr",  fn="iv_robust"),
  list(pkg="estimatr",  fn="lm_robust"),
  list(pkg="estimatr",  fn="lm_lin"),
  list(pkg="plm",       fn="plm"),
  list(pkg="nnet",      fn="multinom"),
  list(pkg="survival",  fn="coxph"),
  list(pkg="survival",  fn="survreg"),
  list(pkg="dynlm",     fn="dynlm"),
  list(pkg="MASS",      fn="polr"),
  list(pkg="MASS",      fn="glm.nb"),
  list(pkg="list",      fn="ictreg"),
  list(pkg="rms",       fn="lrm"),
  list(pkg="rms",       fn="ols"),
  list(pkg="rms",       fn="orm"),
  list(pkg="rms",       fn="cph"),
  list(pkg="rms",       fn="Glm"),
  list(pkg="rms",       fn="psm"),
  list(pkg="rms",       fn="bj"),
  list(pkg="betareg",   fn="betareg"),
  list(pkg="pscl",      fn="zeroinfl"),
  list(pkg="pscl",      fn="hurdle"),
  list(pkg="VGAM",      fn="vglm"),
  list(pkg="survey",    fn="svyglm"),
  list(pkg="survey",    fn="svyolr"),
  list(pkg="survey",    fn="svycoxph"),
  list(pkg="rdrobust",  fn="rdrobust"),
  list(pkg="Matching",  fn="Match")
)) {
  tryCatch({
    if (requireNamespace(.fn_spec$pkg, quietly=TRUE)) {
      .orig_fn <- get(.fn_spec$fn, envir=asNamespace(.fn_spec$pkg))
      .fn_name <- .fn_spec$fn
      # MINIMAL FORWARDER (graduated 2026-04-30 from JOP2017_691058 fix):
      # Bare coxph()/lmer()/etc. calls don't trigger trace() set on the
      # package namespace because R's search-path lookup returns a copy
      # without the trace bytecode. So we install a global-env shadow
      # that simply forwards to .orig_fn — calling .orig_fn IS the
      # namespace's traced function, which fires trace correctly. The
      # forwarder does NOT write its own capture (the trace exit handler
      # handles that). Original verbose wrapper had a `.cnt_before`
      # guard but it failed in subtle cases (JOP2017_691058 captured
      # cmd_1 twice → R trace() emitted "argument passing errors" and
      # disabled itself, leaving 1/77 regressions captured). Using the
      # minimal forwarder eliminates the duplicate-write surface.
      .wrapper <- eval(bquote(function(...) (.(.orig_fn))(...)))
      assign(.fn_name, .wrapper, envir=globalenv())
      .regout_gw <- .regout_gw + 1L
    }
  }, error=function(e) NULL)
}
if (FALSE) {
  # === ORIGINAL VERBOSE WRAPPER (kept for reference, never executed) ===
  # Reason for retirement: see MINIMAL FORWARDER comment above.
  tryCatch({
    if (requireNamespace(.fn_spec$pkg, quietly=TRUE)) {
      .orig_fn <- get(.fn_spec$fn, envir=asNamespace(.fn_spec$pkg))
      .fn_name <- .fn_spec$fn
      .wrapper <- eval(bquote(function(...) {
        .renv_pre <- get(".regout_env", envir=globalenv())
        .cnt_before <- .renv_pre$.counter
        .result <- (.(.orig_fn))(...)
        tryCatch({
          .renv <- get(".regout_env", envir=globalenv())
          if (.renv$.counter > .cnt_before) { return(.result) }
          .renv$.counter <- .renv$.counter + 1L
          .cmd_id <- paste0("cmd_", .renv$.counter)
          .lf <- .renv$.log_file
          .wf <- function(...) cat(..., file=.lf, append=TRUE)
          .sn <- tryCatch({
            .sf <- sys.frames(); .found <- "unknown"
            for (.i in rev(seq_along(.sf))) {
              .of <- get0("ofile", envir=.sf[[.i]])
              if (!is.null(.of)) { .found <- basename(.of); break }
            }
            .found
          }, error=function(e) "unknown")
          .ln <- tryCatch({
            .sc <- sys.call(sys.parent()); .sr <- attr(.sc, "srcref")
            if (!is.null(.sr)) .sr[1] else NA_integer_
          }, error=function(e) NA_integer_)
          .wf(sprintf("REGOUT_START %s TYPE=%s SCRIPT=%s LINE=%s\n", .cmd_id, .(.fn_name), .sn, ifelse(is.na(.ln), "", as.character(.ln))))
          .wf(sprintf("REGOUT_CMD  %s \n", .(.fn_name)))
          .wf("REGOUT_COEFS\n")
          .cf <- if (inherits(.result, "multinom")) {
            tryCatch(summary(.result)$coefficients, error=function(e) coef(.result))
          } else if (inherits(.result, "polr")) {
            tryCatch({
              .sm <- summary(.result)
              if (!is.null(.sm$coefficients)) {
                cbind(Value = .sm$coefficients,
                      `Std. Error` = .sm$standard.errors[seq_along(.sm$coefficients)])
              } else {
                cbind(Value = coef(.result), `Std. Error` = NA_real_)
              }
            }, error=function(e) {
              tryCatch(cbind(Value = coef(.result), `Std. Error` = NA_real_),
                       error=function(e2) NULL)
            })
          } else if (inherits(.result, "rms")) {
            tryCatch({
              .b <- coef(.result)
              .se <- tryCatch(sqrt(diag(vcov(.result))), error=function(e) rep(NA_real_, length(.b)))
              cbind(Estimate=.b, `Std. Error`=.se[seq_along(.b)])
            }, error=function(e) {
              tryCatch(cbind(Estimate = coef(.result), `Std. Error` = NA_real_),
                       error=function(e2) NULL)
            })
          } else if (inherits(.result, "felm")) {
            tryCatch({
              .b <- coef(.result)
              .se <- tryCatch(sqrt(diag(vcov(.result))), error=function(e) rep(NA_real_, length(.b)))
              cbind(Estimate=.b, `Std. Error`=.se[seq_along(.b)])
            }, error=function(e) {
              tryCatch(cbind(Estimate = coef(.result), `Std. Error` = NA_real_),
                       error=function(e2) NULL)
            })
          } else {
            tryCatch(coef(summary(.result)), error=function(e) {
              tryCatch({
                .fe <- lme4::fixef(.result); .se <- sqrt(diag(as.matrix(vcov(.result))))
                cbind(Estimate=.fe, `Std. Error`=.se[seq_along(.fe)])
              }, error=function(e2) coef(summary(.result)))
            })
          }
          if (!is.null(.cf)) {
            if (is.matrix(.cf)) {
              .hdr <- paste(colnames(.cf), collapse="\t")
              .wf(paste0("\t", .hdr, "\n"))
              for (.rn in rownames(.cf)) {
                .wf(paste0(.rn, "\t", paste(.cf[.rn, ], collapse="\t"), "\n"))
              }
            }
          }
          .n_val <- tryCatch(nobs(.result), error=function(e) tryCatch(length(residuals(.result)), error=function(e2) NA))
          .wf(sprintf("REGOUT_N  %s \n", .n_val))
          .r2 <- tryCatch(summary(.result)$r.squared, error=function(e) NA)
          .wf(sprintf("REGOUT_R2  %s \n", .r2))
          .dv <- tryCatch({
            .frm <- formula(.result)
            deparse(.frm[[2]], width.cutoff=500)
          }, error=function(e) NA)
          .wf(sprintf("REGOUT_DEPVAR  %s \n", .dv))
          .wf(sprintf("REGOUT_FORMULA  %s \n", tryCatch(deparse(formula(.result), width.cutoff=500), error=function(e) NA)))
          .wf(sprintf("REGOUT_END %s\n", .cmd_id))
        }, error=function(e) NULL)
        .result
      }))
      assign(.fn_name, .wrapper, envir=globalenv())
      .regout_gw <- .regout_gw + 1L
    }
  }, error=function(e) NULL)
}
cat(sprintf("REGOUT_PROLOG: traced %d estimator functions, %d global wrappers\n", .regout_wrapped, .regout_gw))
tryCatch({
  if (requireNamespace("stargazer", quietly=TRUE)) {
    .sg_orig <- get("stargazer", envir=asNamespace("stargazer"))
    stargazer <- function(...) {
      tryCatch(.sg_orig(...), error=function(e) {
        message("stargazer skipped: ", conditionMessage(e))
        invisible(NULL)
      })
    }
    assign("stargazer", stargazer, envir=globalenv())
  }
}, error=function(e) NULL)
# === END REGOUT PROLOG ===

peru <- read.dta("swf-peru-ajps_forR.dta")

## Replicating main estimates
estimates1 <- lm(health_b ~ L_gk_budget * L_gk_prebudget2 + factor(year) + factor(deptcode)  ,  data=peru)

estimates2 <- plm(health_b ~ L_gk_budget * L_gk_prebudget2 +ln_pbi_pc + execution_nohealth  ,  data=peru, index=c("deptcode", "year"), model="within", effect = "twoways")

summary(estimates1)
summary(estimates2)

plm_se = vcovHC(estimates2, method='arellano', type='HC0', cluster='group') %>% diag %>% sqrt %>% round(3)
plm_se

## NPC implementation

npc.out <- NPC(data=peru, keep = TRUE, tr.var = "L_gk_budget2",tr.label=1, y.vars =c("health_b",  "enviro_b", "def_b"),block.var=c("deptcode"),n.perms=1000, alternative = "two.sided", seed=123, comb.fun="ProductCF",test.statistic = "StudentsT",  FWE.adj=FALSE )

round(npc.out$p.value, 2) 

npc.out2 <- NPC(data=peru, keep = TRUE, tr.var = "L_gk_budget2",tr.label=1, y.vars =c("health_facility_visit",  "licensed_postnatal"),block.var=c("deptcode"),n.perms=1000, alternative = "two.sided", seed=123, comb.fun="ProductCF",test.statistic = "StudentsT",  FWE.adj=FALSE )

round(npc.out2$p.value, 2) 

npc.out3 <- NPC(data=peru, keep = TRUE, tr.var = "L_gk_budget2",tr.label=1, y.vars =c("health_facility_visit",  "licensed_postnatal","health_b",  "enviro_b", "def_b" ),block.var=c("deptcode"),n.perms=1000, alternative = "two.sided", seed=123, comb.fun="ProductCF",test.statistic = "StudentsT",  FWE.adj=FALSE )

round(npc.out3$p.value, 2) 





