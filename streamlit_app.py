import streamlit as st
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="BidWise AI", page_icon="🚗", layout="wide")

st.markdown("""
<style>
.big-card{border:1px solid #e5e7eb;border-radius:18px;padding:18px;background:#ffffff;box-shadow:0 1px 8px rgba(0,0,0,.06);}
.result-card{border:2px solid #f4c542;border-radius:20px;padding:22px;background:#fffdf3;}
.metric-box{border:1px solid #e5e7eb;border-radius:14px;padding:16px;background:white;min-height:110px;}
.small-label{font-size:14px;color:#666;margin-bottom:6px;}
.big-number{font-size:30px;font-weight:800;color:#111;}
.gold{color:#a16207;font-weight:800;}
.good{color:#15803d;font-weight:800;}
.bad{color:#b91c1c;font-weight:800;}
.warn{color:#a16207;font-weight:800;}
</style>
""", unsafe_allow_html=True)


def money(x):
    return f"£{x:,.0f}"


def copart_fee(bid):
    # Simple UK estimate. User can override by adding manual fee adjustment.
    if bid <= 49: return 1
    if bid <= 99: return 25
    if bid <= 199: return 45
    if bid <= 299: return 60
    if bid <= 399: return 75
    if bid <= 499: return 90
    if bid <= 599: return 105
    if bid <= 699: return 120
    if bid <= 799: return 135
    if bid <= 899: return 150
    if bid <= 999: return 165
    if bid <= 1199: return 185
    if bid <= 1399: return 205
    if bid <= 1599: return 225
    if bid <= 1799: return 245
    if bid <= 1999: return 265
    if bid <= 2399: return 300
    if bid <= 2999: return 350
    if bid <= 3499: return 400
    if bid <= 3999: return 450
    if bid <= 4499: return 500
    if bid <= 4999: return 550
    return bid * 0.11


def parse_title_from_url(url):
    try:
        path = urlparse(url).path
        slug = path.strip('/').split('/')[-1]
        slug = slug.replace('-', ' ')
        return slug.title()
    except Exception:
        return ""


