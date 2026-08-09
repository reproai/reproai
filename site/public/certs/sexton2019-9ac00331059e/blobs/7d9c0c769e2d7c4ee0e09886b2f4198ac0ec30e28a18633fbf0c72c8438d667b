program brl, eclass
	version 9
	syntax varlist(min=2 numeric) [if] [in] [aweight pweight/] [, LOGIT CLUSTER(varname) NOINT]  
	marksample touse
	
	
	tempname vc b t df p 
	tempvar _weight v y01 ones intercept
quietly {	
preserve
keep if `touse'
if "`exp'"=="" {
gen _weight = 1 /*replace if there are weights*/
}
else {
gen _weight = `exp'
}

tokenize `varlist'
local lhsvar "`1'"
macro shift 1
local rhsvars "`*'"

tokenize `rhsvars'

local xlistmata `""`1'""'


local k 2
while "``k''"!="" {
local xlistmata `"`xlistmata',"``k''""'

local ++k
}
if "`noint'"=="" {
	local int ""
	}
	else{
	local int noconst
	}

if "`logit'"!="" {
logit `varlist' [weight=_weight],`int'
predict xbeta, xb
predict phat, p

gen v = phat*(1-phat)
gen y01 = xbeta + (`lhsvar'-phat)/v

reg y01 `rhsvars' [w=v*_weight],`int'
local _aweight v
local _pweight _weight

}
else{
reg `varlist' [weight=_weight] if `touse',`int'
gen ones=1
local _aweight ones
local _pweight _weight

}
predict _resid, resid
global S_E_nobs = _result(1)
global S_E_r2 = _result(7)
global S_E_ar2 = _result(8)
global S_E_rmse = _result(9)
global S_E_df = _result(5)
local S_E_nobs = _result(1)
local S_E_r2 = _result(7)
local S_E_ar2 = _result(8)
local S_E_rmse = _result(9)
local S_E_df = _result(5)

matrix `b' = e(b)

	
	drop if _resid == .
	drop if _weight == .
	sort `cluster'
	
	if "`noint'"=="" {
	gen intercept=1
	mata: x=0
	mata: st_view(x,.,(`xlistmata',"intercept"))
	}
	else{
	mata: x=0
	mata: st_view(x,.,(`xlistmata'))
	}


	mata: calcbrl(x, "`cluster'", "`_aweight'", "`_pweight'", "_resid", "e(b)")
	restore 
	matrix `vc' = e(brlvc)
	matrix `df' = e(df)
	matrix `p' = e(brlp)
	matrix `t' = e(brlt)
		
	
	
	if "`noint'"!="" {
	matrix colnames `b'=`rhsvars'
	matrix rownames `vc'=`rhsvars'
	matrix colnames `vc'=`rhsvars'
	matrix rownames `df'=`rhsvars'
	matrix rownames `t'=`rhsvars'
	matrix rownames `p'=`rhsvars'
	}
else{
matrix colnames `b'=`rhsvars' _cons
matrix rownames `vc'=`rhsvars' _cons
matrix colnames `vc'=`rhsvars' _cons
matrix rownames `df'=`rhsvars' _cons
matrix rownames `t'=`rhsvars' _cons
matrix rownames `p'=`rhsvars' _cons
}
	
	ereturn post `b' `vc', esample(`touse') depname(`lhsvar') dof($S_E_df) obs($S_E_nobs)
	
	testparm `rhsvars'
	}
	/* write header */
if "`logit'"==""{
local eststring OLS regression: standard errors 
}
else {
local eststring Logistic regression: standard errors
}
        #delimit ;
        di _n in gr
		
		"`eststring'" _col(55)
		
        "Number of obs  =" in yel %8.0f `S_E_nobs' _n
        in gr "adjusted by Bias Reduced Linearization"
		_col(55) in gr "F["%1.0f r(df) "," %1.0f r(df_r) "]      ="
        in yel %8.4f r(F) _n
		_col(55) in gr "Prob  >  F     ="
        in yel %8.4f r(p) _n
        _col(55) in gr "R-squared      ="
        in yel %8.4f `S_E_r2' _n
        _col(55) in gr "Adj R-squared  ="
        in yel %8.4f `S_E_ar2' _n
        
        _col(55) in gr "Root MSE       ="
        in yel %8.0g `S_E_rmse' _n `addline'  ;
        #delimit cr

        
	  ereturn display

	  ereturn local clustvar "`cluster'"
	  ereturn local depvar "`lhsvar'"
	  if "`logit'"==""{
ereturn local cmd "regress" 
ereturn local predict "regres_p"
}
else {
ereturn local cmd "logit"
ereturn local predict "logit_p"
}
	  ereturn matrix satt_df `df'
	  ereturn matrix satt_t `t'
	  ereturn matrix satt_p `p'	  
end

version 9.0
mata:
void calcbrl(real matrix x, string scalar _clustervar, string scalar _aweight, string scalar _pweight, string scalar _resid, string scalar _beta)
{
/*initialize the matrices to be used:*/
inter=0
xrest=0
resid=0
cluster=0
aweight=0
pweight=0
/*populate the matrices to be used from stata variables*/

  
   st_view(resid,.,_resid)
   st_view(cluster,.,_clustervar)
   st_view(aweight,.,_aweight)
   st_view(pweight,.,_pweight)



/* Algorithm
   1) V = inv(diag(aw)) -- the inverse of the aweights 
   2) W_5 = diag(pw##0.5) -- a diagonal matrix of the square root of pweights
   3) Create omega = sum(xi' wi^1/2 inv(vi) wi^1/2 xi)^{-1}
   4) Loop over i
      5) Loop over j add to qi qij = xi omega xj' wj^1/2 inv(vj) wj^1/2 
      6) qi = i(mi) - qi
      7) Ai = root(vi) * symroot(root(vi) * qi * root(vi)) * root(vi)
      8) adjust the residual and add to the sum
*/

   /*Get coefficient estimates from estimation (in row vector)*/
   beta = st_matrix(_beta)
  

   beta = beta'

   _p = rows(beta)

   clusts = uniqrows(cluster)
   n = rows(clusts)  
   nobs = rows(x)

   w_5 = pweight:^0.5

/* Create omega */
   omega = J( _p, _p,0);
	info = panelsetup(cluster,1)
   for (j = 1;j<=n;j++){
	xj=0
      panelsubview(xj,x,j,info)
	awj=0
  	panelsubview(awj,aweight,j,info)
	w_5j=0
	panelsubview(w_5j,w_5,j,info)
	newterm=J(_p,_p,0)
	for (z=1;z<=rows(xj);z++){
	 newterm=newterm+xj[z,]'*xj[z,]*awj[z]*w_5j[z]
	}
      omega = omega + newterm
    }
   omega = luinv(omega)
gamma=J(cols(x),nobs,0)

/* Create gamma */
	for (z=1;z<=nobs;z++){
		gamma[,z]=x[z,]'w_5[z]^2*aweight[z]
	}

/*initialize these matrices*/
   xrrx =  J( _p, _p,0)
   xrrx2 =  xrrx
gammap1=0
panelsubview(gammap1,gamma',1,info)
gamma1=gammap1'

   for (i=1;i<=n;i++){
   xi=0
      panelsubview(xi,x,i,info)
	ri=0
      panelsubview(ri,resid,i,info)
	awi=0
	panelsubview(awi,aweight,i,info)

      vi_5 = diag(awi:^-.5)
	
      invvi = diag(awi)
	w_5i=0
	panelsubview(w_5i,w_5,i,info)
      wi_5 =  diag(w_5i)
      mi = rows(xi)
      if (i == 1) {
         phii = vi_5 - xi * omega * gamma1 * vi_5;
	}
	else {
		aw1=0
		panelsubview(aw1,aweight,1,info)
      	phii = - xi*omega*gamma1*diag(aw1:^-0.5)
	}
      for(ii=2;ii<=n;ii++){
	  		awii=0
		panelsubview(awii,aweight,ii,info)
		gammapii=0	
		panelsubview(gammapii,gamma',ii,info)
		gammaii=gammapii'
         	vj_5 = diag(awii:^-0.5);
         	if (ii==i) { 
            	phiij = vj_5 - xi * omega * gammaii* vj_5
		}
         else phiij = -xi*omega*gammaii* vj_5
         phii = phii,phiij
      }
      qi = phii * phii' 
	  
      ai = vi_5 * isymroot(vi_5 * qi * vi_5) * vi_5
	  ui = omega * xi' * wi_5 * invvi * wi_5 * ai * phii
      if (i==1) u = ui
      else u = u\ui

      for (k=1;k<=i;k++){
         ind = ((k-1) * _p + 1)::(k * _p)
         gik = ui * u[ind,]'
         if (i==1&k==1) g = gik
         else g = g\gik
      }

   /*Standard Huber Adjustments */
      tmp = xi' * wi_5 * invvi * wi_5 * ri 
      xrrx = xrrx + tmp*tmp' 

   /* BRL Adjustment */
   
      tmp2 = xi' * wi_5 * invvi * wi_5 * ai * ri 
	
      xrrx2 = xrrx2 + tmp2 * tmp2' 
   }
	
   /*mata drop u*/
   
   _df = J(_p,1,0)
   for (pp=1;pp<=_p;pp++){
      l = I(_p)[,pp]
      _df[pp] = satt(l,g,_p,n)
   }

   _tinv = invttail(_df,1-0.975)

/* Standard Huber/GEE sandwich variance-covariance matrix */
   vc_hub = (n/(n-1)) * omega * xrrx * omega 
   var_hub = diagonal(vc_hub) 
   se_hub = sqrt(var_hub)  
   t_hub = beta :/ se_hub 
   p_hub = 2 * (ttail( _df,abs(t_hub)))

/* HC2 Adjusted sandwich variance-covariance matrix */


   vc_brl = omega * xrrx2 * omega 
   var_brl = diagonal(vc_brl) 
   se_brl = sqrt(var_brl)  
   t_brl = beta :/ se_brl  
   p_brl = 2 * ( ttail(_df,abs(t_brl)))
   
   table = beta,se_brl,t_brl,_df,p_brl 
   
   
   cname = (beta, se_brl, t_brl, _df, p_brl)
	

   _dfn=_df', nobs 

	/*printf("Coefficient estimate\tBRL std error\n")
	for (i=1;i<=_p;i++){
	printf("%10.0g\t\t%10.0g\n",beta[i],se_brl[i])
	}*/
	
	st_matrix("e(brlse)",Re(se_brl))
	st_matrix("e(brlvc)",Re(vc_brl))
	st_matrix("e(brlt)",Re(t_brl))
	st_matrix("e(brlp)",Re(p_brl))
	st_matrix("e(df)",Re(_df))
	
}
end 

  
  
	/*----------------------------------------------------*/
*! version 1.0.1  04jan2004
version 9.0

mata:

void eigensystem(numeric matrix A, V, lambda, |cond, real scalar nobalance)
{
	numeric matrix Acpy

	if (args()==3) cond = .

	if(isfleeting(A)) _eigensystem(A,      V, lambda, cond, nobalance)
	else 		  _eigensystem(Acpy=A, V, lambda, cond, nobalance)
}

end

/*------------------------------------------------------*/
*! version 1.0.1  04jan2005
version 9.0

mata:

void  _eigensystem(numeric matrix A, V, lambda, |cond, real scalar nobalance)
{
	if (args()==3) cond = .

	_eigen_work(1, A, V, lambda, cond, nobalance)
}

end
/*------------------------------------------------------------------*/
*! version 1.0.2  19jan2005
version 9.0

mata:

/* (input) todo
   todo == 0 implies eigenvalues only
   todo == 1 implies eigenvalues and right eigenvectors
   todo == 2 implies eigenvalues and left  eigenvectors

   (input) A 
   A is matrix to be decomposed, A is destroyed in process of making
   calculation

   (output) evals
   	evals is complex rowvector containing eigenvalues

   (output) evecs
   	if todo==1 or todo==2, evecs is complex matrix containing
	eigenvectors.

   (input/output) cond
   	on input cond is a real scalar:
		  cond==0 and cond==. imply do not compute condition number
		  of eigenvalues;
		  otherwise condition numbers of eigenvalues are computed and
		  are returned in real rowvector cond
   (input) nobalance
	nobalance==. | nobalance==0 means balance; else do not
*/ 

void  _eigen_work(real scalar todo, numeric matrix A, evecs, evals, 
                  real scalar cond, real scalar nobalance)
{
	real scalar    dima, docond, i
	real colvector p
	numeric matrix tosort
	
	dima   = cols(A)
	docond = (cond!=0 & cond<.)

	/* ------------------------------------------------------------ */
	if (_eigen_la(todo, A, evecs, evals, cond, nobalance)) {
		evals = J(dima,1,.)
		if (todo==1 | todo==2) {
			evecs = .		// clear memory
			evecs = J(dima,dima,.)
		}
		if (docond)  {
			cond = (todo==2 ? J(   1, dima, .) :
					  J(dima,    1, .) )
		}
		return 
	}
	if (dima==0) return
	/* ------------------------------------------------------------ */

	if (todo!=2) _transposeonly(evals)
/*	p = order(tosort = (evals, quadrant(evals)), (-1, -2 ))*/

	/*if (todo) {
		/*_collate(tosort, p)*/
		for (i=2; i<=dima; i++) {
			if (tosort[i-1,.]==tosort[i,.]) {
				/*p = order(
				(evals,quadrant(evals),Re(evecs),Im(evecs)), 
					-(1..(2+2*dima))
				)*/
				break
			}
		}
	}*/
	tosort = .

	/*_collate(evals,p)*/
	if (todo!=2) _transposeonly(evals)

	if (todo==1) 		evecs = evecs/*[.,p]*/
	else if (todo==2) 	evecs = evecs/*[p,.]*/
	/* ------------------------------------------------------------ */

	if (docond) {
		if (todo==2) {
			/*_collate(cond,p)*/
		}
		else {
			_transpose(cond)
			/*_collate(cond,p)*/
			_transpose(cond)
		}
	}	

}

end
/*----------------------------------------------------------------------------*/
*! version 1.0.2  19jan2005
version 9.0

mata:

/* 
syntax 1 returns eigenvalues only
	_symeigen_work(numeric matrix A, lambda)

syntax 2 returns eigenvalues and eigenvectors
	_symeigen_work(numeric matrix A, V, lambda)

A is matrix to be decomposed, A is destroyed in process of making
calculation

*/ 

void  _symeigen_work(numeric matrix A, arg1, | arg2)
{
	real scalar    		i, rc, dima, todo
	real rowvector 		p
	pointer(numeric matrix) V
	pointer(real rowvector) lambda
	
	dima= cols(A)

/* if args() ==2 arg1 is lambda and arg2 is not used
   if args() !=2 arg1 is V and arg2 is lambda 
*/   

	/* ------------------------------------------------------------ */

	if (args()==2){
		todo=0
		rc = _symeigen_la(0, A, arg2, arg1)
		lambda = &arg1
	}	
	else {
		todo=1
		rc = _symeigen_la(1, A, arg1, arg2)
		V      = &arg1
		lambda = &arg2
	}	

	if (rc) {
		(*lambda) = J(1, dima, .)
		if (todo==1) {
			(*V) = .
			(*V) = J(dima,dima,.)
		}
		return 
	}
	if (dima==0) return
	/* ------------------------------------------------------------ */

	// _symeigen_la() returns eigenvalues sorted in ascending order

	if (todo==0) {
		(*lambda) = (*lambda)[dima..1]
		return 
	}

	for (i=2; i<=dima; i++) {
		if ((*lambda)[i-1]==(*lambda)[i]) {
			_transposeonly((*lambda))
			/*p = order((*lambda, Re(*V), Im(*V)), -(1..(1+2*dima)))
			_collate(*lambda, p)*/
			_transposeonly(*lambda)
			/**V = (*V)[.,p]*/
			return
		}
	}

	/*(*lambda) = (*lambda)[p=dima::1]*/
	_transposeonly(*V)
	/*_collate(*V, p)*/
	_transposeonly(*V)
}

end
/*-----------------------------------------------------------------------*/
mata:
function isymroot(a)
{
_evec=J(rows(a),cols(a),0)
_eval=J(1,cols(a),0)
eigensystem(a,_evec,_eval)
 _tmp = _evec*diag(_eval:^(-0.5))*_evec'
 return(_tmp)
}

function symroot(a)
{
   svd(a,_evec, _eval, _v)
   _tmp = _evec * diag(_eval:^(0.5))*_evec'
   return(_tmp)
}

function satt(l,g,_p,n)
{
g=Re(g)
gg = J(n,n,0)
for (jj=1; jj<=n; jj++){
   for (kk = 1; kk<=jj;kk++){
      _ind = (jj*(jj-1)*_p/2 +(kk-1)*_p + 1)..(jj*(jj-1)*_p/2 + kk*_p)
      _tmp = l'*g[_ind,]*l
      gg[jj,kk] = _tmp
      gg[kk,jj] = _tmp
      }
	}
	
_eval = eigenvalues(gg)
_eval = _eval'
_tmp = colsum(_eval)
_tmp2 = _eval'*_eval
_tmp3 = _tmp:^2/_tmp2

return(Re(_tmp3))
}
end
