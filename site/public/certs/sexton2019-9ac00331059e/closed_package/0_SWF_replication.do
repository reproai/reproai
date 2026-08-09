* === REPROAI CLOSURE (line1-core 0.9.0) — injected; pins seeds/sort/processors, changes the RNG stream by design ===
set more off
capture set seed 20260708
capture set sortseed 20260708
capture set processors 1
* === END REPROAI CLOSURE ===
capture ssc install unique
capture ssc install estout
adopath ++ "~/stata_packages"
**************
*** How Government Reactions to Violence Worsen Social Welfare: Evidence from Peru
*** Sexton, Wellhausen and Findley
*** October 2018
*** Replication code
***************

/* Datafiles description
- Budget data come from the World Bank's BOOST program. Raw data available: http://boost.worldbank.org/country/peru
- Violence data are coded from Peru's Defensoria del Pueblo. Reports are available: http://www.defensoria.gob.pe/blog/tag/reporte-de-conflictos-sociales/
The relevant incidents are 'acciondes de violencia subversiva' We include a dataset of extracted and coded incidents.
- Congressional debate data come from the Peru Congress's 'Diario de los Debates,' available:  
- Health information is sourced from USAID's Demographic and Health Survey (DHS): https://dhsprogram.com/data/available-datasets.cfm
- LAPOP survey data for Peru are available: https://www.vanderbilt.edu/lapop/raw-data.php
*/

** NOTE: The BRL command may be installed from: https://economics.byu.edu/frandsen/Pages/software.aspx
** In addition, the brl.ado file is included in this replication dataset
** Type 'personal' in Stata command line to locate personal ado directory
** Move brl.ado brl.hlp brl.pkg to that directory

/* Data accessed in this replication file:

swf-peru-ajps.dta
debate_attacks.dta
attacks_list.dta
hurdle.dta
swf-peru-ajps_forR.dta

*/

*** Created in STATA/MP version 13.1

clear all
set matsize 4000
* set more off

** Change to appropriate working directory (e.g.)

cd "."

** Check packages
capture ssc install ivreg2
* ===REGOUT cmd_0_SWF_replication_1=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_1 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=52"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_1"
}
capture ssc install ranktest

* === AUTO-INJECTED: livreg2.mlib repair for ivreg2 r(3000) ===
capture mata: mata drop ms_vcvorthog()
capture mata: mata drop m_calckw()
capture mata: mata drop m_omega()
capture mata: mata drop s_vkernel()
capture mata: mata drop s_cdsy()
capture mata: mata mlib index
* === END AUTO-INJECTED ===


** Set scheme, temporarily
* set scheme s1mono

********************
* Variable Labels 
********************

capture program label_var1
label var acute_under5_diarrhea_pc "Number of cases of acute diarrhea in under-5 children per capita"
label var acute_under5_respiratory_pc "Number of cases of acute respiratory illness in under-5 children per capita"
label var budget_mining "Number of mining conflict incidents during budget period"
label var non_budget_mining "Number of mining conflict incidents during non budget period"
label var non_mining "Number of non-mining, non-insurgent protest incidents"
label var enviro_b "Environment budget share (percent)"
label var culture_b "Culture budget share (percent)"
label var def_b "Defense budget share (percent)"
label var def_s "Defense spending share (percent)"
label var health_b "Health budget share (percent)"
label var health_s "Health spending share (percent)"
label var socialservice_b "Combined social services budget share (percent)"
label var socialservice_s "Combined social services spending share (percent)"
label var deptcode "Department Code"
label var deptname "Department Name"
label var execution "Department Government Budget Execution"
label var execution_nodef "Department Government Budget Execution (excluding defense)"
label var execution_nohealth "Department Government Budget Execution (excluding health)"
label var gk_budget "Number of soldiers killed by insurgents during budget period"
label var gk_budget2 "Dummy for soldiers killed by insurgents during budget period"
label var gk_prebudget "Number of soldiers killed by insurgents during pre-budget period"
label var gk_prebudget2 "Dummy for soldiers killed by insurgents during pre-budget period"
label var gk_december "Number of soldiers killed by insurgents during December"
label var health_usage_women "Share of women reporting usage of health facilities this year (LAPOP)"
label var health_usage_women_highinc "Share of women in top quartile of income reporting usage of health facilities this year (LAPOP)"
label var health_usage_women_lowinc "Share of women in bottom quartile income reporting usage of health facilities this year (LAPOP)"
label var health_usage_men "Share of men reporting usage of health facilities this year (LAPOP)"
label var health_facility_visit "Share of women reporting visit to health facilities this year (DHS)"
label var licensed_postnatal "Share of births reporting postnatal care by licensed professional (DHS)"
label var infant_mortality "Department infant mortality rate (WHO definition) using DHS data"
label var year "Year"
label var def_budget_mi "Multiply imputed defense budget"
label var def_spent_mi "Multiply imputed defense spending"
label var ln_pbi_pc "GDP per capita (log transformed)"
label var population "Population"
label var pop100k "Population (in 100k)"
label var pride "Share expressing national pride (LAPOP)"
label var problem_crime "Share reporting crime as a problem (LAPOP)"
label var problem_security "Share reporting security as a problem (LAPOP)"
label var problem_terrorism "Share reporting terrorism as a problem (LAPOP)"
label var inc_vote_change "Change in vote share for legislative incumbent party 2006 to 2011"
label var senderista "Department experienced any dissident attacks during time series"
label var distbudget "Department budget (Soles)"
label var high_def_bshare "Dummy for above median defense budget share"
label define yesno 0 "no"  1 "yes"
label values gk_budget2 yesno
label values gk_prebudget2 yesno
label values high_def_bshare yesno
label values senderista yesno
end

********************
* Manuscript Tables
********************