def create_pdf(data):
    if not REPORTLAB_OK:
        return None
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("BidWise AI - Vehicle Bid Report", styles['Title']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 14))
    story.append(Paragraph(f"<b>Vehicle:</b> {data['vehicle']}", styles['Normal']))
    story.append(Paragraph(f"<b>Copart URL:</b> {data['url']}", styles['Normal']))
    story.append(Spacer(1, 14))

    rows = [
        ["Decision", data['decision']],
        ["Recommended Max Bid", money(data['max_bid'])],
        ["Estimated Landed Cost", money(data['landed'])],
        ["Repair Range", f"{money(data['repair_low'])} - {money(data['repair_high'])}"],
        ["Resale Range", f"{money(data['resale_low'])} - {money(data['resale_high'])}"],
        ["Estimated Profit", f"{money(data['profit_low'])} - {money(data['profit_high'])}"],
        ["Gross Margin", f"{data['margin_low']:.1f}% - {data['margin_high']:.1f}%"],
        ["Confidence", f"{data['confidence']}%"],
    ]
    table = Table(rows, colWidths=[180, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fff3cd')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph("Why this recommendation", styles['Heading2']))
    story.append(Paragraph(data['why'], styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer


st.title("🚗 BidWise AI - Copart Bid Calculator")
st.caption("Paste a Copart link, enter the missing numbers, and get a bid decision like SalvageIQ.")

with st.sidebar:
    st.header("Settings")
    target_profit = st.number_input("Target profit (£)", 0, 10000, 1000, 50)
    confidence_base = st.slider("Your confidence in inputs", 40, 100, 85)
    st.info("Version 1 uses manual inputs. Automatic Copart pulling can be added later where allowed.")

url = st.text_input("Paste Copart vehicle URL", placeholder="https://www.copart.co.uk/lot/...")
vehicle_guess = parse_title_from_url(url) if url else ""

colA, colB = st.columns([1,1])
with colA:
    st.subheader("Vehicle details")
    vehicle = st.text_input("Vehicle title", value=vehicle_guess)
    mileage = st.number_input("Mileage", 0, 300000, 80836, 100)
    category = st.selectbox("Category", ["Cat N", "Cat S", "Clean Title", "Unrecorded", "Unknown"])
    primary_damage = st.selectbox("Primary damage", ["Side", "Front End", "Rear End", "Minor Dents/Scratches", "Mechanical", "Undercarriage", "Vandalism", "Normal Wear", "Unknown"])
    engine_starts = st.selectbox("Engine status", ["Starts", "Run and Drive", "Stationary", "Unknown"])
    keys = st.selectbox("Keys", ["Yes", "No", "Unknown"])

with colB:
    st.subheader("Photos / notes")
    photos = st.file_uploader("Upload damage photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    notes = st.text_area("Repair notes", placeholder="Example: passenger side doors damaged, wing mirror, paintwork...")
    if photos:
        cols = st.columns(3)
        for i, p in enumerate(photos[:6]):
            cols[i % 3].image(p, use_container_width=True)

st.divider()
st.subheader("Money inputs")

c1, c2, c3, c4 = st.columns(4)
with c1:
    current_bid = st.number_input("Your bid / current bid (£)", 0, 100000, 1300, 50)
    manual_fee_extra = st.number_input("Other auction fees (£)", 0, 10000, 99, 10)
with c2:
    transport = st.number_input("Transport (£)", 0, 5000, 250, 10)
    valet_mot = st.number_input("MOT/valet/misc (£)", 0, 5000, 150, 10)
with c3:
    repair_low = st.number_input("Repair low (£)", 0, 50000, 700, 50)
    repair_high = st.number_input("Repair high (£)", 0, 50000, 1200, 50)
with c4:
    resale_low = st.number_input("Resale low (£)", 0, 200000, 7000, 100)
    resale_high = st.number_input("Resale high (£)", 0, 200000, 7800, 100)

fee = copart_fee(current_bid) + manual_fee_extra
avg_repair = (repair_low + repair_high) / 2
avg_resale = (resale_low + resale_high) / 2
landed = current_bid + fee + transport + valet_mot + avg_repair
profit_low = resale_low - (current_bid + fee + transport + valet_mot + repair_high)
profit_high = resale_high - (current_bid + fee + transport + valet_mot + repair_low)
margin_low = (profit_low / resale_low * 100) if resale_low else 0
margin_high = (profit_high / resale_high * 100) if resale_high else 0
max_bid = avg_resale - fee - transport - valet_mot - avg_repair - target_profit

risk_penalty = 0
if category == "Cat S": risk_penalty += 15
if engine_starts in ["Stationary", "Unknown"]: risk_penalty += 10
if keys != "Yes": risk_penalty += 5
if primary_damage in ["Front End", "Undercarriage", "Mechanical"]: risk_penalty += 10
confidence = max(35, min(100, confidence_base - risk_penalty))

if profit_low >= target_profit:
    decision = "BUY"
    badge = "🟢 BUY"
    status_class = "good"
elif profit_high >= 500:
    decision = "CAUTION"
    badge = "🟡 CAUTION"
    status_class = "warn"
else:
    decision = "AVOID"
    badge = "🔴 AVOID"
    status_class = "bad"

why = (
    f"Based on an average resale value of {money(avg_resale)}, estimated fees of {money(fee)}, "
    f"transport/misc costs of {money(transport + valet_mot)}, and repair range of {money(repair_low)} to {money(repair_high)}, "
    f"the estimated profit is {money(profit_low)} to {money(profit_high)}. "
    f"Target profit is {money(target_profit)}. Damage/category risk and input confidence give a confidence score of {confidence}%."
)

st.markdown('<div class="result-card">', unsafe_allow_html=True)
top1, top2 = st.columns([2,1])
with top1:
    st.markdown("### Bid Decision Summary")
with top2:
    st.markdown(f"### <span class='{status_class}'>{badge}</span>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Recommended Max Bid</div><div class='big-number'>{money(max_bid)}</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Estimated Landed Cost</div><div class='big-number'>{money(landed)}</div></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Estimated Profit</div><div class='big-number gold'>{money(profit_low)} to {money(profit_high)}</div><div>Target: {money(target_profit)}</div></div>", unsafe_allow_html=True)

m4, m5, m6 = st.columns(3)
with m4:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Repair Range</div><div class='big-number'>{money(repair_low)} - {money(repair_high)}</div></div>", unsafe_allow_html=True)
with m5:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Resale Private</div><div class='big-number'>{money(resale_low)} - {money(resale_high)}</div></div>", unsafe_allow_html=True)
with m6:
    st.markdown(f"<div class='metric-box'><div class='small-label'>Gross Margin</div><div class='big-number'>{margin_low:.0f}% to {margin_high:.0f}%</div></div>", unsafe_allow_html=True)

st.write("Confidence Score")
st.progress(confidence / 100)
st.write(f"**{confidence}%**")
st.markdown("#### Why this recommendation")
st.write(why)
st.markdown('</div>', unsafe_allow_html=True)

pdf_data = {
    'vehicle': vehicle or 'Unknown vehicle', 'url': url or 'No URL provided', 'decision': decision,
    'max_bid': max_bid, 'landed': landed, 'repair_low': repair_low, 'repair_high': repair_high,
    'resale_low': resale_low, 'resale_high': resale_high, 'profit_low': profit_low, 'profit_high': profit_high,
    'margin_low': margin_low, 'margin_high': margin_high, 'confidence': confidence, 'why': why
}
pdf = create_pdf(pdf_data)
if pdf:
    st.download_button("📄 Export PDF report", data=pdf, file_name="bidwise_report.pdf", mime="application/pdf")
else:
    st.warning("PDF export needs reportlab installed. Add reportlab to requirements.txt.")

st.caption("Note: This is an estimate only. Always inspect vehicle history, hidden structural/mechanical damage, fees, VAT and transport before bidding.")
