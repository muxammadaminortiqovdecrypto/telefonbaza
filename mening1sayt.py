import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. SOZLAMALAR (Bularni albatta to'ldiring)
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE" # O'zingizniki bilan almashtiring
TG_CHAT_ID = "1685342390" # O'zingizniki bilan almashtiring
SAYT_LINKI = "https://telefonbaza-r4qykdsrfj6ds3hys6hzkx.streamlit.app" 

def send_telegram_msg(text, order_id):
    confirm_url = f"{SAYT_LINKI}/?task=confirm&order_id={order_id}"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Tasdiqlash (Saytda)", "url": confirm_url}
        ]]
    }
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "reply_markup": keyboard}
    try:
        requests.post(url, json=payload)
    except:
        pass

def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# --- AVTOMATIK TASDIQLASH ---
query_params = st.query_params
if "task" in query_params and query_params["task"] == "confirm":
    o_id = query_params.get("order_id")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT telefon_id FROM buyurtmalar WHERE id = %s", (o_id,))
        order_data = cur.fetchone()
        if order_data:
            cur.execute("DELETE FROM telefonlar WHERE id = %s", (order_data[0],))
            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (o_id,))
            conn.commit()
            st.success("✅ Buyurtma tasdiqlandi!")
            st.balloons()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Xato: {e}")

# --- INTERFEYS ---
st.sidebar.title("Menyu")
page = st.sidebar.radio("Sahifani tanlang:", ["Foydalanuvchi", "Admin Panel"])

if page == "Foydalanuvchi":
    st.title("📱 Telefon do'koni")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        res = cur.fetchall()
        if res:
            df = pd.DataFrame(res, columns=["ID", "Model", "Narx ($)"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.write("---")
            t_id = st.number_input("Sotib olish uchun ID kiriting:", min_value=1, step=1)
            if st.button("Sotib olish"):
                cur.execute("SELECT model, narxi FROM telefonlar WHERE id = %s", (t_id,))
                t_data = cur.fetchone()
                if t_data:
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s) RETURNING id", (t_id, t_data[0]))
                    new_id = cur.fetchone()[0]
                    conn.commit()
                    send_telegram_msg(f"🔔 Buyurtma: {t_data[0]} ({t_data[1]}$)", new_id)
                    st.success("Telegramga xabar yuborildi!")
                else:
                    st.error("ID topilmadi")
        cur.close()
        conn.close()
    except Exception as e:
        st.error(e)

elif page == "Admin Panel":
    st.title("🔐 Admin Panel")
    pwd = st.text_input("Parol:", type="password")
    if pwd == "admin777":
        st.success("Xush kelibsiz!")
        tab1, tab2 = st.tabs(["Qo'shish", "Buyurtmalar"])
        with tab1:
            m = st.text_input("Model:")
            n = st.number_input("Narx:", min_value=0)
            if st.button("Saqlash"):
                c = get_connection()
                k = c.cursor()
                k.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (m, n))
                c.commit()
                st.success("Qo'shildi!")
                k.close()
                c.close()
        with tab2:
            c = get_connection()
            k = c.cursor()
            k.execute("SELECT id, model, holat FROM buyurtmalar WHERE holat='Kutilmoqda'")
            orders = k.fetchall()
            for o in orders:
                st.write(f"ID: {o[0]} | {o[1]}")
            k.close()
            c.close()
