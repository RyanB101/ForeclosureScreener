# 1234 E Columbia Ave: max bid by discounted cash flow at 8%/yr (same method as 2321 Madison Sq and bench-top5/scen.py).
# Max bid = bid where NPV of every cash flow at 8%/yr still leaves $50k. Ceiling (walk-away) = bid where NPV = 0.
import math, csv, itertools, sys
r=0.08; mr=(1+r)**(1/12)-1
df=lambda m:1/(1+mr)**m
OPA=560200; TAX=OPA*0.013998/12           # RE tax from sale date (homestead exemption ends with the owner)
INS_UPK=325; UTIL=100                     # insurance+upkeep from deed; utilities from possession
SELL=0.0929                               # commission 5%, half RTT 2.289%, closing 1%, concessions 1%
LEGAL=2500; TITLE=2000; CLAIMS=2500       # deed petition; title/recording; city claims reserve
SF=2556
SCOPE={'Light':40,'Medium':65,'Heavy':95}
def rehab(scope,adder=0): return round(SF*SCOPE[scope]*1.2+10000+adder,-3)
RMO={'Light':3,'Medium':4,'Heavy':5}
def dcf(arv,rh,rmo,deed,poss,pcost,target):
    p=deed+poss; sale=p+rmo+3
    pv=-70-LEGAL*df(deed/2)-(TITLE+CLAIMS)*df(deed)-pcost*df(deed+poss/2)
    for m in range(math.ceil(sale)):
        pv-= (TAX+(INS_UPK if m>=deed else 0)+(UTIL if m>=p else 0))*df(m+.5)
    for k in range(rmo): pv-= rh/rmo*df(p+k+.5)
    pv+= arv*(1-SELL)*df(sale)
    k=0.115+0.90*df(0.5)                  # 10%+1.5% premium Nov 4, 90% Nov 18
    return (pv-target)/k, sale
def nominal_profit(arv,rh,rmo,deed,poss,pcost,bid):
    p=deed+poss; sale=p+rmo+3
    cost=bid*1.015+70+LEGAL+TITLE+CLAIMS+pcost+rh+TAX*sale+INS_UPK*(sale-deed)+UTIL*(sale-p)
    return arv*(1-SELL)-cost, sale
OCC={'Owner leaves on cash for keys (3 mo, $10k)':(3,10000),
     'Occupied, ryan rule (8.5 mo, $12k)':(8.5,12000)}
if __name__=='__main__':
    w=csv.writer(sys.stdout)
    w.writerow(['occupancy','scope','rehab','arv','deed_mo','sale_month','max_bid_npv50k','ceiling_npv0','nominal_profit_at_400k','nominal_profit_at_max','all_in_at_max'])
    for (on,(pm,pc)),sc,arv,deed in itertools.product(OCC.items(),['Light','Medium','Heavy'],[750000,820000,900000],[12,15]):
        rh=rehab(sc); mb,s=dcf(arv,rh,RMO[sc],deed,pm,pc,50000); be,_=dcf(arv,rh,RMO[sc],deed,pm,pc,0)
        n4,_=nominal_profit(arv,rh,RMO[sc],deed,pm,pc,400000); nm,_=nominal_profit(arv,rh,RMO[sc],deed,pm,pc,mb)
        allin=arv*(1-SELL)-nm
        w.writerow([on,sc,rh,arv,deed,s,round(mb,-3),round(be,-3),round(n4,-3),round(nm,-3),round(allin,-3)])
