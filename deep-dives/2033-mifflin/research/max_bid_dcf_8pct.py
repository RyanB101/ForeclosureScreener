# Discounted cash-flow max bid for 2033 Mifflin St, occupied (8%/yr cost of capital)
import csv, math, sys
r=0.08; mr=(1+r)**(1/12)-1
def df(m): return 1/(1+mr)**m
ARV_COST=0.05+0.02289+0.01+0.01            # broker, seller RTT, closing, concessions
TAX=208400*0.013998/12; INS=175; UPK=150; UTIL=100
SELL_MO=3; TITLE=2000; LIENS=2500
# 1,512 sf x model $/sf x 1.2 contingency + $10k allowance + $15k bay/porch/cornice (L&I notice 10/22/2026); months
SCOPES={"Light":(79400,2),"Medium":(124800,3),"Heavy":(179200,5),"Gut":(251800,7)}
def run(arv,deed,poss_mo,poss_cost,target,scope="Medium"):
    rehab,rmo=SCOPES[scope]
    p=deed+poss_mo; sale=p+rmo+SELL_MO
    pv=0; nom=0
    def add(m,amt):
        nonlocal pv,nom; pv+=amt*df(m); nom+=amt
    add(0,-70); add(deed/2,-2500)                 # fees, legal to compel deed
    add(deed,-TITLE); add(deed,-LIENS)
    add(deed+poss_mo/2,-poss_cost)
    for m in range(math.ceil(sale)):
        add(m+0.5,-(TAX+(INS+UPK if m>=deed else 0)+(UTIL if m>=p else 0)))
    for k in range(rmo): add(p+k+0.5,-rehab/rmo)
    add(sale, arv*(1-ARV_COST))
    k_pv=0.115*df(0)+0.90*df(0.5); k_nom=1.015      # 10%+1.5% premium day 1, 90% at day 15
    mb=(pv-target)/k_pv
    return dict(sale_month=sale,max_bid=mb,profit_nominal=nom-mb*k_nom)
def profit_at(bid,arv,deed,poss_mo,poss_cost,scope="Medium"):
    x=run(arv,deed,poss_mo,poss_cost,0,scope)       # breakeven bid at NPV 0
    k_pv=0.115+0.90*df(0.5)
    npv=(x['max_bid']-bid)*k_pv
    nom=x['profit_nominal']+(x['max_bid']-bid)*1.015
    return npv,nom
TIMES=[("Fast: deed 9 mo, keys 2 mo, $7.5k",9,2,7500),
       ("Base: deed 12 mo, cash for keys/ejectment 8.5 mo, $10k",12,8.5,10000),
       ("Slow: deed 15 mo, contested ejectment 11 mo, $15k",15,11,15000)]
ARVS=[345000,360000,375000,390000,410000]
if __name__=="__main__":
    w=csv.writer(sys.stdout)
    w.writerow(["timeline","scope","arv","sale_month","max_bid_npv50k","nominal_profit_at_max","breakeven_bid_npv0"])
    for n,d,pm,pc in TIMES:
        for s in SCOPES:
            for a in ARVS:
                x=run(a,d,pm,pc,50000,s); b=run(a,d,pm,pc,0,s)
                w.writerow([n,s,a,x['sale_month'],round(x['max_bid'],-2),round(x['profit_nominal'],-2),round(b['max_bid'],-2)])
