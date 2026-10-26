# 8%/yr discounted cash-flow max bid for 1619 S 2nd St (3-unit row), occupied by default.
# Max bid = bid at which NPV at 8%/yr = $50k (ryan's flip profit target). Breakeven = NPV 0 (absolute ceiling).
import csv, math, sys
r=0.08; mr=(1+r)**(1/12)-1
df=lambda m: 1/(1+mr)**m
OPA=320900; TAX=OPA*0.013998/12; INS_UPK=325; UTIL=100
SELL=0.05+0.02289+0.01+0.01          # commission, half RTT, closing, concessions = 9.29%
TITLE=2000; LIENS=2500; DEED_LEGAL=2500; B4A=70
SCOPES=[  # name, rehab budget (model: $/sf x 1,560 x 1.2 + $10k + adders), rehab months, resale low/base/high
 ("Light: keep 3 units, refresh, sell to investor", 66160, 3, (430000,470000,510000)),
 ("Medium: de-convert to 1-family 3bd/2ba (base)", 127960, 3, (460000,500000,540000)),
 ("Heavy: 1-family, new systems + kitchen/baths", 184120, 5, (530000,575000,620000)),
 ("Gut: 1-family + roof deck", 274000, 7, (590000,640000,700000)),
]
TIMELINES=[("Fast: deed 9 mo, vacant or keys in 3 mo, $9k",9,3,9000),
           ("Base: deed 12 mo, cash for keys/ejectment 9 mo, $15k (3 units)",12,9,15000),
           ("Slow: deed 15 mo, contested/tenant removal 12 mo, $25k",15,12,25000)]
def run(arv,rehab,rmo,deed,pmo,pcost,target):
    p=deed+pmo; sale=p+rmo+3; pv=0; nom=0
    def add(m,a):
        nonlocal pv,nom; pv+=a*df(m); nom+=a
    add(0,-B4A); add(deed/2,-DEED_LEGAL); add(deed,-(TITLE+LIENS)); add(deed+pmo/2,-pcost)
    for m in range(math.ceil(sale)):
        add(m+0.5,-(TAX+(INS_UPK if m>=deed else 0)+(UTIL if m>=p else 0)))
    for k in range(rmo): add(p+k+0.5,-rehab/rmo)
    add(sale,arv*(1-SELL))
    k_pv=0.115*df(0)+0.90*df(0.5); k_nom=1.015
    mb=(pv-target)/k_pv
    return dict(sale_month=sale,max_bid=mb,profit_nominal=nom-mb*k_nom,cash_out_ex_bid=-(nom-arv*(1-SELL)))
rows=[]
for sname,reh,rmo,arvs in SCOPES:
    for lab,arv in zip(("low","base","high"),arvs):
        for tname,d,pm,pc in TIMELINES:
            a=run(arv,reh,rmo,d,pm,pc,50000); b=run(arv,reh,rmo,d,pm,pc,0)
            rows.append(dict(scope=sname,resale_case=lab,arv=arv,rehab=reh,timeline=tname,sale_month=a['sale_month'],
                max_bid_npv50k=round(a['max_bid'],-2),profit_before_8pct_at_max=round(a['profit_nominal'],-2),
                breakeven_bid_8pct=round(b['max_bid'],-2),all_in_at_max=round(a['max_bid']*1.015+a['cash_out_ex_bid'],-2)))
out=sys.argv[1] if len(sys.argv)>1 else None
w=csv.DictWriter(open(out,'w',newline='') if out else sys.stdout,fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
