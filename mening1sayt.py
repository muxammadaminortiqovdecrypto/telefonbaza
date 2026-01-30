import streamlit as st
import psycopg2
import pandas as pd
import requests
import base64

# 1. SOZLAMALAR
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
IMGBB_API_KEY = "7db025f8ea7addb4a9e3d1910b54db49" # Test uchun (o'zingiznikini qo'ying)
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# --- BAZA BILAN ALOQA (DEBUG REJIMIDA) ---
def get_connection():
    try:
        return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    except Exception as e:
        st.error(f"🚨 ULANISHDA XATO: Bazaga bog'lanib bo'lmadi. Sababi: {e}")
        return None

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
        else:
            st.error(f"🚨 IMGBB XATOSI: {res.text}")
            return None
    except Exception as e:
        st.error(f"🚨 RASM YUKLASHDA TEXNIK XATO: {e}")
        return None

# --- TELEGRAM FUNKSIYASI ---
def send_tg_review(model, narx, photo_url, temp_id):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    approve_url = f"{SAYT_LINKI}/?task=approve_tel&id={temp_id}"
    keyboard = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": approve_url}]]}
    caption = f"🆕 *YANGI E'LON*\n\n📱 Model: {model}\n💰 Narxi: {narx}$"
    payload = {"chat_id": TG_CHAT_ID, "photo": photo_url, "caption": caption, "parse_mode": "Markdown", "reply_markup": keyboard}
    try:
        r = requests.post(url, json=payload)
        if r.status_code != 200: st.warning(f"⚠️ Telegramga xabar ketmadi: {r.text}")
    except: pass

# --- AVTOMATIK TASDIQLASH ---
q_params = st.query_params
if "task" in q_params:
    task = q_params["task"]
    t_id = q_params.get("id")
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            if task == "approve_tel":
                cur.execute("SELECT model, narxi, rasm_url FROM kutilayotganlar WHERE id = %s", (t_id,))
                data = cur.fetchone()
                if data:
                    cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url) VALUES (%s, %s, %s)", data)
                    cur.execute("DELETE FROM kutilayotganlar WHERE id = %s", (t_id,))
                    conn.commit()
                    st.balloons()
                    st.success("✅ Tasdiqlandi!")
            cur.close(); conn.close()
        except Exception as e:
            st.error(f"🚨 TASDIQLASHDA SQL XATO: {e}")

# --- INTERFEYS ---
st.set_page_config(page_title="E-Market Pro", page_icon="📱", layout="wide")
menu = st.sidebar.radio("Bo'limlar:", ["🛍 Katalog", "📤 Telefon sotish", "🛠 Admin"])

# 1. KATALOG
if menu == "🛍 Katalog":
    st.markdown("<h1 style='text-align:center;'>📱 Sotuvdagi Telefonlar</h1>", unsafe_allow_html=True)
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, model, narxi, rasm_url FROM telefonlar ORDER BY id DESC")
            items = cur.fetchall()
            if items:
                cols = st.columns(4)
                for i, (id, model, narx, rasm) in enumerate(items):
                    with cols[i % 4]:
                        if rasm: st.image(rasm, use_container_width=True)
                        st.markdown(f"**{model}**")
                        st.write(f"💰 {narx}$")
                        st.button("Sotib olish", key=f"buy_{id}")
            else:
                st.info("ℹ️ Ombor hozircha bo'sh. Telefon qo'shilishini kuting.")
            cur.close(); conn.close()
        except Exception as e:
            st.error(f"🚨 KATALOGDA SQL XATO: {e}")
            st.info("💡 Maslahat: SQL Editorga kirib 'rasm_url' ustuni borligini tekshiring.")

# 2. TELEFON SOTISH
elif menu == "📤 Telefon sotish":
    st.title("📞 Telefoningizni soting")
    with st.form("upload_form"):
        model = st.text_input("Model nomi:")
        narx = st.number_input("Narxi ($):", min_value=1)
        file = st.file_uploader("Rasm yuklang", type=['jpg', 'png', 'jpeg'])
        if st.form_submit_button("Yuborish"):
            if model and file:
                img_url = upload_image(file)
                if img_url:
                    conn = get_connection()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO kutilayotganlar (model, narxi, rasm_url) VALUES (%s, %s, %s) RETURNING id", (model, narx, img_url))
                            temp_id = cur.fetchone()[0]
                            conn.commit()
                            send_tg_review(model, narx, img_url, temp_id)
                            st.success("✅ Adminga yuborildi!")
                            cur.close(); conn.close()
                        except Exception as e:
                            st.error(f"🚨 SOTISHDA SQL XATO: {e}")
                else: st.error("❌ Rasm yuklanmadi, API keyni tekshiring.")
            else: st.warning("⚠️ Ma'lumotlarni to'ldiring!")

# 3. ADMIN
elif menu == "🛠 Admin":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "admin777":
        st.title("🛠 Admin paneli")
        st.write("Tizim barqaror ishlamoqda ✅")