use swf-peru-ajps, clear
tsset deptcode year
label_var1

* Table 1: Unexpected budget-period soldier fatalities decrease total social services and health sector budget shares/spending, and increase defense budget shares/spending.

eststo clear
local __ro_c1_L1 = 0
foreach y in socialservice_b socialservice_s health_b health_s{
xtreg `y' cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc execution_nohealth i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_1===
local __ro_c1_L1 = `__ro_c1_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_1_i`__ro_c1_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=120"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_1_i`__ro_c1_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_1_i`__ro_c1_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_1_i`__ro_c1_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
}

local __ro_c2_L1 = 0
foreach y in def_b def_s {
xtreg `y' cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc execution_nodef i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_2===
local __ro_c2_L1 = `__ro_c2_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_2_i`__ro_c2_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=125"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_2_i`__ro_c2_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_2_i`__ro_c2_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_2_i`__ro_c2_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
}

esttab using "table1.tex", keep(L.gk_budget cL.gk_budget#cL.gk_prebudget2 L.gk_prebudget2 ///
  ln_pbi_pc execution_nodef execution_nohealth) cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_g Departments")  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 2: Budget-period soldier fatalities increase the likelihood of congressional debate on fatalities and defense spending.

use debate_attacks, clear

label var ln_numberkilled "Log number of goverment fatalities"
label var CasualtiesfromSL "Casualities from Sendero mentioned in debate"
label var Fundingformilitary "Funding for military mentioned in debate"
label var id "Unique id for incident"
label var After "Is date of debate after the incident"
label define yesno 0 "no"  1 "yes"
label values CasualtiesfromSL yesno
label values Fundingformilitary yesno
label values After yesno

