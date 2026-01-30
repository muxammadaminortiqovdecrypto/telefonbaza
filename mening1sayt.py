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

# --- BAZA ULANISHLARI ---
def get_neon_conn():
    try: return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    except: return None

def get_local_conn():
    try: return psycopg2.connect(host="localhost", database="postgres", user="postgres", password="Karotk1y_@k@m")
    except: return None

# --- TELEGRAM XABAR TIZIMI ---
def send_tg_msg(msg_type, data):
    clean_link = SAYT_LINKI.strip("/")
    if msg_type == "new_ad":
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        btn_url = f"{clean_link}/?task=approve_tel&id={data['id']}"
        kb = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "url": btn_url}]]}
        payload = {"chat_id": TG_CHAT_ID, "photo": data['img'], "caption": f"📱 {data['model']}\n💰 {data['price']}$", "reply_markup": kb}
    else: # Buyurtma uchun
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        btn_url = f"{clean_link}/?task=sell_confirm&oid={data['oid']}"
        kb = {"inline_keyboard": [[{"text": "💰 Sotuvni tasdiqlash", "url": btn_url}]]}
        payload = {"chat_id": TG_CHAT_ID, "text": f"🛒 Buyurtma: {data['model']}\n💰 {data['price']}$", "reply_markup": kb}
    requests.post(url, json=payload)

# --- ASOSIY AMALLAR (TASDIQLASH VA SOTUV) ---
params = st.query_params
if "task" in params:
    n_conn = get_neon_conn(); cur = n_conn.cursor()
    if params["task"] == "approve_tel":
        cur.execute("SELECT model, narxi, rasm_url, brand, tel_raqam FROM kutilayotganlar WHERE id = %s", (params["id"],))
        res = cur.fetchone()
        if res:
            cur.execute("INSERT INTO telefonlar (model, narxi, rasm_url, brand, tel_raqam) VALUES (%s,%s,%s,%s,%s)", res)
            cur.execute("DELETE FROM kutilayotganlar WHERE id = %s", (params["id"],))
            n_conn.commit(); st.success("✅ E'lon saytga chiqdi!")
    
    elif params["task"] == "sell_confirm":
        cur.execute("SELECT telefon_id, model FROM buyurtmalar WHERE id = %s", (params["oid"],))
        res = cur.fetchone()
        if res:
            cur.execute("DELETE FROM telefonlar WHERE id = %s", (res[0],))
            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (params["oid"],))
            n_conn.commit(); st.warning(f"✅ {res[1]} sotildi va o'chirildi!")
    cur.close(); n_conn.close()

# --- INTERFEYS ---
st.set_page_config(page_title="Phone Market Pro", layout="wide")
menu = st.sidebar.radio("Menyu:", ["🛍 Katalog", "📤 Sotish", "📊 Tahlil"])

# --- 🛍 KATALOG ---
if menu == "🛍 Katalog":
    st.title("📱 Smartfonlar")
    n_conn = get_neon_conn(); cur = n_conn.cursor()
    cur.execute("SELECT id, model, narxi, rasm_url, brand, chegirma FROM telefonlar")
    rows = cur.fetchall()
    if rows:
        cols = st.columns(4)
        for i, (tid, model, price, img, brand, discount) in enumerate(rows):
            with cols[i % 4]:
                st.image(img, use_container_width=True)
                st.subheader(f"{brand} {model}")
                st.write(f"💰 {price}$")
                if st.button(f"🛒 Sotib olish", key=f"buy_{tid}"):
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model, narxi) VALUES (%s,%s,%s) RETURNING id", (tid, model, price))
                    oid = cur.fetchone()[0]; n_conn.commit()
                    send_tg_msg("order", {"model": model, "price": price, "oid": oid})
                    st.toast("Adminga xabar yuborildi!")
    else: st.info("Katalog bo'sh.")
    cur.close(); n_conn.close()

# --- 📊 TAHLIL (PROFESSIONAL) ---
elif menu == "📊 Tahlil":
    st.title("📈 Bozor va Sotuv Tahlili")
    n_conn = get_neon_conn(); cur = n_conn.cursor()
    
    # 1. Brendlar bo'yicha jami e'lonlar (Grafik)
    cur.execute("SELECT brand, COUNT(*) FROM telefonlar GROUP BY brand")
    df_brand = pd.DataFrame(cur.fetchall(), columns=["Brend", "Soni"])
    
    # 2. Eng ko'p sotilgan modellar (Preferred Choice uchun)
    cur.execute("SELECT model, COUNT(*) FROM buyurtmalar WHERE holat='Sotildi' GROUP BY model ORDER BY 2 DESC LIMIT 5")
    df_sold = pd.DataFrame(cur.fetchall(), columns=["Model", "Sotuv soni"])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Ombor tarkibi")
        st.bar_chart(df_brand.set_index("Brend"))
    with col2:
        st.subheader("🔥 Top sotuvlar")
        st.table(df_sold)

    # Preferred Choice mantiqi
    cur.execute("SELECT model FROM telefonlar WHERE narxi < (SELECT AVG(narxi) FROM telefonlar) ORDER BY id DESC LIMIT 1")
    pref = cur.fetchone()
    if pref:
        st.success(f"🌟 **Preferred Choice:** {pref[0]} (Eng yaxshi narx/sifat mutanosibligi)")
    
    cur.close(); n_conn.close()
