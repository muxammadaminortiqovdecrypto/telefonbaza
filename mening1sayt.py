import streamlit as st
import psycopg2
import pandas as pd
import requests
import base64

# 1. SOZLAMALAR
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
IMGBB_API_KEY = "7db025f8ea7addb4a9e3d1910b54db49"
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

def upload_image(image_file):
    url = "https://api.imgbb.com/1/upload"
    try:
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(image_file.read()).decode('utf-8'),
        }
        res = requests.post(url, payload)
        return res.json()['data']['url']
    except:
        return None

def send_tg_review(model, narx, photo_url, temp_id):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    approve_url = f"{SAYT_LINKI}/?task=approve_tel&id={temp_id}"
    keyboard = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": approve_url}]]}
    caption = f"🆕 *YANGI E'LON*\n\n📱 Model: {model}\n💰 Narxi: {narx}$\n\nTasdiqlash tugmasini bossangiz saytga chiqadi."
    payload = {"chat_id": TG_CHAT_ID, "photo": photo_url, "caption": caption, "parse_mode": "Markdown", "reply_markup": keyboard}
    requests.post(url, json=payload)

# --- AVTOMATIK TASDIQLASH ---
q_params = st.query_params
if "task" in q_params:
    task = q_params["task"]
    t_id = q_params.get("id")
    try:
        conn = get_connection(); cur = conn.cursor()
        if task == "approve_tel":
            cur.execute("SELECT model, narxi, rasm_url FROM kutilayotganlar WHERE id = %s", (t_id,))
            data = cur.fetchone()
            if data:
                cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url) VALUES (%s, %s, %s)", data)
                cur.execute("DELETE FROM kutilayotganlar WHERE id = %s", (t_id,))
                conn.commit(); st.balloons(); st.success("Tasdiqlandi!")
        cur.close(); conn.close()
    except Exception as e: st.error(f"Xato: {e}")

# --- INTERFEYS ---
st.set_page_config(page_title="E-Market Pro", page_icon="📱", layout="wide")
menu = st.sidebar.radio("Bo'limlar:", ["🛍 Katalog", "📤 Telefon sotish", "🛠 Admin"])

if menu == "🛍 Katalog":
    st.markdown("<h1 style='text-align:center;'>📱 Sotuvdagi Telefonlar</h1>", unsafe_allow_html=True)
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, model, narxi, rasm_url FROM telefonlar ORDER BY id DESC")
        items = cur.fetchall()
        if items:
            cols = st.columns(4)
            for i, (id, model, narx, rasm) in enumerate(items):
                with cols[i % 4]:
                    st.image(rasm, use_container_width=True)
                    st.markdown(f"**{model}**")
                    st.write(f"💰 {narx}$")
                    if st.button("Sotib olish", key=f"buy_{id}"):
                        st.toast("Buyurtma yuborildi!")
        else: st.info("Hozircha ombor bo'sh.")
        cur.close(); conn.close()
    except: st.error("Baza bilan muammo.")

elif menu == "📤 Telefon sotish":
    st.title("📞 Telefoningizni soting")
    with st.form("upload_form"):
        model = st.text_input("Model nomi:")
        narx = st.number_input("Narxi ($):", min_value=1)
        file = st.file_uploader("Telefon rasmini yuklang", type=['jpg', 'png', 'jpeg'])
        if st.form_submit_button("Tekshirishga yuborish"):
            if model and file:
                img_url = upload_image(file)
                if img_url:
                    conn = get_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO kutilayotganlar (model, narxi, rasm_url) VALUES (%s, %s, %s) RETURNING id", (model, narx, img_url))
                    temp_id = cur.fetchone()[0]; conn.commit()
                    send_tg_review(model, narx, img_url, temp_id)
                    st.success("✅ Adminga yuborildi!")
                    cur.close(); conn.close()
                else: st.error("Rasm yuklanmadi.")
            else: st.warning("To'ldiring!")

elif menu == "🛠 Admin":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "admin777":
        st.title("🛠 Admin paneli")
        st.write("Statistika bu yerda bo'ladi.")