eststo clear
reg CasualtiesfromSL After , vce(cl id)
* ===REGOUT cmd_0_SWF_replication_3===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_3 TYPE=ols SCRIPT=0_SWF_replication.do LINE=148"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_3.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_3.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_3"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
margins, at(After=(0 1))
* ===REGOUT cmd_61===
capture confirm matrix r(table)
if _rc == 0 {
    tempname __regout_rt
    matrix `__regout_rt' = r(table)
    local __regout_cols : colnames `__regout_rt'
    capture noisily display "REGOUT_START cmd_61 TYPE=margins SCRIPT=0_SWF_replication.do LINE=150"
    capture noisily display "REGOUT_CMD margins"
    capture noisily display "REGOUT_CMDLINE margins, at(After=(0 1))"
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    capture noisily display "REGOUT_COEFS"
    foreach __regout_c of local __regout_cols {
        local __regout_b = el(`__regout_rt', 1, colnumb(`__regout_rt', "`__regout_c'"))
        local __regout_se = el(`__regout_rt', 2, colnumb(`__regout_rt', "`__regout_c'"))
        capture noisily display "`__regout_c'	" %20.12f `__regout_b' "	" %20.12f `__regout_se'
    }
    capture noisily display "REGOUT_END cmd_61"
}
reg Fundingformilitary After , vce(cl id)
* ===REGOUT cmd_0_SWF_replication_4===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_4 TYPE=ols SCRIPT=0_SWF_replication.do LINE=151"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_4.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_4.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_4"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
margins, at(After=(0 1))
* ===REGOUT cmd_62===
capture confirm matrix r(table)
if _rc == 0 {
    tempname __regout_rt
    matrix `__regout_rt' = r(table)
    local __regout_cols : colnames `__regout_rt'
    capture noisily display "REGOUT_START cmd_62 TYPE=margins SCRIPT=0_SWF_replication.do LINE=153"
    capture noisily display "REGOUT_CMD margins"
    capture noisily display "REGOUT_CMDLINE margins, at(After=(0 1))"
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    capture noisily display "REGOUT_COEFS"
    foreach __regout_c of local __regout_cols {
        local __regout_b = el(`__regout_rt', 1, colnumb(`__regout_rt', "`__regout_c'"))
        local __regout_se = el(`__regout_rt', 2, colnumb(`__regout_rt', "`__regout_c'"))
        capture noisily display "`__regout_c'	" %20.12f `__regout_b' "	" %20.12f `__regout_se'
    }
    capture noisily display "REGOUT_END cmd_62"
}
***
reg CasualtiesfromSL c.After##c.numberkilled , vce(cl id)
* ===REGOUT cmd_0_SWF_replication_5===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_5 TYPE=ols SCRIPT=0_SWF_replication.do LINE=155"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_5.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_5.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_5"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
margins, dydx(After) at(numberkilled=(1 2 5 10))
* ===REGOUT cmd_63===
capture confirm matrix r(table)
if _rc == 0 {
    tempname __regout_rt
    matrix `__regout_rt' = r(table)
    local __regout_cols : colnames `__regout_rt'
    capture noisily display "REGOUT_START cmd_63 TYPE=margins SCRIPT=0_SWF_replication.do LINE=157"
    capture noisily display "REGOUT_CMD margins"
    capture noisily display "REGOUT_CMDLINE margins, dydx(After) at(numberkilled=(1 2 5 10))"
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    capture noisily display "REGOUT_COEFS"
    foreach __regout_c of local __regout_cols {
        local __regout_b = el(`__regout_rt', 1, colnumb(`__regout_rt', "`__regout_c'"))
        local __regout_se = el(`__regout_rt', 2, colnumb(`__regout_rt', "`__regout_c'"))
        capture noisily display "`__regout_c'	" %20.12f `__regout_b' "	" %20.12f `__regout_se'
    }
    capture noisily display "REGOUT_END cmd_63"
}
reg Fundingformilitary c.After##c.numberkilled , vce(cl id)
* ===REGOUT cmd_0_SWF_replication_6===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_6 TYPE=ols SCRIPT=0_SWF_replication.do LINE=158"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_6.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_6.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_6"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
margins, dydx(After) at(numberkilled=(1 2 5 10))
* ===REGOUT cmd_64===
capture confirm matrix r(table)
if _rc == 0 {
    tempname __regout_rt
    matrix `__regout_rt' = r(table)
    local __regout_cols : colnames `__regout_rt'
    capture noisily display "REGOUT_START cmd_64 TYPE=margins SCRIPT=0_SWF_replication.do LINE=160"
    capture noisily display "REGOUT_CMD margins"
    capture noisily display "REGOUT_CMDLINE margins, dydx(After) at(numberkilled=(1 2 5 10))"
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    capture noisily display "REGOUT_COEFS"
    foreach __regout_c of local __regout_cols {
        local __regout_b = el(`__regout_rt', 1, colnumb(`__regout_rt', "`__regout_c'"))
        local __regout_se = el(`__regout_rt', 2, colnumb(`__regout_rt', "`__regout_c'"))
        capture noisily display "`__regout_c'	" %20.12f `__regout_b' "	" %20.12f `__regout_se'
    }
    capture noisily display "REGOUT_END cmd_64"
}


esttab using "table2.tex", keep(After numberkilled c.After#c.numberkilled) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N (sessions)" "N_clust Fatal attacks" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* Table 3: Soldier fatalities indirectly increase infant mortality.

use swf-peru-ajps, clear
tsset deptcode year
label_var1

eststo clear
local __ro_c7_L1 = 0
foreach y in socialservice_b socialservice_s health_b health_s {
ivregress 2sls F.infant_mortality i.year i.deptcode L.gk_prebudget ln_pbi_pc  execution_nohealth (`y' = L.gk_budget), vce( cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_2=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_2 TYPE=ivregress SCRIPT=0_SWF_replication.do LINE=499"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_2"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_7_fs1 for `y'===
capture noisily estimates store __ivest_7
capture noisily quietly regress `y' L.gk_budget i.year i.deptcode L.gk_prebudget ln_pbi_pc execution_nohealth
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_7_fs1_i`__regout_cmd_7_iter' TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=176"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR `y'"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_7_fs1_i`__regout_cmd_7_iter'"
}
capture noisily estimates restore __ivest_7
* ===REGOUT cmd_0_SWF_replication_7===
local __ro_c7_L1 = `__ro_c7_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_7_i`__ro_c7_L1' TYPE=iv SCRIPT=0_SWF_replication.do LINE=176"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_7_i`__ro_c7_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_7_i`__ro_c7_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_7_i`__ro_c7_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_20.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_20.csv", replace
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_19.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_19.csv", replace
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_18.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_18.csv", replace
}
eststo
}

esttab using "table3.tex", keep(socialservice_b socialservice_s health_b health_s) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 
  
*** Table 3: First stage F-test

local __ro_c8_L1 = 0
foreach y in socialservice_b socialservice_s health_b health_s{
qui xtreg `y' L.gk_budget L.gk_prebudget ln_pbi_pc  execution_nohealth , fe  vce( cl deptcode)
* ===REGOUT cmd_0_SWF_replication_8===
local __ro_c8_L1 = `__ro_c8_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_8_i`__ro_c8_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=190"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_8_i`__ro_c8_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_8_i`__ro_c8_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_8_i`__ro_c8_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
di "First stage F statistic for `y': `e(F)'"
}  
  
* Table 4: Soldier fatalities in the previous year's budget period reduce women's usage of local general and postnatal health services.

eststo clear
xtreg health_facility_visit cL.gk_budget cL.gk_prebudget ln_pbi_pc execution_nohealth    i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_9===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_9 TYPE=ols SCRIPT=0_SWF_replication.do LINE=197"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_9.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_9.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_9"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg licensed_postnatal cL.gk_budget cL.gk_prebudget ln_pbi_pc execution_nohealth    i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_10===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_10 TYPE=ols SCRIPT=0_SWF_replication.do LINE=199"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_10.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_10.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_10"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "table4.tex", keep(L.gk_budget L.gk_prebudget ln_pbi_pc execution_nohealth) ///
  cells(b(star fmt(3)) se(par fmt(3))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 5: Reductions in women's usage of local general and postnatal health services increase infant mortality in t+1.

eststo clear
ivregress 2sls F.infant_mortality i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution    (licensed_postnatal = L.gk_budget), vce( cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_3=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_3 TYPE=ivregress SCRIPT=0_SWF_replication.do LINE=728"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_3"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_11_fs1 for licensed_postnatal===
capture noisily estimates store __ivest_11
capture noisily quietly regress licensed_postnatal L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_11_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=209"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR licensed_postnatal"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_11_fs1"
}
capture noisily estimates restore __ivest_11
* ===REGOUT cmd_0_SWF_replication_11===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_11 TYPE=iv SCRIPT=0_SWF_replication.do LINE=209"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_11.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_11.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_11"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_3.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_3.csv", replace
}
eststo
ivregress 2sls F.infant_mortality i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution   (health_facility_visit = L.gk_budget ), vce( cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_4=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_4 TYPE=ivregress SCRIPT=0_SWF_replication.do LINE=794"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_4"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_12_fs1 for health_facility_visit===
capture noisily estimates store __ivest_12
capture noisily quietly regress health_facility_visit L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_12_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=212"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR health_facility_visit"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_12_fs1"
}
capture noisily estimates restore __ivest_12
* ===REGOUT cmd_0_SWF_replication_12===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_12 TYPE=iv SCRIPT=0_SWF_replication.do LINE=212"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_12.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_12.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_12"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
#delimit cr
capture noisily export delimited using "analysis_data_spec_4.csv" if e(sample), replace
if _rc != 0 {
    capture noisily export delimited using "analysis_data_spec_4.csv", replace
}
eststo

esttab using "table5.tex", keep(licensed_postnatal health_facility_visit) ///
  cells(b(star fmt(0)) se(par fmt(0))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

  
*** First stage F-test

local __ro_c13_L1 = 0
foreach y in licensed_postnatal health_facility_visit{
qui reg `y' L.gk_budget L.gk_prebudget  ,   vce( cl deptcode)
* ===REGOUT cmd_0_SWF_replication_13===
local __ro_c13_L1 = `__ro_c13_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_13_i`__ro_c13_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=224"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_13_i`__ro_c13_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_13_i`__ro_c13_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_13_i`__ro_c13_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
di "First stage F statistic for `y': `e(F)'"
}  

  
* Table 6: Survey evidence suggests that soldier fatalities do not affect citizens' perceptions of security.

eststo clear
xtreg problem_security cL.gk_budget cL.gk_prebudget2 ln_pbi_pc   i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_14===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_14 TYPE=ols SCRIPT=0_SWF_replication.do LINE=232"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_14.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_14.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_14"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg problem_terrorism cL.gk_budget cL.gk_prebudget2 ln_pbi_pc   i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_15===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_15 TYPE=ols SCRIPT=0_SWF_replication.do LINE=234"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_15.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_15.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_15"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg problem_crime cL.gk_budget cL.gk_prebudget2 ln_pbi_pc   i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_16===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_16 TYPE=ols SCRIPT=0_SWF_replication.do LINE=236"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_16.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_16.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_16"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "table6.tex", keep(L.gk_budget) ///
  cells(b(star fmt(3)) se(par fmt(3))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

  
********************
* Appendix
********************


* Table 1: Summary Statistics
capture noisily sum infant_mortality socialservice_b health_b def_b socialservice_s health_s def_s  ///
health_usage_women health_facility_visit licensed_postnatal problem_security problem_terrorism problem_crime
capture noisily sum gk_budget gk_prebudget gk_december if year<2011
 
* Figure 1: Average number of dissident attacks that kill soldiers, by month

use attacks_list,clear

collapse (sum) numgovkilled, by(year month)
tsset month year
tsfill, full
replace numgovkilled=0 if missing(numgovkilled)
capture rename gov_killed_event __jbak_1
capture noisily gen gov_killed_event=(numgovkilled>0)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_1 gov_killed_event
}
else {
    capture drop __jbak_1
}
sort year month
bysort month: egen mean_govkilled=mean(numgovkilled)
bysort month: egen mean_govkilled2=mean(gov_killed_event)

twoway  (lpolyci numgovkilled month) (scatter mean_govkilled month) , legend(off) xlabel(1(1)12) ///
 xtitle("                                                                             Budget Period ")	  xline (8.5 11.5) ///
 ytitle("Average Number of Soldier Deaths")
* ===REPROAI-FIG fig_0_SWF_replication_1=== (injected; exports the just-drawn graph)
capture quietly mkdir "reproai_results"
capture quietly mkdir "reproai_results/figures"
capture noisily graph export "reproai_results/figures/fig_0_SWF_replication_1.pdf", replace
 graph export "events_month.pdf",replace

* Table 2: Robustness: Biased-reduced Linearization

use swf-peru-ajps, clear
tsset deptcode year
label_var1

forvalues i=2007/2011{
gen yr`i'=(year==`i')
}
forvalues i=1/26{
 gen dpt`i'=(deptcode==`i')
}
capture rename L_gk_budget __jbak_2
capture noisily gen L_gk_budget=L.gk_budget
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_2 L_gk_budget
}
else {
    capture drop __jbak_2
}
capture rename L_gk_prebudget2 __jbak_3
capture noisily gen L_gk_prebudget2=L.gk_prebudget2
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_3 L_gk_prebudget2
}
else {
    capture drop __jbak_3
}
capture rename interaction __jbak_4
capture noisily gen interaction=(L_gk_budget*L_gk_prebudget2)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_4 interaction
}
else {
    capture drop __jbak_4
}

eststo clear
brl def_b L_gk_budget L_gk_prebudget2 interaction ln_pbi_pc  yr2008-yr2010 dpt1-dpt7 dpt9-dpt20 dpt22-dpt25 execution  , cluster(deptcode)
eststo
brl health_b L_gk_budget L_gk_prebudget2 interaction ln_pbi_pc  yr2008-yr2010 dpt1-dpt7 dpt9-dpt20 dpt22-dpt25 execution  , cluster(deptcode)
eststo


esttab using "Appendix_table2.tex", keep(L_gk_budget L_gk_prebudget2 interaction ln_pbi_pc execution) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 



* Table 3: Non-parametric combination of results (R file)

** See "SWF-NPC-implmentation.R"

* Table 4: Robustness: LDV

eststo clear
xtreg def_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc L.def_b execution_nodef  i.year , fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_17===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_17 TYPE=ols SCRIPT=0_SWF_replication.do LINE=340"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_17.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_17.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_17"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg health_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc L.health_b execution_nohealth i.year , fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_18===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_18 TYPE=ols SCRIPT=0_SWF_replication.do LINE=342"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_18.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_18.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_18"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table4.tex", keep(L.gk_budget cL.gk_budget#cL.gk_prebudget2  ln_pbi_pc execution_nodef execution_nohealth) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* Table 5: Robustness: First differences

eststo clear
xtreg D.def_b cLD.gk_budget##cL.gk_prebudget2 ln_pbi_pc execution_nodef i.year    ,  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_19===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_19 TYPE=ols SCRIPT=0_SWF_replication.do LINE=353"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_19.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_19.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_19"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg D.health_b cLD.gk_budget##cL.gk_prebudget2 ln_pbi_pc execution_nohealth i.year   ,  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_20===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_20 TYPE=ols SCRIPT=0_SWF_replication.do LINE=355"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_20.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_20.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_20"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo


esttab using "Appendix_table5.tex", drop(*.year _cons) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* Table 6: Accounting for mining-sector violence does not change results

eststo clear
xtreg health_b cL.gk_budget##cL.gk_prebudget2 L.budget_mining cL.non_budget_mining L.non_mining ln_pbi_pc execution  i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_21===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_21 TYPE=ols SCRIPT=0_SWF_replication.do LINE=367"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_21.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_21.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_21"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg def_b cL.gk_budget##cL.gk_prebudget2 L.budget_mining cL.non_budget_mining L.non_mining ln_pbi_pc execution  i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_22===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_22 TYPE=ols SCRIPT=0_SWF_replication.do LINE=369"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_22.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_22.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_22"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table6.tex", keep(L.gk_budget cL.gk_budget#cL.gk_prebudget2 L.gk_prebudget2 ln_pbi_pc L.budget_mining L.non_budget_mining execution ) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Figure 2: Treatment effects with a treatment dummy with varying cutpoints

capture rename killeddummy_0 __jbak_5
capture noisily gen killeddummy_0=(gk_budget>0) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_5 killeddummy_0
}
else {
    capture drop __jbak_5
}
capture rename killeddummy_1 __jbak_6
capture noisily gen killeddummy_1=(gk_budget>1) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_6 killeddummy_1
}
else {
    capture drop __jbak_6
}
capture rename killeddummy_2 __jbak_7
capture noisily gen killeddummy_2=(gk_budget>2) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_7 killeddummy_2
}
else {
    capture drop __jbak_7
}
capture rename killeddummy_3 __jbak_8
capture noisily gen killeddummy_3=(gk_budget>3) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_8 killeddummy_3
}
else {
    capture drop __jbak_8
}
capture rename killeddummy_4 __jbak_9
capture noisily gen killeddummy_4=(gk_budget>4) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_9 killeddummy_4
}
else {
    capture drop __jbak_9
}
capture rename killeddummy_5 __jbak_10
capture noisily gen killeddummy_5=(gk_budget>5) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_10 killeddummy_5
}
else {
    capture drop __jbak_10
}
capture rename killeddummy_6 __jbak_11
capture noisily gen killeddummy_6=(gk_budget>6) if !missing(gk_budget)
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_11 killeddummy_6
}
else {
    capture drop __jbak_11
}


