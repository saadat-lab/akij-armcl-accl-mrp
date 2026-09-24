"""
ARMCL/ACCL — 18-Month MRP Live Dashboard
Replicates AAFL pattern for ARMCL (175) + ACCL (4)
Source: REV PDF matrix 12M + 6M forecast (linear trend blended, ±15% cap)
Run: streamlit run armcl_accl_mrp_dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ---- Config ----
DB = {
    "server": "203.202.241.211",
    "port": 1433,
    "database": "DWH",
    "user": "mcp_user",
    "password": "iAOS@35o997",
}
BU_MAP = {"ARMCL": 175, "ACCL": 4}
MONTHS = ["Jul-26","Aug-26","Sep-26","Oct-26","Nov-26","Dec-26","Jan-27","Feb-27","Mar-27","Apr-27","May-27","Jun-27","Jul-27","Aug-27","Sep-27","Oct-27","Nov-27","Dec-27"]
GEO = {
    "Cement Clinker": ("high","Import","CLINKER","China curbs, Red Sea freight — Clinker FOB +8% YoY, advise LOCK long"),
    "Blast Furnace Slag": ("high","Import","SLAG","India steel output volatile, slag scarcity — cover long"),
    "Lime Stone 3/4": ("moderate","Import","LIMESTONE","Vietnam supply stable, BDT weakness risk — blanket part"),
    "Gypsum": ("moderate","Import","GYPSUM","Oman/UAE gypsum steady — opportunistic dip buying"),
    "Grinding Aid": ("moderate","Import","CHEM","Specialty chem, FX exposed — blanket part"),
    "Limestone (5-10)": ("low","Local","STONE","Sylhet quarry local — spot, short cover"),
    "Limestone (10-20)": ("low","Local","STONE","Sylhet quarry local — spot, short cover, monsoon risk Q3"),
    "Gabbro/Pakur 10-20 mm": ("low","Local","STONE","Pakur/India border local stone — spot"),
    "Gabbro/Pakur 5-10 mm": ("low","Local","STONE","Pakur local — spot"),
    "Coarse Sand FM 2.2-3.0": ("low","Local","SAND","Local sand — spot, monsoon dredging risk Jul-Sep"),
    "Cement OPC": ("low","Local","CEMENT","Local cement — spot"),
    "Cement PCC": ("low","Local","CEMENT","Local cement — spot"),
    "Admixture": ("low","Local","ADMIX","Local admixture — spot"),
    "Bitumen 60/70": ("high","Import","BITUMEN","Brent-linked, Middle East — BLANKET long, urgent <1mo"),
}

# ---- Static RM_DATA built from PDF matrix + forecast ----
# Qty in MT except Sand in CFT? Keep as MT/CFT mix as per source; value in BDT
RM_DATA = [
    {"name":"Cement Clinker","code":"1111209","abc":"A","source":"Import","risk":"high","stock_mt":73500,"cover":0.82,"req18":1657498,"net_order":1583998,"budget_rate":8343,"latest_rate":8253,"budget_var_pct":-1.08,"price_trend":"STABLE","decision":"BLANKET-URGENT","monthly":[84216,96360,92928,93984,78144,97152,97152,88704,98335,94512,98208,88440,90571,90967,91363,91758,92154,92550],"price_series":[["2025-10",8200,85000],["2025-11",8343,84216],["2025-12",8343,96360],["2026-01",8042,93984],["2026-03",8101,97152],["2026-06",8253,88440]],"signal":"Import HIGH risk — global clinker tight on China decarbonization + Red Sea freight up. Landed rate stable but advise COVER LONG via 6M blanket."},
    {"name":"Blast Furnace Slag","code":"1111213","abc":"A","source":"Import","risk":"high","stock_mt":42000,"cover":0.88,"req18":897812,"net_order":855812,"budget_rate":3858,"latest_rate":3744,"budget_var_pct":-2.95,"price_trend":"FALLING","decision":"BLANKET-URGENT","monthly":[45617,52195,50336,50908,42328,52624,52624,48048,53265,51194,53196,47905,49059,49274,49488,49703,49917,50131],"price_series":[["2025-11",3858,45617],["2026-01",3582,50908],["2026-03",3465,52624],["2026-06",3744,47905]],"signal":"High-risk import tied to steel cycle. Price dipped but India export curbs possible — lock part of next 6M."},
    {"name":"Lime Stone 3/4","code":"1111212","abc":"A","source":"Import","risk":"moderate","stock_mt":52000,"cover":1.42,"req18":725159,"net_order":673159,"budget_rate":4842,"latest_rate":4332,"budget_var_pct":-10.53,"price_trend":"FALLING","decision":"BLANKET(part)","monthly":[36845,42158,40656,41118,34188,42504,42504,38808,43021,41349,42966,38693,39625,39798,39972,40145,40318,40491],"price_series":[["2025-11",4842,36845],["2026-01",4544,41118],["2026-03",4479,42504],["2026-06",4332,38693]],"signal":"Imported limestone softening. Moderate risk — take BLANKET(part) 50% on dip, spot top-up."},
    {"name":"Limestone (10-20)","code":"ARM-LIM-10-20","abc":"A","source":"Local","risk":"low","stock_mt":15000,"cover":0.61,"req18":498579,"net_order":483579,"budget_rate":5400,"latest_rate":5300,"budget_var_pct":-1.85,"price_trend":"STABLE","decision":"SPOT-URGENT","monthly":[23450,24443,24443,25437,26431,28338,36466,38533,22555,42627,25536,23549,25999,26051,26103,26154,26206,26258],"price_series":[["2025-11",5400,23450],["2026-03",5100,28338],["2026-06",5300,23549]],"signal":"Local Sylhet stone — low risk. BUT cover <1mo → SPOT-URGENT immediate buy. Monsoon may disrupt Jul-Sep supply."},
    {"name":"Cement PCC","code":"ARM-CEM-PCC","abc":"A","source":"Local","risk":"low","stock_mt":28000,"cover":1.91,"req18":288281,"net_order":260281,"budget_rate":8300,"latest_rate":8300,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[13559,14133,14133,14708,15282,16386,21085,22280,13042,24647,14765,13616,15033,15063,15093,15122,15152,15182],"price_series":[["2025-11",8300,13559],["2026-03",8200,16386],["2026-06",8300,13616]],"signal":"Domestic cement — stable. Keep SPOT short cover 30-45 days."},
    {"name":"Gabbro/Pakur 10-20 mm","code":"ARM-GAB-10-20","abc":"A","source":"Local","risk":"low","stock_mt":22000,"cover":1.82,"req18":233918,"net_order":211918,"budget_rate":5500,"latest_rate":5500,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[11162,11635,11635,12110,12579,13477,17101,18083,10566,20022,12003,10941,12096,12098,12100,12102,12103,12105],"price_series":[["2025-11",5500,11162],["2026-03",5500,13477],["2026-06",5500,10941]],"signal":"Local Pakur stone — spot, ample supply."},
    {"name":"Coarse Sand FM 2.2-3.0","code":"ARM-SAND","abc":"A","source":"Local","risk":"low","stock_mt":450000,"cover":0.52,"req18":16896712,"net_order":16446712,"budget_rate":69,"latest_rate":72,"budget_var_pct":4.35,"price_trend":"RISING","decision":"SPOT-URGENT","monthly":[794701,828375,828375,862049,895722,960376,1235827,1305869,764395,1444605,865416,798068,881109,882861,884613,886365,888117,889869],"price_series":[["2025-11",69,794701],["2026-03",70,960376],["2026-06",72,798068]],"signal":"Local sand — low geo risk but seasonal dredging ban + high volume. Cover 0.5mo → SPOT-URGENT buy now, keep short (monsoon upside)."},
    {"name":"Bitumen 60/70","code":"ABSL-BIT","abc":"A","source":"Import","risk":"high","stock_mt":180,"cover":0.42,"req18":9791,"net_order":9611,"budget_rate":105000,"latest_rate":98000,"budget_var_pct":-6.67,"price_trend":"FALLING","decision":"BLANKET-URGENT","monthly":[420,510,540,630,690,750,750,750,480,750,480,450,479,460,441,422,404,385],"price_series":[["2025-11",105000,420],["2026-01",102000,630],["2026-03",100000,750],["2026-06",98000,450]],"signal":"Bitumen HIGH import, Brent-linked. Price down but Brent volatility + road season Q4 → BLANKET long despite fall; urgent <1mo."},
    # B items
    {"name":"Limestone (5-10)","code":"ARM-LIM-5-10","abc":"B","source":"Local","risk":"low","stock_mt":7500,"cover":1.10,"req18":128941,"net_order":121441,"budget_rate":4841,"latest_rate":4465,"budget_var_pct":-7.77,"price_trend":"FALLING","decision":"SPOT","monthly":[6065,6322,6322,6579,6835,7329,9431,9965,5833,11024,6604,6090,6724,6737,6750,6764,6777,6790],"price_series":[["2025-11",4841,6065],["2026-03",4465,9431],["2026-06",4465,6090]],"signal":"Local — spot short cover."},
    {"name":"Gabbro/Pakur 5-10 mm","code":"ARM-GAB-5-10","abc":"B","source":"Local","risk":"low","stock_mt":6800,"cover":1.04,"req18":132412,"net_order":125612,"budget_rate":4841,"latest_rate":4465,"budget_var_pct":-7.77,"price_trend":"FALLING","decision":"SPOT","monthly":[6282,6548,6548,6815,7079,7587,9682,10235,5985,11328,6789,6218,6871,6877,6883,6889,6895,6901],"price_series":[["2025-11",4841,6282],["2026-03",4465,9682],["2026-06",4465,6218]],"signal":"Local — spot."},
    {"name":"Gypsum","code":"1111211","abc":"B","source":"Import","risk":"moderate","stock_mt":10500,"cover":1.22,"req18":171621,"net_order":161121,"budget_rate":5112,"latest_rate":4253,"budget_var_pct":-16.8,"price_trend":"FALLING","decision":"BLANKET(part)","monthly":[8720,9977,9622,9731,8091,10059,10059,9185,10182,9786,10169,9157,9378,9419,9460,9501,9542,9583],"price_series":[["2025-11",5112,8720],["2026-01",4771,9731],["2026-06",4253,9157]],"signal":"Moderate import — price down 16%, take part blanket on dip."},
    {"name":"Admixture","code":"ARM-ADM","abc":"B","source":"Local","risk":"low","stock_mt":800000,"cover":3.20,"req18":4920655,"net_order":4120655,"budget_rate":100,"latest_rate":100,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[224000,231000,231000,237000,455000,257000,334000,348000,240000,376000,260000,247000,258472,253793,249115,244437,239758,235080],"price_series":[["2025-11",100,224000],["2026-03",100,334000],["2026-06",100,247000]],"signal":"Local — spot, high cover."},
    {"name":"Cement OPC","code":"ARM-CEM-OPC","abc":"B","source":"Local","risk":"low","stock_mt":5800,"cover":2.25,"req18":50876,"net_order":45076,"budget_rate":9000,"latest_rate":9000,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[2393,2494,2494,2596,2697,2892,3721,3932,2301,4350,2606,2403,2653,2658,2664,2669,2674,2679],"price_series":[["2025-11",9000,2393],["2026-03",9200,2892],["2026-06",9000,2403]],"signal":"Local cement — spot."},
    {"name":"Grinding Aid","code":"1111210","abc":"C","source":"Import","risk":"moderate","stock_mt":150,"cover":2.50,"req18":1079,"net_order":929,"budget_rate":140332,"latest_rate":138363,"budget_var_pct":-1.4,"price_trend":"STABLE","decision":"SPOT(verify)","monthly":[60,60,60,60,56,60,60,60,60,60,60,60,60,60,60,61,61,61],"price_series":[["2025-11",140332,60],["2026-03",146037,60],["2026-06",138363,60]],"signal":"Low volume specialty — spot verify."},
    {"name":"Empty Bag PCC (Stitch)","code":"1111217","abc":"C","source":"Local","risk":"low","stock_mt":3500000,"cover":2.10,"req18":30903803,"net_order":27403803,"budget_rate":30,"latest_rate":30,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[1593368,1593368,1679496,1679496,1754858,1862518,2024008,2002476,1701028,1830220,1539538,1668730,1693851,1681290,1668730,1656170,1643609,1631049],"price_series":[["2025-11",30,1593368],["2026-03",30,1862518],["2026-06",30,1668730]],"signal":"Packaging — spot."},
    {"name":"Empty Bag PCC CEM-II","code":"1111218","abc":"C","source":"Local","risk":"low","stock_mt":2800000,"cover":2.15,"req18":24227020,"net_order":21427020,"budget_rate":26,"latest_rate":26,"budget_var_pct":0.0,"price_trend":"STABLE","decision":"SPOT","monthly":[1249120,1249120,1316640,1316640,1375720,1460120,1586720,1569840,1333520,1434800,1206920,1308200,1327893,1318047,1308200,1298353,1288507,1278660],"price_series":[["2025-11",26,1249120],["2026-03",26,1460120],["2026-06",26,1308200]],"signal":"Packaging — spot."},
]

SKU_DATA = [
    {"code":"RMX-25MPa-3500","name":"25 MPa Concrete mix (3500)","vals":[126500,236000,246000,246000,285200,367000,387800,227000,429000,257000,237000,0,0,0,0,0,0,0]},
    {"code":"RMX-28MPa-4000","name":"28 MPa Concrete mix (4000)","vals":[126500,236000,246000,246000,285200,367000,387800,227000,429000,257000,237000,0,0,0,0,0,0,0]},
    {"code":"RMX-30MPa-4500","name":"30 MPa Concrete mix (4500)","vals":[126500,236000,246000,246000,285200,367000,387800,227000,429000,257000,237000,0,0,0,0,0,0,0]},
    {"code":"RMX-35MPa-5000","name":"35 MPa Concrete mix (5000)","vals":[94875,177000,184500,184500,213900,275250,290850,170250,321750,192750,177750,0,0,0,0,0,0,0]},
]

st.set_page_config(layout="wide", page_title="ARMCL/ACCL 18M MRP")
st.markdown("<h1 style='font-family:Cambria'>ARMCL/ACCL — 18-Month Material Requirement Plan</h1><div style='color:#5B6B73'>As of 2026-09-24 | DWH-live stock OFFLINE — static fallback | 12M budget + 6M forecast (trend blended ±15%)</div>", unsafe_allow_html=True)

# KPIs
total_req = sum(r["req18"] for r in RM_DATA)
classA = [r for r in RM_DATA if r["abc"]=="A"]
crit = [r for r in classA if r["cover"] < 1]
over_budget = [r for r in RM_DATA if r["budget_var_pct"] and r["budget_var_pct"]>10]

c1,c2,c3,c4 = st.columns(4)
c1.metric("18-mo RM Required", f"{total_req:,.0f} MT/CFT")
c2.metric("Class A Materials", len(classA))
c3.metric("Class A URGENT <1mo", len(crit), delta_color="inverse")
c4.metric("DWH Status", "🔴 OFFLINE", "static fallback")
if crit:
    st.error("⚠ Under 1mo cover: " + ", ".join(r["name"] for r in crit))
if over_budget:
    st.warning("Buying above budget: " + " · ".join(f"{r['name']} +{r['budget_var_pct']:.0f}%" for r in over_budget))

# Class A table
st.subheader("Class A RM — Coverage & Decision (Spot vs Blanket)")
df = pd.DataFrame([{
    "Material": r["name"],"Source": r["source"],"Risk": r["risk"],
    "Stock": f"{r['stock_mt']:,.0f}","Cover(d)": round(r["cover"]*30),"Cover(mo)": round(r["cover"],1),
    "18-Mo Req": f"{r['req18']:,.0f}","Net Order": f"{r['net_order']:,.0f}",
    "Budget": r["budget_rate"],"Latest": r["latest_rate"],"vs Budget": f"{r['budget_var_pct']:+.0f}%" if r["budget_var_pct"] else "—",
    "Trend": r["price_trend"],"DECISION": r["decision"]
} for r in classA])
st.dataframe(df, use_container_width=True, hide_index=True)

def decision_color(d):
    if "URGENT" in d: return "background-color:#FBEAE8;color:#B23A2F"
    if "BLANKET" in d: return "background-color:#DDE7F0;color:#2C5F8A"
    return "background-color:#E3F1EA;color:#2E7D5B"

# Item detail
st.subheader("Item Detail — Landed Rate vs Purchase Qty + Budget & Projection")
rm_names = [r["name"] for r in RM_DATA]
sel = st.selectbox("Select RM", rm_names, index=0)
r = next(x for x in RM_DATA if x["name"]==sel)
col1,col2 = st.columns(2)
with col1:
    fig = go.Figure()
    xs = [p[0] for p in r["price_series"]]; ys = [p[1] for p in r["price_series"]]
    fig.add_trace(go.Scatter(x=xs,y=ys,mode="lines+markers",name="Actual Landed Rate",line=dict(color="#24333B",width=2.5)))
    if r["budget_rate"]:
        fig.add_trace(go.Scatter(x=[xs[0], MONTHS[-1]],y=[r["budget_rate"],r["budget_rate"]],mode="lines",name=f"Budget {r['budget_rate']}",line=dict(dash="dot",color="#C97B2E")))
    # simple projection: last rate +/- trend
    last = ys[-1]
    proj = last * (1.08 if r["price_trend"]=="RISING" else 0.95 if r["price_trend"]=="FALLING" else 1.02)
    fig.add_trace(go.Scatter(x=[xs[-1],"Dec-27"],y=[last,proj],mode="lines",name="Projection",line=dict(dash="dash",color="#B23A2F")))
    fig.update_layout(height=320, title=f"{r['name']} | {r['risk']} | {r['decision']}", yaxis_title="BDT / MT", plot_bgcolor="#F7F7F5", paper_bgcolor="#F7F7F5", margin=dict(t=40,b=30))
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=MONTHS, y=r["monthly"], name="Monthly Req", marker_color=["#C97B2E"]*12 + ["#5B6B73"]*6))
    fig2.update_layout(height=320, title=f"Monthly Requirement — 12M budget (amber) + 6M forecast (grey)", plot_bgcolor="#F7F7F5", paper_bgcolor="#F7F7F5", margin=dict(t=40,b=60))
    st.plotly_chart(fig2, use_container_width=True)
st.info(f"**Signal:** {r['signal']} | Cover {r['cover']*30:.0f} days / {r['cover']:.1f} mo | Stock {r['stock_mt']:,.0f} → Net Order {r['net_order']:,.0f} | vs Budget {r['budget_var_pct']:+.1f}%")

# All RM matrix
st.subheader("All RM — Month-wise Requirement (18M)")
q = st.text_input("Search RM", "")
filtered = [r for r in RM_DATA if q.lower() in r["name"].lower()]
mat = pd.DataFrame({r["name"]: r["monthly"] for r in filtered}, index=MONTHS).T
mat["18-Mo"] = [r["req18"] for r in filtered]
mat["Cover(mo)"] = [r["cover"] for r in filtered]
mat["Decision"] = [r["decision"] for r in filtered]
st.dataframe(mat, use_container_width=True)

# Market intelligence
st.subheader("Market Intelligence — Geo & Price Outlook")
for name,(risk,src,_,note) in GEO.items():
    col = "#B23A2F" if risk=="high" else "#C97B2E" if risk=="moderate" else "#2E7D5B"
    st.markdown(f"<span style='color:{col};font-weight:bold'>{name} [{risk.upper()} {src}]</span> — {note}", unsafe_allow_html=True)
st.caption("Forecast 6M = linear trend on last 9M blended with 6M avg, capped ±15% (same as AAFL proj_price ±40% but tighter for cement). For live futures, connect yfinance tickers: Cement/Coal/Bitumen (Brent), Stone local index.")

with st.expander("Methodology"):
    st.write("""
- **SKU forecast:** REV 12M budget (17.2M CFT) + 6M forecast via trend blend. 
- **RM plan:** PDF matrix Qty × SKU mix already exploded; verified sum ~2,255 Cr 12M value.
- **ABC:** Cumulative 80% value → Class A (7 items: Clinker, Lime Stone 3/4, Slag, Limestone 10-20, PCC, Gabbro 10-20, Sand) + Bitumen strategic.
- **Cover:** Stock / avg monthly 18M; stock uses static fallback (DWH offline). Net Order = Req18 - Stock.
- **Decision:** Same AAFL matrix: <1mo → URGENT (Import BLANKET, Local SPOT); else HIGH Import→BLANKET, HIGH Local→SPOT-URGENT, MODERATE Import→BLANKET(part), LOW Local→SPOT.
- **Price projection:** Linear + blended, capped; replace with DWH weighted Σvalue/Σqty when online.
- **Refresh:** Re-run build with new REV PDF and paste RM_DATA.
    """)

if st.button("Export offline HTML"):
    st.info("Use the generated armcl_accl_mrp_dashboard.html file in project root (self-contained, Plotly CDN) for sharing.")
