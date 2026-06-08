import streamlit as st
import requests
from us_counties import US_COUNTIES

SUPABASE_URL = "https://qducnczihagvarhpmvxj.supabase.co"
SUPABASE_KEY = "sb_publishable_2jTzuh0d7RQe_ahd8lf6Ow_5GaGAEtc"
PASS = "Blackmoat2026"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def sb_get(table, query=""):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}{query}", headers=HEADERS)
    return r.json()

def sb_post(table, data):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=data)
    return r.json()

def sb_patch(table, match, data):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?{match}", headers=HEADERS, json=data)
    return r

def sb_delete(table, match):
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}?{match}", headers=HEADERS)
    return r

st.set_page_config(page_title="Arxies Ops", page_icon="🚪", layout="wide")

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("### Arxies Operations")
        pw = st.text_input("Password", type="password")
        if st.button("Sign in", use_container_width=True):
            if pw == PASS:
                st.session_state.authed = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()

st.sidebar.markdown("## Arxies")
st.sidebar.markdown("Operations Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("", ["📋 Requests", "📤 Dispatches", "👥 Vendors", "📍 Markets"], label_visibility="collapsed")
st.sidebar.markdown("---")
if st.sidebar.button("Sign out"):
    st.session_state.authed = False
    st.rerun()

@st.cache_data(ttl=30)
def load_requests():
    return sb_get("requests", "?order=created_at.desc")

@st.cache_data(ttl=30)
def load_vendors():
    return sb_get("vendors", "?order=name.asc")

@st.cache_data(ttl=30)
def load_markets():
    return sb_get("markets", "?order=name.asc")

@st.cache_data(ttl=30)
def load_dispatches():
    return sb_get("dispatches", "?order=assigned_at.desc")

@st.cache_data(ttl=30)
def load_counties():
    return sb_get("counties", "?order=name.asc")

def clear_cache():
    load_requests.clear()
    load_vendors.clear()
    load_markets.clear()
    load_dispatches.clear()
    load_counties.clear()

requests_data = load_requests()
vendors_data = load_vendors()
markets_data = load_markets()
dispatches_data = load_dispatches()
counties_data = load_counties()

vendor_map = {v["id"]: v["name"] for v in vendors_data}
market_map = {m["id"]: m["name"] for m in markets_data}

STATUS_CYCLE = ["new", "review", "scheduled", "closed"]
STATUS_EMOJI = {"new": "🔵 New", "review": "🟡 In review", "scheduled": "🟢 Scheduled", "closed": "✓ Closed"}

if page == "📋 Requests":
    st.markdown("## Requests")
    col1, col2, col3, col4 = st.columns(4)
    counts = {"new":0,"review":0,"scheduled":0,"closed":0}
    for r in requests_data:
        counts[r.get("status","new")] = counts.get(r.get("status","new"),0) + 1
    col1.metric("Total", len(requests_data))
    col2.metric("New", counts["new"])
    col3.metric("In Review", counts["review"])
    col4.metric("Scheduled", counts["scheduled"])
    st.markdown("---")
    filter_col, refresh_col = st.columns([4,1])
    with filter_col:
        status_filter = st.selectbox("Filter", ["All", "🔵 New", "🟡 In review", "🟢 Scheduled", "✓ Closed"], label_visibility="collapsed")
    with refresh_col:
        if st.button("🔄 Refresh", use_container_width=True):
            clear_cache()
            st.rerun()
    filtered = requests_data
    if status_filter != "All":
        status_key = {"🔵 New":"new","🟡 In review":"review","🟢 Scheduled":"scheduled","✓ Closed":"closed"}[status_filter]
        filtered = [r for r in requests_data if r.get("status") == status_key]
    if not filtered:
        st.info("No requests found.")
    else:
        for r in filtered:
            dispatch = next((d for d in dispatches_data if d.get("request_id") == r["id"]), None)
            vendor_name = vendor_map.get(dispatch["vendor_id"], "—") if dispatch else "No vendor"
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                with c1:
                    st.markdown(f"**{r.get('contact','Unknown')}**")
                    st.caption(f"{r['id'][:8].upper()} · {r.get('created_at','')[:16].replace('T',' ')}")
                    st.markdown(f"📍 {r.get('address','—')}  \n🔧 {r.get('issue','—')}")
                    st.caption(f"{r.get('urgency','')} · {r.get('type','')} · 👤 {vendor_name}")
                with c2:
                    current_status = r.get("status", "new")
                    idx = STATUS_CYCLE.index(current_status) if current_status in STATUS_CYCLE else 0
                    next_status = STATUS_CYCLE[(idx+1) % len(STATUS_CYCLE)]
                    st.markdown(f"**{STATUS_EMOJI.get(current_status, current_status)}**")
                    if st.button(f"→ {STATUS_EMOJI[next_status]}", key=f"status_{r['id']}"):
                        sb_patch("requests", f"id=eq.{r['id']}", {"status": next_status})
                        clear_cache()
                        st.rerun()

elif page == "📤 Dispatches":
    st.markdown("## Dispatches")
    if st.button("🔄 Refresh"):
        clear_cache()
        st.rerun()
    if not dispatches_data:
        st.info("No dispatches yet.")
    else:
        rows = []
        for d in dispatches_data:
            req = next((r for r in requests_data if r["id"] == d.get("request_id")), None)
            rows.append({
                "ID": d["id"][:8].upper(),
                "Customer": req.get("contact","—") if req else "—",
                "Vendor": vendor_map.get(d.get("vendor_id"),"—"),
                "Market": market_map.get(d.get("market_id"),"—"),
                "Status": d.get("status","pending"),
                "Assigned": d.get("assigned_at","")[:16].replace("T"," ") if d.get("assigned_at") else "—"
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

elif page == "👥 Vendors":
    st.markdown("## Vendors")
    with st.expander("➕ Add / Edit vendor", expanded=False):
        edit_vendor = st.selectbox("Edit existing", ["— Add new —"] + [v["name"] for v in vendors_data])
        existing = next((v for v in vendors_data if v["name"] == edit_vendor), None) if edit_vendor != "— Add new —" else None
        v_name = st.text_input("Company name", value=existing["name"] if existing else "")
        v_contact = st.text_input("Contact name", value=existing.get("contact_name","") if existing else "")
        v_phone = st.text_input("Phone", value=existing.get("phone","") if existing else "")
        v_email = st.text_input("Email", value=existing.get("email","") if existing else "")
        market_names = ["— None —"] + [m["name"] for m in markets_data]
        current_market = market_map.get(existing.get("market_id")) if existing else None
        market_idx = market_names.index(current_market) if current_market in market_names else 0
        v_market = st.selectbox("Market", market_names, index=market_idx)
        v_notes = st.text_input("Notes", value=existing.get("notes","") if existing else "")
        market_id = next((m["id"] for m in markets_data if m["name"] == v_market), None)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save vendor", use_container_width=True):
                if v_name:
                    payload = {"name": v_name, "contact_name": v_contact or None, "phone": v_phone or None,
                               "email": v_email or None, "market_id": market_id, "notes": v_notes or None, "active": True}
                    if existing:
                        sb_patch("vendors", f"id=eq.{existing['id']}", payload)
                    else:
                        sb_post("vendors", payload)
                    clear_cache()
                    st.rerun()
        with col2:
            if existing and st.button("Toggle active/inactive", use_container_width=True):
                sb_patch("vendors", f"id=eq.{existing['id']}", {"active": not existing.get("active", True)})
                clear_cache()
                st.rerun()
    st.markdown("---")
    if not vendors_data:
        st.info("No vendors yet.")
    else:
        rows = [{"Name": v["name"], "Contact": v.get("contact_name","—"), "Phone": v.get("phone","—"),
                 "Email": v.get("email","—"), "Market": market_map.get(v.get("market_id"),"—"),
                 "Active": "✅" if v.get("active") else "❌"} for v in vendors_data]
        st.dataframe(rows, use_container_width=True, hide_index=True)

elif page == "📍 Markets":
    st.markdown("## Markets")
    with st.expander("➕ Add / Edit market", expanded=False):
        edit_market = st.selectbox("Edit existing", ["— Add new —"] + [m["name"] for m in markets_data])
        existing_market = next((m for m in markets_data if m["name"] == edit_market), None) if edit_market != "— Add new —" else None
        m_name = st.text_input("Market name", value=existing_market["name"] if existing_market else "")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save market", use_container_width=True):
                if m_name:
                    payload = {"name": m_name, "active": True}
                    if existing_market:
                        sb_patch("markets", f"id=eq.{existing_market['id']}", payload)
                    else:
                        sb_post("markets", payload)
                    clear_cache()
                    st.rerun()
        with col2:
            if existing_market and st.button("Toggle active/inactive", use_container_width=True):
                sb_patch("markets", f"id=eq.{existing_market['id']}", {"active": not existing_market.get("active", True)})
                clear_cache()
                st.rerun()
    st.markdown("---")
    if not markets_data:
        st.info("No markets yet — add one above.")
    else:
        for market in markets_data:
            with st.container(border=True):
                mc1, mc2 = st.columns([4,1])
                with mc1:
                    status_badge = "✅ Active" if market.get("active") else "❌ Inactive"
                    st.markdown(f"**{market['name']}** &nbsp; {status_badge}")
                with mc2:
                    vendor_count = len([v for v in vendors_data if v.get("market_id") == market["id"]])
                    st.caption(f"{vendor_count} vendor{'s' if vendor_count != 1 else ''}")

                market_counties = [c for c in counties_data if c.get("market_id") == market["id"]]
                tab_list, tab_add = st.tabs(["📋 Counties", "➕ Add county"])

                with tab_list:
                    if not market_counties:
                        st.caption("No counties assigned yet.")
                    else:
                        for county in market_counties:
                            cc1, cc2 = st.columns([4,1])
                            with cc1:
                                st.markdown(f"{county['name']}, {county.get('state','')}")
                            with cc2:
                                if st.button("Remove", key=f"del_{county['id']}"):
                                    sb_delete("counties", f"id=eq.{county['id']}")
                                    clear_cache()
                                    st.rerun()

                with tab_add:
                    already_assigned = [f"{c['name']}, {c.get('state','')}" for c in market_counties]
                    available = [c for c in US_COUNTIES if c not in already_assigned]
                    selected_county = st.selectbox(
                        "Search and select a county",
                        ["— Select —"] + available,
                        key=f"county_select_{market['id']}"
                    )
                    if st.button("Add county", key=f"add_{market['id']}"):
                        if selected_county and selected_county != "— Select —":
                            parts = selected_county.split(", ")
                            county_name = parts[0]
                            county_state = parts[1] if len(parts) > 1 else None
                            sb_post("counties", {
                                "name": county_name,
                                "state": county_state,
                                "market_id": market["id"]
                            })
                            clear_cache()
                            st.rerun()