xtreg health_b L.killeddummy_0 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_23===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_23 TYPE=ols SCRIPT=0_SWF_replication.do LINE=443"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_23.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_23.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_23"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_1 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_24===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_24 TYPE=ols SCRIPT=0_SWF_replication.do LINE=444"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_24.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_24.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_24"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_2 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_25===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_25 TYPE=ols SCRIPT=0_SWF_replication.do LINE=445"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_25.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_25.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_25"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_3 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_26===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_26 TYPE=ols SCRIPT=0_SWF_replication.do LINE=446"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_26.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_26.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_26"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_4 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_27===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_27 TYPE=ols SCRIPT=0_SWF_replication.do LINE=447"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_27.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_27.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_27"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_5 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_28===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_28 TYPE=ols SCRIPT=0_SWF_replication.do LINE=448"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_28.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_28.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_28"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
xtreg health_b L.killeddummy_6 i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_29===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_29 TYPE=ols SCRIPT=0_SWF_replication.do LINE=449"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_29.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_29.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_29"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}

*** Treatment effects exported to hurdle.dta

use hurdle,clear

capture rename u __jbak_12
capture noisily gen u=coef+se
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_12 u
}
else {
    capture drop __jbak_12
}
capture rename l __jbak_13
capture noisily gen l=coef-se
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_13 l
}
else {
    capture drop __jbak_13
}

