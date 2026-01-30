import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. SOZLAMALAR (Siz yuborgan ma'lumotlar ulandi)
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# --- SAHIFANING DIZAYNI (CSS) ---
st.set_page_config(page_title="Phone Store", page_icon="📱", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-title {
        color: #2e4053;
        text-align: center;
        font-weight: bold;
        padding-bottom: 20px;
        font-size: 40px;
    }
    div.stButton > button:first-child {
        background-color: #00b894;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #009473;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
def send_telegram_msg(text, order_id):
    confirm_url = f"{SAYT_LINKI}/?task=confirm&order_id={order_id}"
    keyboard = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": confirm_url}]]}
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "reply_markup": keyboard}
    try:
        requests.post(url, json=payload)
    except:
        pass

def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# --- AVTOMATIK TASDIQLASH (Link orqali kelganda) ---
query_params = st.query_params
if "task" in query_params and query_params["task"] == "confirm":
    o_id = query_params.get("order_id")
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT telefon_id FROM buyurtmalar WHERE id = %s", (o_id,))
        order_data = cur.fetchone()
        if order_data:
            cur.execute("DELETE FROM telefonlar WHERE id = %s", (order_data[0],))
            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (o_id,))
            conn.commit()
            st.balloons()
            st.success("✅ Buyurtma tasdiqlandi va ombordan o'chirildi!")
        cur.close(); conn.close()
    except Exception as e:
        st.error(f"Xato: {e}")

# --- INTERFEYS ---
st.sidebar.markdown("## 🧭 Navigatsiya")
page = st.sidebar.radio("", ["🛒 Do'kon sahifasi", "🛠 Admin Panel"])

if page == "🛒 Do'kon sahifasi":
    st.markdown("<h1 class='main-title'>📱 Smartfonlar Markazi</h1>", unsafe_allow_html=True)
    
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        res = cur.fetchall()
        
        if res:
            df = pd.DataFrame(res, columns=["ID", "Model nomi", "Narxi ($)"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.write("---")
            col1, col2 = st.columns([1, 1])
            with col1:
                t_id = st.number_input("Sotib olish uchun ID kiriting:", min_value=1, step=1)
            with col2:
                st.write("##")
                if st.button("🛍 Sotib olish"):
                    cur.execute("SELECT model, narxi FROM telefonlar WHERE id = %s", (t_id,))
                    t_data = cur.fetchone()
                    if t_data:
                        cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s) RETURNING id", (t_id, t_data[0]))
                        new_id = cur.fetchone()[0]
                        conn.commit()
                        send_telegram_msg(f"🔔 YANGI BUYURTMA\n\n📱 Model: {t_data[0]}\n💰 Narxi: {t_data[1]}$\n🆔 ID: {t_id}", new_id)
                        st.toast(f"Xabar yuborildi!", icon='🚀')
                    else:
                        st.error("Bunday ID dagi telefon topilmadi!")
        else:
            st.info("Ombor bo'sh.")
        cur.close(); conn.close()
    except Exception as e:
        st.error(f"Ulanish xatosi: {e}")

elif page == "🛠 Admin Panel":
    st.markdown("<h1 class='main-title'>🔐 Admin Boshqaruvi</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Parol:", type="password")
    if pwd == "admin777":
        st.success("Xush kelibsiz!")
        tab1, tab2 = st.tabs(["➕ Yangi telefon", "📦 Buyurtmalar ro'yxati"])
        
        with tab1:
            m = st.text_input("Model nomi:")
            n = st.number_input("Narxi ($):", min_value=0)
            if st.button("💾 Omborda saqlash"):
                if m:
                    c = get_connection(); k = c.cursor()
                    k.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (m, n))
                    c.commit(); st.success("Qo'shildi!"); k.close(); c.close()
                else: st.warning("Nomini yozing")
        
        with tab2:
            c = get_connection(); k = c.cursor()
            k.execute("SELECT id, model, holat FROM buyurtmalar WHERE holat='Kutilmoqda'")
            orders = k.fetchall()
            if orders:
                for o in orders:
                    st.write(f"📦 ID: {o[0]} | Model: {o[1]}")
            else: st.write("Buyurtmalar yo'q.")
            k.close(); c.close()
