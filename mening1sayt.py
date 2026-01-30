import streamlit as st
import psycopg2
import pandas as pd
import requests
import base64

# --- 1. SOZLAMALAR ---
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
IMGBB_API_KEY = "7db025f8ea7addb4a9e3d1910b54db49" # Sizning kalitingiz saqlandi
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# --- 2. BAZA BILAN ALOQA ---
def get_connection():
    try:
        return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    except Exception as e:
        st.error(f"🚨 Baza xatosi: {e}")
        return None

# --- 3. RASM YUKLASH (IMGBB) ---
def upload_image(image_file):
    url = "https://api.imgbb.com/1/upload"
    try:
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(image_file.read()).decode('utf-8'),
        }
        res = requests.post(url, payload)
        if res.status_code == 200:
            return res.json()['data']['url']
        st.error(f"🚨 ImgBB xatosi: {res.text}")
        return None
    except Exception as e:
        st.error(f"🚨 Rasm yuklashda texnik xato: {e}")
        return None

# --- 4. TELEGRAM XABARLARI ---
def send_tg_msg(msg_type, data):
    clean_link = SAYT_LINKI.strip("/")
    
    if msg_type == "new_ad":
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        approve_url = f"{clean_link}/?task=approve_tel&id={data['temp_id']}"
        keyboard = {"inline_keyboard": [[{"text": "✅ Saytga chiqarish", "url": approve_url}]]}
        payload = {
            "chat_id": TG_CHAT_ID,
            "photo": data['img_url'],
            "caption": f"🆕 *YANGI E'LON*\n\n📱 Model: {data['model']}\n💰 Narx: {data['price']}$",
            "parse_mode": "Markdown", "reply_markup": keyboard
        }
    
    elif msg_type == "order":
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        sell_url = f"{clean_link}/?task=sell_confirm&order_id={data['order_id']}"
        keyboard = {"inline_keyboard": [[{"text": "💰 Sotuvni tasdiqlash", "url": sell_url}]]}
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": f"🛒 *YANGI BUYURTMA*\n\n📱 Model: {data['model']}\n💰 Narx: {data['price']}$",
            "parse_mode": "Markdown", "reply_markup": keyboard
        }

    requests.post(url, json=payload)

# --- 5. TASDIQLASH LOGIKASI ---
params = st.query_params
if "task" in params:
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        try:
            if params["task"] == "approve_tel":
                cur.execute("SELECT model, narxi, rasm_url FROM kutilayotganlar WHERE id = %s", (params["id"],))
                row = cur.fetchone()
                if row:
                    cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url) VALUES (%s, %s, %s)", row)
                    cur.execute("DELETE FROM kutilayotganlar WHERE id = %s", (params["id"],))
                    conn.commit(); st.balloons(); st.success("✅ E'lon tasdiqlandi!")
            
            elif params["task"] == "sell_confirm":
                cur.execute("SELECT telefon_id FROM buyurtmalar WHERE id = %s", (params["order_id"],))
                order = cur.fetchone()
                if order:
                    cur.execute("DELETE FROM telefonlar WHERE id = %s", (order[0],))
                    cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (params["order_id"],))
                    conn.commit(); st.success("✅ Mahsulot sotildi!")
            cur.close(); conn.close()
        except: pass

# --- 6. INTERFEYS ---
st.set_page_config(page_title="Phone Market", layout="wide")
menu = st.sidebar.radio("Bo'limlar:", ["🛍 Katalog", "📤 Telefon sotish", "🛠 Admin"])

if menu == "🛍 Katalog":
    st.markdown("<h1 style='text-align:center;'>📱 Sotuvdagi telefonlar</h1>", unsafe_allow_html=True)
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT id, model, narxi, rasm_url FROM telefonlar ORDER BY id DESC")
        items = cur.fetchall()
        if items:
            cols = st.columns(4)
            for i, (tid, model, price, img) in enumerate(items):
                with cols[i % 4]:
                    st.image(img, use_container_width=True)
                    st.markdown(f"**{model}**")
                    st.write(f"💰 {price}$")
                    if st.button(f"🛍 Sotib olish", key=f"b_{tid}"):
                        cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s) RETURNING id", (tid, model))
                        new_oid = cur.fetchone()[0]; conn.commit()
                        send_tg_msg("order", {"model": model, "price": price, "order_id": new_oid})
        else: st.info("Hozircha hech narsa yo'q.")
        cur.close(); conn.close()

elif menu == "📤 Telefon sotish":
    st.title("🚀 Telefon sotish uchun ariza")
    with st.form("sell_form"):
        m_name = st.text_input("Model nomi:")
        m_price = st.number_input("Narxi ($):", min_value=1)
        m_file = st.file_uploader("Rasm yuklang", type=['jpg','jpeg','png'])
        if st.form_submit_button("Adminga yuborish"):
            if m_name and m_file:
                img_url = upload_image(m_file)
                if img_url:
                    conn = get_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO kutilayotganlar (model, narxi, rasm_url) VALUES (%s, %s, %s) RETURNING id", (m_name, m_price, img_url))
                    temp_id = cur.fetchone()[0]; conn.commit()
                    send_tg_msg("new_ad", {"model": m_name, "price": m_price, "img_url": img_url, "temp_id": temp_id})
                    st.success("✅ Tekshiruvga ketdi!")
                    cur.close(); conn.close()

elif menu == "🛠 Admin":
    pwd = st.text_input("Parol:", type="password")
    if pwd == "admin777":
        st.title("🛠 Boshqaruv")
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT count(*) FROM buyurtmalar WHERE holat='Sotildi'")
        sotilganlar = cur.fetchone()[0]
        st.metric("Jami sotilgan mahsulotlar", sotilganlar)
        
        st.subheader("📦 Ombor ro'yxati")
        cur.execute("SELECT id, model FROM telefonlar")
        for tid, tmodel in cur.fetchall():
            col1, col2 = st.columns([3, 1])
            col1.write(f"ID: {tid} | {tmodel}")
            if col2.button("O'chirish", key=f"del_{tid}"):
                cur.execute("DELETE FROM telefonlar WHERE id = %s", (tid,))
                conn.commit(); st.rerun()
        cur.close(); conn.close()
