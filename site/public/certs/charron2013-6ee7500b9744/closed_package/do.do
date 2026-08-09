* === REPROAI CLOSURE (line1-core 0.10.0) — injected; pins seeds/sort/processors, changes the RNG stream by design ===
set more off
capture set seed 20260708
capture set sortseed 20260708
capture set processors 1
* === END REPROAI CLOSURE ===

* === AUTO-INJECTED: livreg2.mlib repair for ivreg2 r(3000) ===
capture mata: mata drop ms_vcvorthog()
capture mata: mata drop m_calckw()
capture mata: mata drop m_omega()
capture mata: mata drop s_vkernel()
capture mata: mata drop s_cdsy()
capture mata: mata mlib index
* === END AUTO-INJECTED ===

adopath ++ "~/stata_packages"
* === AUTHOR_BUG_FIX (pipeline-injected 2026-05-11) ===
* Author's original logic tried final2.dta first and only fell back to
* final.dta on rc!=0. But final2.dta exists in the shipped package, so the
* fallback never triggered — and final2.dta has only N=69 obs
* (pc_institutions non-null = 58), while paper Table 1 reports N=73
* (matching final.dta's pc_institutions non-null = 73). Verified: OLS
* reg eqi pc_institutions vce(cluster country) on final.dta gives
* coef=0.2403 (paper says 0.24 ✓); same regression on final2.dta gives
* coef=0.2245 (paper rejects). See author_issues.json AI-1 for evidence.
* --- ORIGINAL (commented) ---
* capture noisily use "final2.dta", clear
* if _rc != 0 {
*     use "final.dta", clear
*     capture noisily egen inversSD = sd(clientalism), by(name)
* }
* --- PATCH: force final.dta + always run the egen helper ---
use "final.dta", clear
capture noisily egen inversSD = sd(clientalism), by(name)
* === END AUTHOR_BUG_FIX ===

***table 1 results, models with fe, Spain is comparison country**
reg eqi pc_institutions, vce (cluster country)
* ===REGOUT cmd_do_1===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_1 TYPE=ols SCRIPT=do.do LINE=9"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_1.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_1.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_1"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_2===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_2 TYPE=ols SCRIPT=do.do LINE=10"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_2.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_2.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_2"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi inst_1600 logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_3===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_3 TYPE=ols SCRIPT=do.do LINE=11"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_3.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_3.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_3"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi inst_1700 logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_4===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_4 TYPE=ols SCRIPT=do.do LINE=12"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_4.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_4.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_4"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi  inst_1750 logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_5===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_5 TYPE=ols SCRIPT=do.do LINE=13"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_5.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_5.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_5"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi  inst_1800 logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_6===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_6 TYPE=ols SCRIPT=do.do LINE=14"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_6.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_6.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_6"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi  inst_1850 logppp logpop capitalregion , vce (cluster country)
* ===REGOUT cmd_do_7===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_7 TYPE=ols SCRIPT=do.do LINE=15"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_7.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_7.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_7"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logppp logpop capitalregion trust , vce (cluster country)
* ===REGOUT cmd_do_8===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_8 TYPE=ols SCRIPT=do.do LINE=16"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_8.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_8.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_8"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logppp logpop capitalregion ger  bel  it nl por uk , vce (robust)
* ===REGOUT cmd_do_9===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_9 TYPE=ols SCRIPT=do.do LINE=17"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_9.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_9.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_9"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logppp logpop capitalregion trust ger  bel  it nl por uk , vce (robust)
* ===REGOUT cmd_do_10===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_10 TYPE=ols SCRIPT=do.do LINE=18"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_10.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_10.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_10"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
**table 2**
reg eqi pc_institutions logpop capitalregion singleparty minority yrspwrconsec threshold autonomous  , vce (cluster country)
* ===REGOUT cmd_do_11===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_11 TYPE=ols SCRIPT=do.do LINE=20"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_11.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_11.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_11"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logpop capitalregion singleparty minority yrspwrconsec threshold autonomous ger  bel  it nl por uk , vce (robust)
* ===REGOUT cmd_do_12===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_12 TYPE=ols SCRIPT=do.do LINE=21"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_12.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_12.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_12"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
reg eqi pc_institutions logpop capitalregion STwage , vce (cluster country)
* ===REGOUT cmd_do_13===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_13 TYPE=ols SCRIPT=do.do LINE=22"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_13.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_13.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_13"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
capture noisily reg eqi pc_institutions logpop capitalregion STwage mezzogiono , vce (cluster country)
***table 3***
ivregress 2sls eqi  logpop capitalregion ger it uk ( clientalism = pc_institutions ) , robust first
* ===REGOUT cmd_do_1=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_1 TYPE=ivregress SCRIPT=do.do LINE=523"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily display "REGOUT_END cmd_do_1"
}
* ===FIRSTSTAGE cmd_do_14_fs1 for clientalism===
capture noisily estimates store __ivest_14
capture noisily quietly regress clientalism pc_institutions logpop capitalregion ger it uk, robust
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_14_fs1 TYPE=ols_firststage SCRIPT=do.do LINE=25"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR clientalism"
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_END cmd_do_14_fs1"
}
capture noisily estimates restore __ivest_14
* ===REGOUT cmd_do_14===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_14 TYPE=iv SCRIPT=do.do LINE=25"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_14.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_14.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_14"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_9.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_9.csv", replace
}
ivregress 2sls eqi  logpop capitalregion ger it uk urb_1860_1850_30 ( pc_all4_tol = pc_institutions literacy1880 )  if clientalism!=.  , robust first
* ===REGOUT cmd_do_2=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_2 TYPE=ivregress SCRIPT=do.do LINE=588"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily display "REGOUT_END cmd_do_2"
}
* ===FIRSTSTAGE cmd_do_15_fs1 for pc_all4_tol===
capture noisily estimates store __ivest_15
capture noisily quietly regress pc_all4_tol pc_institutions literacy1880 logpop capitalregion ger it uk urb_1860_1850_30 if clientalism!=., robust
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_15_fs1 TYPE=ols_firststage SCRIPT=do.do LINE=27"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR pc_all4_tol"
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_END cmd_do_15_fs1"
}
capture noisily estimates restore __ivest_15
* ===REGOUT cmd_do_15===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_15 TYPE=iv SCRIPT=do.do LINE=27"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_15.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_15.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_15"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
ivregress 2sls eqi  logpop capitalregion ger it uk  ( trust=  STwage )  if clientalism!=.  , robust first
* ===REGOUT cmd_do_3=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_3 TYPE=ivregress SCRIPT=do.do LINE=648"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily display "REGOUT_END cmd_do_3"
}
* ===FIRSTSTAGE cmd_do_16_fs1 for trust===
capture noisily estimates store __ivest_16
capture noisily quietly regress trust STwage logpop capitalregion ger it uk if clientalism!=., robust
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_16_fs1 TYPE=ols_firststage SCRIPT=do.do LINE=28"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR trust"
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_END cmd_do_16_fs1"
}
capture noisily estimates restore __ivest_16
* ===REGOUT cmd_do_16===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_16 TYPE=iv SCRIPT=do.do LINE=28"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_16.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_16.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_16"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
ivregress 2sls eqi  logpop capitalregion ger it uk ( clientalism trust= pc_institutions literacy1880 STwage) , robust first
* ===REGOUT cmd_do_4=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_4 TYPE=ivregress SCRIPT=do.do LINE=708"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily display "REGOUT_END cmd_do_4"
}
* === AUTHOR_BUG_FIX 2026-05-12: persist ivregress e(sample) so FS regressions
*     use the SS sample (N=54). Without this, cmd_do_17_fs2 ran on N=69 because
*     `trust` has fewer missings than `clientalism`, so the unconditioned regress
*     pulled in 15 obs the IV had dropped. Paper Table 3 col 7 reports N=54. ===
capture drop __ivest_17_sample
capture noisily gen byte __ivest_17_sample = e(sample)
* ===FIRSTSTAGE cmd_do_17_fs2 for trust===
capture noisily estimates store __ivest_17
capture noisily quietly regress trust pc_institutions literacy1880 STwage logpop capitalregion ger it uk if __ivest_17_sample, robust
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_17_fs2 TYPE=ols_firststage SCRIPT=do.do LINE=29"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR trust"
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_END cmd_do_17_fs2"
}
capture noisily estimates restore __ivest_17
* ===FIRSTSTAGE cmd_do_17_fs1 for clientalism===
capture noisily estimates store __ivest_17
capture noisily quietly regress clientalism pc_institutions literacy1880 STwage logpop capitalregion ger it uk if __ivest_17_sample, robust
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_17_fs1 TYPE=ols_firststage SCRIPT=do.do LINE=29"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR clientalism"
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_END cmd_do_17_fs1"
}
capture noisily estimates restore __ivest_17
* ===REGOUT cmd_do_17===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_do_17 TYPE=iv SCRIPT=do.do LINE=29"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    noisily matrix list e(b), format(%20.12f)
    capture noisily display "REGOUT_N " e(N)
    capture noisily display "REGOUT_R2 " e(r2)
    capture noisily display "REGOUT_R2_A " e(r2_a)
    tempname __regout_se
    capture quietly matrix `__regout_se' = vecdiag(e(V))
    if _rc == 0 {
        capture noisily display "REGOUT_V_DIAG"
        noisily matrix list `__regout_se', format(%20.12f)
    }
    capture noisily display "REGOUT_CLUSTVAR " e(clustvar)
    capture noisily display "REGOUT_VCE " e(vce)
    capture noisily display "REGOUT_ABSORB " e(absvar)
    capture noisily display "REGOUT_ABSVARS " e(absvars)
    capture noisily display "REGOUT_WTYPE " e(wtype)
    capture noisily display "REGOUT_WEXP " e(wexp)
    capture noisily export delimited using "analysis_data_cmd_do_17.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_do_17.csv", replace
    }
    capture noisily display "REGOUT_END cmd_do_17"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}


capture drop inversSD
egen inversSD = sd(clientalism), by(name)
* === REPROAI FIGSWEEP === (injected; exports named graphs left in memory)
capture quietly mkdir "reproai_results"
capture quietly mkdir "reproai_results/figures"
capture quietly graph dir
local __reproai_graphs "`r(list)'"
foreach __reproai_g of local __reproai_graphs {
    capture noisily graph export "reproai_results/figures/named_do_`__reproai_g'.pdf", name(`__reproai_g') replace
}
* === END REPROAI FIGSWEEP ===
