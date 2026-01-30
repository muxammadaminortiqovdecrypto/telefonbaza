import streamlit as st
import psycopg2
import requests
import base64

# --- SOZLAMALAR ---
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
IMGBB_API_KEY = "7db025f8ea7addb4a9e3d1910b54db49" # Sizning kalitingiz saqlandi
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

# 1. NEON (Onlayn) ulanishi
def get_neon_conn():
    try:
        return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    except Exception as e:
        st.error(f"🚨 Neon ulanishda xato: {e}")
        return None

# 2. LOCAL (Kompyuteringiz) ulanishi
def get_local_conn():
    try:
        # 'Karotk1y_@k@m' parolini ishlatamiz
        return psycopg2.connect(
            host="localhost", 
            database="postgres", 
            user="postgres", 
            password="Karotk1y_@k@m"
        )
    except Exception as e:
        # Saytda xalaqit bermasligi uchun faqat ogohlantirish beramiz
        return None

# Rasm yuklash funksiyasi
def upload_image(image_file):
    url = "https://api.imgbb.com/1/upload"
    try:
        payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(image_file.read()).decode('utf-8')}
        res = requests.post(url, payload)
        return res.json()['data']['url'] if res.status_code == 200 else None
    except: return None

# --- ASOSIY LOGIKA ---
st.set_page_config(page_title="Dual-DB Market", layout="wide")
menu = st.sidebar.radio("Bo'limlar:", ["🛍 Katalog", "📤 Telefon sotish", "📊 Tahlil"])

if menu == "🛍 Katalog":
    st.title("📱 Sotuvdagi telefonlar")
    conn = get_neon_conn()
    if conn:
        cur = conn.cursor()
        # Rasm_url xatosini oldini olish uchun "SELECT *" o'rniga aniq nomlarni yozamiz
        cur.execute("SELECT model, narxi, rasm_url FROM telefonlar ORDER BY id DESC")
        items = cur.fetchall()
        if items:
            cols = st.columns(4)
            for i, (model, narx, rasm) in enumerate(items):
                with cols[i % 4]:
                    st.image(rasm if rasm else "https://via.placeholder.com/150")
                    st.subheader(model)
                    st.write(f"💰 {narx}$")
        else: st.info("Hozircha mahsulot yo'q.")
        cur.close(); conn.close()

elif menu == "📤 Telefon sotish":
    st.title("🚀 Yangi e'lon")
    with st.form("dual_upload"):
        brand = st.selectbox("Brend:", ["Apple", "Samsung", "Xiaomi", "Google"])
        model = st.text_input("Model:")
        price = st.number_input("Narx:", min_value=1)
        file = st.file_uploader("Rasm yuklang")
        
        if st.form_submit_button("Ikkala bazaga saqlash"):
            img_url = upload_image(file)
            if img_url:
                # A. NEON-GA YOZISH
                n_conn = get_neon_conn()
                if n_conn:
                    n_cur = n_conn.cursor()
                    n_cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url, brand) VALUES (%s, %s, %s, %s)", (model, price, img_url, brand))
                    n_conn.commit(); n_cur.close(); n_conn.close()
                
                # B. LOCAL-GA YOZISH (Sinxronizatsiya)
                l_conn = get_local_conn()
                if l_conn:
                    l_cur = l_conn.cursor()
                    l_cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url, brand) VALUES (%s, %s, %s, %s)", (model, price, img_url, brand))
                    l_conn.commit(); l_cur.close(); l_conn.close()
                    st.success("✅ Ma'lumot Local bazaga ham saqlandi!")
                
                st.success("🚀 Sayt yangilandi!")
            else: st.error("Rasm yuklanmadi.")
