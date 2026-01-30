import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. SOZLAMALAR
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# --- BAZA BILAN ALOQA ---
def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# --- TELEGRAMGA XABAR YUBORISH ---
def send_telegram_msg(text, order_id=None, is_menu=False):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    reply_markup = {}
    
    if order_id:
        confirm_url = f"{SAYT_LINKI}/?task=confirm&order_id={order_id}"
        reply_markup["inline_keyboard"] = [[{"text": "✅ Tasdiqlash", "url": confirm_url}]]
    
    if is_menu:
        reply_markup["keyboard"] = [[{"text": "📦 Omborni ko'rish"}]],
        reply_markup["resize_keyboard"] = True
        reply_markup["one_time_keyboard"] = False

    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup if reply_markup else None
    }
    try: requests.post(url, json=payload)
    except: pass

# --- DIZAYN (CSS) ---
st.set_page_config(page_title="Phone Store", page_icon="📱", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-title { color: #2e4053; text-align: center; font-weight: bold; font-size: 35px; margin-bottom: 20px; }
    div.stButton > button:first-child {
        background-color: #00b894; color: white; border-radius: 10px; font-weight: bold; border: none; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #009473; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- AVTOMATIK TASDIQLASH (Link orqali) ---
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
    except Exception as e: st.error(f"Xato: {e}")

# --- NAVIGATSIYA ---
st.sidebar.markdown("## 🧭 Menyu")
page = st.sidebar.radio("", ["🛒 Do'kon sahifasi", "🛠 Admin Panel"])

# --- FOYDALANUVCHI SAHIFASI ---
if page == "🛒 Do'kon sahifasi":
    st.markdown("<h1 class='main-title'>📱 Smartfonlar Markazi</h1>", unsafe_allow_html=True)
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        res = cur.fetchall()
        
        if res:
            st.subheader("Mavjud telefonlar")
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
                        new_id = cur.fetchone()[0]; conn.commit()
                        send_telegram_msg(f"🔔 *YANGI BUYURTMA*\n\n📱 Model: {t_data[0]}\n💰 Narxi: {t_data[1]}$", new_id)
                        st.toast(f"So'rov yuborildi!", icon='🚀')
                    else: st.error("ID topilmadi!")
        else: st.info("Hozircha ombor bo'sh.")
        cur.close(); conn.close()
    except Exception as e: st.error(f"Xato: {e}")

# --- ADMIN PANEL ---
elif page == "🛠 Admin Panel":
    st.markdown("<h1 class='main-title'>🔐 Admin Boshqaruvi</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Parolni kiriting:", type="password")
    
    if pwd == "admin777":
        st.success("Xush kelibsiz!")
        
        # Bot tugmasi
        if st.button("🚀 Botda 'Ombor' tugmasini chiqarish"):
            send_telegram_msg("Bot klaviaturasi yangilandi! Pastdagi tugmani bosing 👇", is_menu=True)
            st.toast("Botga xabar ketdi!")

        tab1, tab2 = st.tabs(["➕ Yangi telefon", "📦 Buyurtmalar"])
        
        with tab1:
            m_nomi = st.text_input("Telefon modeli:")
            m_narxi = st.number_input("Narxi ($):", min_value=0, step=10)
            if st.button("💾 Omborda saqlash"):
                if m_nomi:
                    c = get_connection(); k = c.cursor()
                    k.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (m_nomi, m_narxi))
                    c.commit(); st.success(f"{m_nomi} qo'shildi!"); k.close(); c.close()
                else: st.warning("Model nomini yozing!")

        with tab2:
            st.subheader("Kutilayotgan buyurtmalar")
            c = get_connection(); k = c.cursor()
            k.execute("SELECT id, model, holat FROM buyurtmalar WHERE holat='Kutilmoqda'")
            orders = k.fetchall()
            if orders:
                for o in orders:
                    st.write(f"🆔 Buyurtma ID: {o[0]} | 📱 Model: {o[1]}")
            else: st.write("Yangi buyurtmalar yo'q.")
            k.close(); c.close()