twoway rcap u l band  || ///
    scatter coef band ///
    , legend(off) ///
     xtitle("Treatment=1 for X or greater fatalities") ///
    yline(0, lc(black)) ytitle("Treatment effect on Health Budget Share")
* ===REPROAI-FIG fig_0_SWF_replication_2=== (injected; exports the just-drawn graph)
capture quietly mkdir "reproai_results"
capture quietly mkdir "reproai_results/figures"
capture noisily graph export "reproai_results/figures/fig_0_SWF_replication_2.pdf", replace
 graph export "hurdle1.pdf",replace

* Table 7: Soldiers killed during budget period and defense share

use swf-peru-ajps, clear
tsset deptcode year
label_var1

replace def_budget_mi=(def_budget_mi/1000000)
replace def_spent_mi=(def_spent_mi/1000000)

replace def_budget_mi=. if def_budget_mi==0

capture rename Ldef_budget __jbak_14
capture noisily gen Ldef_budget=L.def_budget_mi
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_14 Ldef_budget
}
else {
    capture drop __jbak_14
}
capture rename L2def_budget __jbak_15
capture noisily gen L2def_budget=L2.def_budget_mi
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_15 L2def_budget
}
else {
    capture drop __jbak_15
}
capture rename Ldef_spent __jbak_16
capture noisily gen Ldef_spent=L.def_spent_mi
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_16 Ldef_spent
}
else {
    capture drop __jbak_16
}
capture rename L2def_spent __jbak_17
capture noisily gen L2def_spent=L2.def_spent_mi
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_17 L2def_spent
}
else {
    capture drop __jbak_17
}

