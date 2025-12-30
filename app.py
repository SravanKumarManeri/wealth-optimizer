import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Delta-Wealth | Strategic Optimizer", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    .stMetric { background-color: white; border: 1px solid #e1e4e8; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'debts' not in st.session_state:
    st.session_state.debts = []

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🛡️ Delta-Wealth")
    st.caption("v1.6 Final Production Build")
    st.divider()
    
    budget = st.number_input("Monthly Repayment Budget ($)", min_value=10, value=1000, step=100)
    uploaded_file = st.file_uploader("Upload Bank CSV", type="csv")
    
    if st.button("🗑️ Reset All System Data"):
        st.session_state.debts = []
        st.rerun()

# --- MAIN SCREEN ---
st.title("📈 Strategic Debt Elimination Engine")

tab1, tab2, tab3 = st.tabs(["📥 Data Import", "📊 Analytics Dashboard", "🗓️ Debt-Free Timeline"])

# --- TAB 1: DATA IMPORT ---
with tab1:
    col_entry, col_preview = st.columns([1, 2])
    
    with col_entry:
        st.subheader("Manual Entry")
        with st.form("add_debt", clear_on_submit=True):
            n = st.text_input("Account Name")
            b = st.number_input("Balance ($)", min_value=0.0)
            r = st.number_input("Interest Rate (%)", min_value=0.0)
            m = st.number_input("Minimum Monthly ($)", min_value=0.0)
            if st.form_submit_button("Add to Engine"):
                st.session_state.debts.append({"Name": n, "Balance": b, "Rate": r, "Min": m})
                st.rerun()
    
    with col_preview:
        if uploaded_file:
            df_csv = pd.read_csv(uploaded_file)
            st.subheader("Smart CSV Mapper")
            st.dataframe(df_csv.head(5), use_container_width=True)
            
            c_map, c_mode = st.columns(2)
            col_to_map = c_map.selectbox("Select Amount Column", df_csv.columns)
            mode = c_mode.radio("Logic Mode", ["Sum Negatives Only (Standard Bank)", "Sum All / Flip Sign (Credit Card)"])
            
            # --- THE SMART LOGIC PATCH ---
            if st.button("🚀 Extract Data from CSV"):
                try:
                    nums = pd.to_numeric(df_csv[col_to_map], errors='coerce').fillna(0)
                    
                    if mode == "Sum Negatives Only (Standard Bank)":
                        final_val = abs(nums[nums < 0].sum())
                    else:
                        # For Credit Cards where expenses are +50.00
                        final_val = abs(nums.sum())
                    
                    if final_val > 0:
                        st.session_state.debts.append({
                            "Name": f"Imported_{uploaded_file.name[:5]}", 
                            "Balance": final_val, 
                            "Rate": 18.0, 
                            "Min": final_val * 0.03
                        })
                        st.success(f"Successfully Imported ${final_val:,.2f}!")
                        st.rerun()
                    else:
                        st.error("No debt detected. Ensure you picked the correct column or logic mode.")
                except Exception as e:
                    st.error(f"Error parsing data: {e}")

# --- TAB 2: ANALYTICS ---
with tab2:
    if st.session_state.debts:
        master_df = pd.DataFrame(st.session_state.debts)
        total_debt = master_df['Balance'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Liability", f"${total_debt:,.2f}")
        m2.metric("Weighted Interest", f"{(master_df['Rate'].mean()):.2f}%")
        m3.metric("Monthly Surplus", f"${(budget - master_df['Min'].sum()):.2f}")
        
        fig = go.Figure(data=[go.Pie(labels=master_df['Name'], values=master_df['Balance'], hole=.4)])
        fig.update_layout(title="Debt Concentration")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Current Priority List (Avalanche Method)")
        st.table(master_df.sort_values(by="Rate", ascending=False))
    else:
        st.info("👋 Hello Founder. Awaiting data input in Tab 1 to run optimization.")

# --- TAB 3: THE TIMELINE ---
with tab3:
    if st.session_state.debts:
        # Optimization Simulation
        sim_debts = pd.DataFrame(st.session_state.debts).sort_values(by="Rate", ascending=False).to_dict('records')
        months = 0
        history = []
        
        # Iterative Simulation (Limit 30 years)
        while sum(d['Balance'] for d in sim_debts) > 0 and months < 360:
            months += 1
            available_cash = budget
            
            # Pay Minimums first
            for d in sim_debts:
                interest = (d['Balance'] * (d['Rate']/100)) / 12
                d['Balance'] += interest
                payment = min(d['Balance'], d['Min'])
                d['Balance'] -= payment
                available_cash -= payment
            
            # Apply Surplus to highest interest
            for d in sim_debts:
                if d['Balance'] > 0 and available_cash > 0:
                    extra = min(d['Balance'], available_cash)
                    d['Balance'] -= extra
                    available_cash -= extra
            
            history.append(sum(d['Balance'] for d in sim_debts))

        end_date = datetime.now() + timedelta(days=months*30.44) # Average month length
        
        c1, c2 = st.columns(2)
        c1.success(f"### Debt Free Date: {end_date.strftime('%B %Y')}")
        c2.info(f"### Time to Freedom: {months // 12}y {months % 12}m")
        
        st.line_chart(history)
    else:
        st.warning("No data found to project timeline.")
