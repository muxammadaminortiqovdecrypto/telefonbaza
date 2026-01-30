import streamlit as st
import psycopg2
import pandas as pd
import requests
import base64

# --- KONFIGURATSIYA ---
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"
IMGBB_API_KEY = "7db025f8ea7addb4a9e3d1910b54db49"
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app"

def get_neon_conn():
    try: return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    except: return None

# --- TELEGRAM XABARLARI ---
def send_tg(type, data):
    clean_url = SAYT_LINKI.strip("/")
    if type == "new_ad":
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        link = f"{clean_url}/?task=approve&id={data['id']}"
        kb = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": link}]]}
        payload = {"chat_id": TG_CHAT_ID, "photo": data['img'], "caption": f"📱 {data['m']}\n💰 {data['p']}$", "reply_markup": kb}
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        link = f"{clean_url}/?task=sell&oid={data['oid']}"
        kb = {"inline_keyboard": [[{"text": "💰 Sotuvni tasdiqlash", "url": link}]]}
        payload = {"chat_id": TG_CHAT_ID, "text": f"🛒 BUYURTMA: {data['m']}\n💰 {data['p']}$", "reply_markup": kb}
    requests.post(url, json=payload)

# --- ADMIN TASDIQLASH ---
params = st.query_params
if "task" in params:
    n_conn = get_neon_conn(); cur = n_conn.cursor()
    if params["task"] == "approve":
        cur.execute("SELECT model, narxi, rasm_url, brand, tel_raqam FROM kutilayotganlar WHERE id = %s", (params["id"],))
        res = cur.fetchone()
        if res:
            cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url, brand, tel_raqam) VALUES (%s,%s,%s,%s,%s)", res)
            cur.execute("DELETE FROM kutilayotganlar WHERE id = %s", (params["id"],))
            n_conn.commit(); st.success("✅ Saytga chiqdi!")
    
    elif params["task"] == "sell":
        cur.execute("SELECT telefon_id FROM buyurtmalar WHERE id = %s", (params["oid"],))
        res = cur.fetchone()
        if res:
            cur.execute("DELETE FROM telefonlar WHERE id = %s", (res[0],))
            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (params["oid"],))
            n_conn.commit(); st.warning("✅ Sotildi!")
    cur.close(); n_conn.close()

# --- INTERFEYS ---
st.set_page_config(page_title="Phone Market", layout="wide")
menu = st.sidebar.radio("Menyu", ["🛍 Katalog", "📤 Sotish", "📊 Tahlil"])

if menu == "🛍 Katalog":
    st.title("📱 Katalog")
    n_conn = get_neon_conn(); cur = n_conn.cursor()
    cur.execute("SELECT id, model, narxi, rasm_url, brand FROM telefonlar ORDER BY id DESC")
    rows = cur.fetchall()
    if rows:
        cols = st.columns(4)
        for i, (tid, model, price, img, brand) in enumerate(rows):
            with cols[i % 4]:
                st.image(img, use_container_width=True)
                st.subheader(f"{brand} {model}")
                st.write(f"💰 {price}$")
                if st.button(f"🛒 Sotib olish", key=f"b_{tid}"):
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model, narxi) VALUES (%s,%s,%s) RETURNING id", (tid, model, price))
                    oid = cur.fetchone()[0]; n_conn.commit()
                    send_tg("order", {"m": model, "p": price, "oid": oid})
                    st.success("Buyurtma yuborildi!")
    cur.close(); n_conn.close()

elif menu == "📤 Sotish":
    st.title("🚀 E'lon berish")
    with st.form("f"):
        brand = st.selectbox("Brend", ["Apple", "Samsung", "Xiaomi", "Other"])
        model = st.text_input("Model")
        price = st.number_input("Narx", min_value=1)
        tel = st.text_input("Tel")
        file = st.file_uploader("Rasm")
        if st.form_submit_button("Yuborish"):
            img_b64 = base64.b64encode(file.read()).decode('utf-8')
            res = requests.post("https://api.imgbb.com/1/upload", {"key": IMGBB_API_KEY, "image": img_b64}).json()
            url = res['data']['url']
            n_conn = get_neon_conn(); cur = n_conn.cursor()
            cur.execute("INSERT INTO kutilayotganlar (model, narxi, rasm_url, brand, tel_raqam) VALUES (%s,%s,%s,%s,%s) RETURNING id", (model, price, url, brand, tel))
            nid = cur.fetchone()[0]; n_conn.commit()
            send_tg("new_ad", {"id": nid, "img": url, "m": model, "p": price})
            st.info("Admin tasdiqlashini kuting.")

elif menu == "📊 Tahlil":
    st.title("📊 Analitika")
    st.write("Local bazadagi tahlilni ko'rish uchun pastdagi kodni kompyuteringizda ishlating.")