mi set wide
mi register imputed def_budget_mi
mi impute pmm def_budget_mi Ldef_budget L2def_budget distbudget if year>2007, add(20) knn(1)  rseed(2232) force
eststo clear
sort deptcode year
capture rename treatment __jbak_18
capture noisily gen treatment= L.gk_budget
local __janitor_rc = _rc
if `__janitor_rc' != 0 {
    capture rename __jbak_18 treatment
}
else {
    capture drop __jbak_18
}
mi estimate, post dots:  xtreg def_budget_mi c.treatment##high_def_bshare   i.year , fe vce(cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_30===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_30 TYPE=ols SCRIPT=0_SWF_replication.do LINE=543"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_30.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_30.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_30"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo


esttab using "Appendix_table7.tex", keep( treatment 1.high_def_bshare#c.treatment 1.high_def_bshare ) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


*  Table 8: No effects of budgeting on child morbidity

use swf-peru-ajps, clear
tsset deptcode year
label_var1

eststo clear
ivreg2 F.acute_under5_diarrhea_pc i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (health_b = L.gk_budget  ), cluster( deptcode) 
* ===REGOUT cmd_0_SWF_replication_5=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_5 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=1861"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_5"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_31_fs1 for health_b===
capture noisily estimates store __ivest_31
capture noisily quietly regress health_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_31_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=559"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR health_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_31_fs1"
}
capture noisily estimates restore __ivest_31
* ===REGOUT cmd_0_SWF_replication_31===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_31 TYPE=iv SCRIPT=0_SWF_replication.do LINE=559"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_31.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_31.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_31"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
ivreg2 F.acute_under5_diarrhea_pc i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (enviro_b = L.gk_budget  ), cluster( deptcode)
* ===REGOUT cmd_0_SWF_replication_6=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_6 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=1922"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_6"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_32_fs1 for enviro_b===
capture noisily estimates store __ivest_32
capture noisily quietly regress enviro_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_32_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=561"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR enviro_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_32_fs1"
}
capture noisily estimates restore __ivest_32
* ===REGOUT cmd_0_SWF_replication_32===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_32 TYPE=iv SCRIPT=0_SWF_replication.do LINE=561"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_32.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_32.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_32"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
ivreg2 F.acute_under5_diarrhea_pc i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (culture_b = L.gk_budget  ), cluster( deptcode)
* ===REGOUT cmd_0_SWF_replication_7=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_7 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=1983"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_7"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_33_fs1 for culture_b===
capture noisily estimates store __ivest_33
capture noisily quietly regress culture_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_33_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=563"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR culture_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_33_fs1"
}
capture noisily estimates restore __ivest_33
* ===REGOUT cmd_0_SWF_replication_33===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_33 TYPE=iv SCRIPT=0_SWF_replication.do LINE=563"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_33.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_33.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_33"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
ivreg2 F.acute_under5_respiratory_pc  i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (health_b = L.gk_budget  ), cluster( deptcode) 
* ===REGOUT cmd_0_SWF_replication_8=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_8 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=2044"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_8"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_34_fs1 for health_b===
capture noisily estimates store __ivest_34
capture noisily quietly regress health_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_34_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=565"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR health_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_34_fs1"
}
capture noisily estimates restore __ivest_34
* ===REGOUT cmd_0_SWF_replication_34===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_34 TYPE=iv SCRIPT=0_SWF_replication.do LINE=565"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_34.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_34.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_34"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
ivreg2 F.acute_under5_respiratory_pc i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (enviro_b = L.gk_budget  ), cluster( deptcode) 
* ===REGOUT cmd_0_SWF_replication_9=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_9 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=2105"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_9"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_35_fs1 for enviro_b===
capture noisily estimates store __ivest_35
capture noisily quietly regress enviro_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_35_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=567"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR enviro_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_35_fs1"
}
capture noisily estimates restore __ivest_35
* ===REGOUT cmd_0_SWF_replication_35===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_35 TYPE=iv SCRIPT=0_SWF_replication.do LINE=567"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_35.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_35.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_35"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo 
ivreg2 F.acute_under5_respiratory_pc i.year i.deptcode cL.gk_prebudget ln_pbi_pc  execution_nohealth   (culture_b = L.gk_budget  ), cluster( deptcode) 
* ===REGOUT cmd_0_SWF_replication_10=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_10 TYPE=ivreg2 SCRIPT=0_SWF_replication.do LINE=2166"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_10"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_36_fs1 for culture_b===
capture noisily estimates store __ivest_36
capture noisily quietly regress culture_b L.gk_budget i.year i.deptcode cL.gk_prebudget ln_pbi_pc execution_nohealth, vce(cluster deptcode)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_36_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=569"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR culture_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_36_fs1"
}
capture noisily estimates restore __ivest_36
* ===REGOUT cmd_0_SWF_replication_36===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_36 TYPE=iv SCRIPT=0_SWF_replication.do LINE=569"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_36.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_36.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_36"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table8.tex", keep( health_b enviro_b culture_b) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 



* Table 9: Departments with soldier fatalities are poorer but otherwise similar

use swf-peru-ajps, clear
tsset deptcode year
label_var1

collapse senderista  ln_pbi_pc pop100k  infant_mortality def_b health_b , by(deptcode)

eststo clear
local __ro_c37_L1 = 0
foreach y in ln_pbi_pc pop100k def_b health_b  infant_mortality {
reg `y'  senderista, robust
* ===REGOUT cmd_0_SWF_replication_37===
local __ro_c37_L1 = `__ro_c37_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_37_i`__ro_c37_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=588"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_37_i`__ro_c37_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_37_i`__ro_c37_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_37_i`__ro_c37_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo 
}


esttab using "Appendix_table9.tex",  keep(senderista) cells(b(star fmt(2)) se(par fmt(2))) stats(N, labels(N) fmt(0)) starlevel(* .05 ** .01 *** .001) replace tex nolz label noabb wrap varwidth(50) mtitles



* Table 10: Soldier fatalities in the budget period reduce other social services sector budget shares.

use swf-peru-ajps, clear
tsset deptcode year
label_var1

