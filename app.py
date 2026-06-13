import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from fpdf import FPDF

# --- Page Configuration ---
st.set_page_config(page_title="EcoTrack Enterprise", page_icon="🌱", layout="wide")

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect("carbon_tracker.db")
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    # Carbon logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            region TEXT,
            car_co2 REAL,
            flight_co2 REAL,
            electric_co2 REAL,
            diet_co2 REAL,
            total_co2 REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Password Hashing Function ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- Initialize Authentication Session States ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- INTERFACE: GATEWAY (NOT LOGGED IN) ---
if not st.session_state['logged_in']:
    st.title("🔐 Welcome to EcoTrack")
    st.subheader("Understand, track, and reduce your global footprint impact.")
    
    auth_mode = st.tabs(["Login Account", "Create Account"])
    
    with auth_mode[0]:
        st.write("### Sign In to Dashboard")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            conn = sqlite3.connect("carbon_tracker.db")
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username=?", (username,))
            user_record = cursor.fetchone()
            conn.close()
            
            if user_record and user_record[0] == make_hash(password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.rerun()
            else:
                st.error("Invalid credentials entered.")
                
    with auth_mode[1]:
        st.write("### Register New Credentials")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register Account"):
            if new_user and new_pass:
                try:
                    conn = sqlite3.connect("carbon_tracker.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users VALUES (?, ?)", (new_user, make_hash(new_pass)))
                    conn.commit()
                    conn.close()
                    st.success("Account created! Please change tab to Login.")
                except sqlite3.IntegrityError:
                    st.error("Username already taken in system databases.")
            else:
                st.warning("Please fully populate entry parameters.")

# --- INTERFACE: CORE MANAGEMENT DASHBOARD (LOGGED IN) ---
else:
    st.sidebar.title(f"👤 Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout Session"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()

    page = st.sidebar.radio("Navigation Pane", ["Track & Calculate", "Historical Analytics & PDF Export"])
    
    # Regional grid impact weights (kg CO2 / kWh electricity used)
    REGIONAL_FACTORS = {
        "Global Average": 0.43, 
        "India": 0.71, 
        "United States": 0.37, 
        "European Union": 0.23, 
        "Australia": 0.65
    }

    # --- TRACKING CONSOLE ---
    if page == "Track & Calculate":
        st.header("📊 Calculate Monthly Footprint Vectors")
        
        with st.form("carbon_calculation_form"):
            col1, col2 = st.columns(2)
            with col1:
                region = st.selectbox("Select Tracking Region", list(REGIONAL_FACTORS.keys()))
                km_driven = st.number_input("Car Distance Driven (km / month)", min_value=0, value=200)
                flights = st.number_input("Air Flights Logged (hours / month)", min_value=0, value=1)
            with col2:
                electricity = st.number_input("Grid Electricity Consumption (kWh / month)", min_value=0, value=150)
                diet = st.selectbox("Primary Nutritional Profile", ["Meat-heavy", "Balanced", "Vegetarian", "Vegan"])
            
            submitted = st.form_submit_with_button_label("Commit Month Metrics")

        # Carbon conversion metrics math logic
        car_co2 = km_driven * 0.2
        flight_co2 = flights * 90
        electric_co2 = electricity * REGIONAL_FACTORS[region]
        
        diet_factors = {"Meat-heavy": 208, "Balanced": 141, "Vegetarian": 100, "Vegan": 66}
        diet_co2 = diet_factors[diet]
        
        total_co2_kg = car_co2 + flight_co2 + electric_co2 + diet_co2
        total_co2_tons = total_co2_kg / 1000

        if submitted:
            conn = sqlite3.connect("carbon_tracker.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (username, date, region, car_co2, flight_co2, electric_co2, diet_co2, total_co2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (st.session_state['username'], datetime.now().strftime("%Y-%m-%d"), region, car_co2, flight_co2, electric_co2, diet_co2, total_co2_tons))
            conn.commit()
            conn.close()
            st.success("📝 Success! Entry saved securely inside database profile records.")

        # Display Live Breakdown Graph for current values
        st.write("---")
        st.subheader("Current Parameter Breakdown Visualization")
        metrics_df = pd.DataFrame({
            "Source Sector": ["Driving Vector", "Flight Vector", "Power Grid Vector", "Dietary Impact"],
            "Emissions (kg CO2)": [car_co2, flight_co2, electric_co2, diet_co2]
        })
        fig_pie = px.pie(metrics_df, values="Emissions (kg CO2)", names="Source Sector", title="Current Month Percentage Impact Weights", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- ANALYTICS AND EXPORT MANAGEMENT ---
    elif page == "Historical Analytics & PDF Export":
        st.header("📈 Historical Progression Matrix & Statement Export")
        
        conn = sqlite3.connect("carbon_tracker.db")
        df = pd.read_sql_query("SELECT * FROM logs WHERE username=? ORDER BY date ASC", conn, params=(st.session_state['username'],))
        conn.close()
        
        if df.empty:
            st.info("No timeline profile datasets found. Proceed to metrics log module first.")
        else:
            fig_line = px.line(df, x="date", y="total_co2", markers=True, title="Your Timeline Footprint Trend (Metric Tons CO2)")
            st.plotly_chart(fig_line, use_container_width=True)
            
            st.subheader("🖨️ Statement and Report Distribution Panels")
            c1, c2 = st.columns(2)
            
            # Prepare PDF generation data block
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            pdf.cell(200, 10, txt=f"EcoTrack Statement for: {st.session_state['username']}", ln=1, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Generated on Timeline Index: {datetime.now().strftime('%Y-%m-%d')}", ln=2, align='C')
            pdf.ln(10)
            
            for index, row in df.iterrows():
                pdf.cell(200, 10, txt=f"Date Matrix: {row['date']} | Emission Load: {row['total_co2']:.3f} Tons CO2 | Region Context: {row['region']}", ln=1)
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            
            with c1:
                st.write("#### Local System Download")
                st.download_button(label="📥 Download PDF Summary Report", data=pdf_output, file_name="Carbon_Profile_Report.pdf", mime="application/pdf")
                
            with c2:
                st.write("#### SMTP Mail Distribution")
                target_email = st.text_input("Destination Email")
                if st.button("📧 Dispatch Email Statement Asset"):
                    if target_email:
                        try:
    # Your code here (e.g., sending email or database updates)
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()
    st.success("Report successfully emailed!")
except Exception as e:
    st.error(f"Failed to transmit email configuration: {e}")


