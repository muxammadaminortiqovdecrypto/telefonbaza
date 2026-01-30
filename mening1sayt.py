import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. SOZLAMALAR
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# --- TELEGRAM FUNKSIYALARI ---
def send_telegram_msg(text, order_id=None, is_menu=False):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": text,
        "parse_mode": "Markdown"
    }
    
    # 1. Tasdiqlash tugmasi (Inline Keyboard)
    if order_id:
        confirm_url = f"{SAYT_LINKI}/?task=confirm&order_id={order_id}"
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": confirm_url}]]
        }
    
    # 2. Asosiy Menyu tugmasi (Reply Keyboard)
    if is_menu:
        payload["reply_markup"] = {
            "keyboard": [[{"text": "📦 Omborni ko'rish"}]],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    try: requests.post(url, json=payload)
    except: pass

def get_ombor_status():
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT model, narxi FROM telefonlar ORDER BY id DESC")
        res = cur.fetchall()
        cur.close(); conn.close()
        if res:
            text = "📋 *OMBOR HOLATI*\n\n"
            for m, n in res:
                text += f"📱 *{m}* — `{n}$` \n"
            return text
        return "📭 Ombor hozircha bo'sh."
    except: return "❌ Baza bilan aloqa uzildi."

def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# --- DIZAYN ---
st.set_page_config(page_title="Phone Store", page_icon="📱")
st.markdown("<style>.stApp { background-color: #f4f7f6; }</style>", unsafe_allow_html=True)

# --- AVTOMATIK TASDIQLASH ---
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
            st.balloons(); st.success("✅ Tasdiqlandi!")
        cur.close(); conn.close()
    except Exception as e: st.error(e)

# --- INTERFEYS ---
st.sidebar.title("Menyu")
page = st.sidebar.radio("", ["🛒 Do'kon", "🛠 Admin"])

if page == "🛒 Do'kon":
    st.title("📱 Smartfonlar Markazi")
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        res = cur.fetchall()
        if res:
            df = pd.DataFrame(res, columns=["ID", "Model", "Narx ($)"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            t_id = st.number_input("ID kiriting:", min_value=1, step=1)
            if st.button("🛍 Sotib olish"):
                cur.execute("SELECT model, narxi FROM telefonlar WHERE id = %s", (t_id,))
                t_data = cur.fetchone()
                if t_data:
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s) RETURNING id", (t_id, t_data[0]))
                    new_id = cur.fetchone()[0]; conn.commit()
                    send_telegram_msg(f"🔔 *Yangi Buyurtma!*\n\n📱 Model: {t_data[0]}\n💰 Narxi: {t_data[1]}$", new_id)
                    st.toast("Adminga xabar ketdi!")
        cur.close(); conn.close()
    except Exception as e: st.error(e)

elif page == "🛠 Admin":
    st.title("🔐 Admin Panel")
    pwd = st.text_input("Parol:", type="password")
    if pwd == "admin777":
        # Bot tugmasini faollashtirish
        if st.button("🚀 Botda 'Ombor' tugmasini chiqarish"):
            send_telegram_msg("Pastdagi tugma orqali omborni tekshirishingiz mumkin 👇", is_menu=True)
            st.success("Telegram botga tugma yuborildi!")
            
        tab1, tab2 = st.tabs(["➕ Qo'shish", "📦 Buyurtmalar"])
        with tab1:
            m = st.text_input("Model:")
            n = st.number_input("Narx:", min_value=0)
            if st.button("Saqlash"):
                c = get_connection(); k = c.cursor()
                k.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (m, n))
                c.commit(); st.success("Qo'shildi!"); k.close(); c.close()