eststo clear
xtreg enviro_b cL.gk_budget cL.gk_prebudget2 ln_pbi_pc execution_nohealth  i.year, fe  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_38===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_38 TYPE=ols SCRIPT=0_SWF_replication.do LINE=604"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_38.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_38.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_38"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg culture_b cL.gk_budget cL.gk_prebudget2 ln_pbi_pc execution_nohealth  i.year, fe  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_39===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_39 TYPE=ols SCRIPT=0_SWF_replication.do LINE=606"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_39.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_39.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_39"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table10.tex", keep( L.gk_budget L.gk_prebudget2 ln_pbi_pc  execution_nohealth) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* Table 11: Model 1 (year fixed effects): LaGrange Multiplier Autocorrelation Test

eststo clear
reg health_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc  i.year,  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_40===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_40 TYPE=ols SCRIPT=0_SWF_replication.do LINE=617"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_40.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_40.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_40"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

predict residuals0, residuals

reg residuals0 cL.gk_budget##cL.gk_prebudget2  L.residuals0
* ===REGOUT cmd_0_SWF_replication_41===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_41 TYPE=ols SCRIPT=0_SWF_replication.do LINE=622"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_41.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_41.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_41"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}

scalar N=e(N)
scalar R2=e(r2)
scalar NR2= N*R2 
scalar list N  R2  NR2 

scalar chi15=invchi2(1, .95) 
scalar list chi15 NR2

eststo clear
reg def_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc i.year,  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_42===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_42 TYPE=ols SCRIPT=0_SWF_replication.do LINE=633"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_42.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_42.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_42"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

predict residuals, residuals

reg residuals cL.gk_budget##cL.gk_prebudget2  L.residuals
* ===REGOUT cmd_0_SWF_replication_43===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_43 TYPE=ols SCRIPT=0_SWF_replication.do LINE=638"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_43.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_43.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_43"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}

scalar N=e(N)
scalar R2=e(r2)
scalar NR2= N*R2 
scalar list N  R2  NR2 

scalar chi15=invchi2(1, .95) 
scalar list chi15 NR2

* Table 12: Model 2 (year and department fixed effects): LaGrange Multiplier Autocorrelation Test

eststo clear

reg health_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc i.deptcode i.year, vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_44===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_44 TYPE=ols SCRIPT=0_SWF_replication.do LINE=652"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_44.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_44.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_44"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

predict residuals1, residuals

reg residuals1 cL.gk_budget##cL.gk_prebudget2  L.residuals1
* ===REGOUT cmd_0_SWF_replication_45===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_45 TYPE=ols SCRIPT=0_SWF_replication.do LINE=657"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_45.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_45.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_45"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}

scalar N=e(N)
scalar R2=e(r2) 
scalar NR2= N*R2 
scalar list N  R2  NR2 

scalar chi15=invchi2(1, .95) 
scalar list chi15 NR2

eststo clear
reg def_b cL.gk_budget##cL.gk_prebudget2 ln_pbi_pc  i.deptcode i.year,  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_46===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_46 TYPE=ols SCRIPT=0_SWF_replication.do LINE=668"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_46.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_46.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_46"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

predict residuals2, residuals

reg residuals2 cL.gk_budget##cL.gk_prebudget2   L.residuals2
* ===REGOUT cmd_0_SWF_replication_47===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_47 TYPE=ols SCRIPT=0_SWF_replication.do LINE=673"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_47.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_47.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_47"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}

scalar N=e(N)
scalar R2=e(r2)
scalar NR2= N*R2 
scalar list N  R2  NR2 

scalar chi15=invchi2(1, .95) 
scalar list chi15 NR2


* Table 13: Only recent soldier fatalities reduce incumbent party vote share

eststo clear
reg inc_vote_change gk_budget gk_prebudget ln_pbi_pc, vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_48===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_48 TYPE=ols SCRIPT=0_SWF_replication.do LINE=687"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_48.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_48.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_48"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
reg inc_vote_change health_b ln_pbi_pc, vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_49===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_49 TYPE=ols SCRIPT=0_SWF_replication.do LINE=689"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_49.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_49.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_49"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
reg inc_vote_change gk_budget gk_prebudget health_b ln_pbi_pc, vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_50===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_50 TYPE=ols SCRIPT=0_SWF_replication.do LINE=691"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_50.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_50.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_50"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table13.tex", keep(gk_budget gk_prebudget health_b ln_pbi_pc) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 14: Soldier fatalities increase national pride, briefly

eststo clear
xtreg pride gk_budget gk_prebudget ln_pbi_pc i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_51===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_51 TYPE=ols SCRIPT=0_SWF_replication.do LINE=701"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_51.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_51.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_51"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table14.tex", keep(gk_budget gk_prebudget ln_pbi_pc) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 15: Soldier fatalities in budget period hurt poor women's health access, in particular

eststo clear
xtreg health_usage_women_highinc L.gk_budget i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_52===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_52 TYPE=ols SCRIPT=0_SWF_replication.do LINE=711"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_52.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_52.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_52"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg health_usage_women_lowinc L.gk_budget i.year, fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_53===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_53 TYPE=ols SCRIPT=0_SWF_replication.do LINE=713"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_53.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_53.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_53"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table15.tex", keep(L.gk_budget ) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 16: Placebo: Soldier fatalities in December (after budget period) have no effect on health budget share or women's health facility visits

eststo clear
xtreg health_b   L.gk_budget L.gk_december cL.gk_prebudget ln_pbi_pc    i.year , fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_54===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_54 TYPE=ols SCRIPT=0_SWF_replication.do LINE=723"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_54.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_54.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_54"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg health_facility_visit   L.gk_budget L.gk_december cL.gk_prebudget ln_pbi_pc    i.year , fe vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_55===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_55 TYPE=ols SCRIPT=0_SWF_replication.do LINE=725"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_55.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_55.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_55"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table16.tex", keep(L.gk_budget L.gk_december L.gk_prebudget ln_pbi_pc ) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 17: Placebo: Health budget does not affect last year's infant mortality

