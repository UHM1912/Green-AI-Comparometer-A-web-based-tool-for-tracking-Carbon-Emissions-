import streamlit as st
from auth import login, sign_up

st.set_page_config(page_title="Login | GreenAI Comparometer", layout="centered")

# --- CSS Styling ---
st.markdown("""
<style>
.stApp { 
    background: url('https://www.thedigitalspeaker.com/content/images/2023/02/Sustainable-AI-greener-future.jpg') center/cover fixed no-repeat;
    color: #c7d9b9; font-family: 'Inter', sans-serif; min-height: 100vh;
}
.stApp::before {
    content:""; position:fixed; inset:0; background: rgba(20,30,15,0.75); backdrop-filter: blur(6px); pointer-events:none; z-index:0;
}
[data-testid="stAppViewContainer"]>.main, .block-container {position:relative; z-index:1;}
.header-wrapper {max-width:1000px; margin:0 auto 1rem; text-align:center;}
.title-block h1 {color:#a0d468; font-size:2.4rem; text-shadow:0 0 6px #335522aa;}
.title-block .tagline {color:#8cbf40; font-style:italic;}
.stTextInput>div>div>input {border-radius:10px; padding:10px; background:#2b2b2b; color:#c7d9b9;}
.stButton>button {border-radius:10px; padding:10px 20px; background:linear-gradient(135deg,#629f38,#2c5b11); color:white; font-weight:600;}
.stButton>button:hover {filter:brightness(1.1);}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="header-wrapper">
  <div class="title-block">
    <h1>🌱 GreenAI Comparometer</h1>
    <div class="tagline">Code Smart. Code Green. Compare to Care.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Tabs for Login / Sign Up ---
tab1, tab2 = st.tabs(["Login", "Sign Up"])

# --- LOGIN TAB ---
with tab1:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        success, result = login(email, password)
        if success:
            # Save login state
            st.session_state['user'] = result
            st.session_state['logged_in'] = True

            st.success(f"✅ Login successful! Welcome, {result['name']}.")

            # Show dashboard links
            st.markdown("### 🚀 Choose a Tool to Continue:")
            st.page_link("pages/eco2ai_web_tool.py", label="🌍 eco2AI Tool")
            st.page_link("pages/codecarbon_web_tool.py", label="⚡ CodeCarbon Tool")
            st.page_link("pages/carbontracker_web_tool.py", label="📊 CarbonTracker Tool")

        else:
            st.error(result)

# --- SIGN UP TAB ---
with tab2:
    name = st.text_input("Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
    
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("❌ Passwords do not match!")
        else:
            success, msg = sign_up(name, email, password)
            if success:
                st.success("🎉 " + msg)
            else:
                st.error(msg)