eststo clear
ivregress 2sls L.infant_mortality i.year i.deptcode  (health_b = L.gk_budget ), vce( cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_11=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_11 TYPE=ivregress SCRIPT=0_SWF_replication.do LINE=3084"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_11"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_56_fs1 for health_b===
capture noisily estimates store __ivest_56
capture noisily quietly regress health_b L.gk_budget i.year i.deptcode
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_56_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=735"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR health_b"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_56_fs1"
}
capture noisily estimates restore __ivest_56
* ===REGOUT cmd_0_SWF_replication_56===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_56 TYPE=iv SCRIPT=0_SWF_replication.do LINE=735"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_56.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_56.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_56"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
ivregress 2sls L.infant_mortality i.year i.deptcode  (health_s = L.gk_budget ), vce( cl deptcode) 
* ===REGOUT cmd_0_SWF_replication_12=== (injected by reproai close; read-and-print only)
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_12 TYPE=ivregress SCRIPT=0_SWF_replication.do LINE=3145"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_12"
}
* ===FIRSTSTAGE cmd_0_SWF_replication_57_fs1 for health_s===
capture noisily estimates store __ivest_57
capture noisily quietly regress health_s L.gk_budget i.year i.deptcode
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_57_fs1 TYPE=ols_firststage SCRIPT=0_SWF_replication.do LINE=737"
    capture noisily display "REGOUT_CMD regress"
    capture noisily display "REGOUT_DEPVAR health_s"
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
    capture noisily display "REGOUT_END cmd_0_SWF_replication_57_fs1"
}
capture noisily estimates restore __ivest_57
* ===REGOUT cmd_0_SWF_replication_57===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_57 TYPE=iv SCRIPT=0_SWF_replication.do LINE=737"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_57.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_57.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_57"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table17.tex", keep(health_b health_s) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 

* Table 18: First stage estimates

eststo clear
local __ro_c58_L1 = 0
foreach y in socialservice_b socialservice_s health_b health_s{
 xtreg `y' L.gk_budget L.gk_prebudget ln_pbi_pc  execution_nohealth , fe  vce( cl deptcode)
* ===REGOUT cmd_0_SWF_replication_58===
local __ro_c58_L1 = `__ro_c58_L1' + 1
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_58_i`__ro_c58_L1' TYPE=ols SCRIPT=0_SWF_replication.do LINE=748"
    capture noisily display "REGOUT_CMD " e(cmd)
    capture noisily display "REGOUT_CMDLINE " e(cmdline)
    capture noisily display "REGOUT_INSTD " e(instd)
    capture noisily display "REGOUT_INSTS " e(insts)
    capture noisily display "REGOUT_DEPVAR " e(depvar)
    * rdrobust within-bandwidth N override: rdrobust's e(N) is the
    * full input sample, but paper tables report N_h_l + N_h_r
    * (within-bandwidth count). Override e(N) BEFORE REGOUT_N
    * captures it so paper N matches code N.
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(N)", st_numscalar("e(N_h_l)") + st_numscalar("e(N_h_r)"))
    }
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_58_i`__ro_c58_L1'.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_58_i`__ro_c58_L1'.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_58_i`__ro_c58_L1'"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
 di "First stage F statistic for `y': `e(F)'"
eststo
}  

esttab using "Appendix_table18.tex", keep(L.gk_budget) ///
  cells(b(star fmt(2)) se(par fmt(2))) ///
  scalars("N N" "N_clust Departments" "F F-stat" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* Table 19: Disaggregating health access effects by gender

eststo clear
xtreg health_usage_women cL.gk_budget cL.gk_prebudget2 ln_pbi_pc execution i.year, fe  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_59===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_59 TYPE=ols SCRIPT=0_SWF_replication.do LINE=761"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_59.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_59.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_59"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo
xtreg health_usage_men cL.gk_budget cL.gk_prebudget2 ln_pbi_pc execution i.year, fe  vce(cl deptcode)
* ===REGOUT cmd_0_SWF_replication_60===
capture confirm matrix e(b)
if _rc == 0 {
    capture noisily display "REGOUT_START cmd_0_SWF_replication_60 TYPE=ols SCRIPT=0_SWF_replication.do LINE=763"
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
    capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_60.csv" if e(sample), replace
    if _rc != 0 {
        capture noisily export delimited using "analysis_data_cmd_0_SWF_replication_60.csv", replace
    }
    capture noisily display "REGOUT_END cmd_0_SWF_replication_60"
    * rdrobust v10 compat: restore old e() scalar names
    if "`e(cmd)'" == "rdrobust" {
        capture mata: st_numscalar("e(h_bw)", st_numscalar("e(h_l)"))
        capture mata: st_numscalar("e(se_cl)", st_numscalar("e(se_tau_cl)"))
    }
}
eststo

esttab using "Appendix_table19.tex", keep(L.gk_budget ) ///
  cells(b(star fmt(3)) se(par fmt(3))) ///
  scalars("N N" "N_clust Departments" )  starlevel(* .05 ** .01 *** .001) replace tex nolz label noobs noabb wrap varwidth(50) 


* === REPROAI FIGSWEEP === (injected; exports named graphs left in memory)
capture quietly mkdir "reproai_results"
capture quietly mkdir "reproai_results/figures"
capture quietly graph dir
local __reproai_graphs "`r(list)'"
foreach __reproai_g of local __reproai_graphs {
    capture noisily graph export "reproai_results/figures/named_0_SWF_replication_`__reproai_g'.pdf", name(`__reproai_g') replace
}
* === END REPROAI FIGSWEEP ===
