import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. TELEGRAM SOZLAMALARI
TG_TOKEN = "SIZNING_BOT_TOKENINGIZ"
TG_CHAT_ID = "SIZNING_CHAT_ID_RAQAMINGIZ"
SAYT_LINKI = "https://sizning-saytingiz.streamlit.app" # O'zingizning streamlit linkizni yozing

def send_telegram_msg(text, order_id):
    # Telegram xabari ichida tugma yaratish
    confirm_url = f"{SAYT_LINKI}/?task=confirm&order_id={order_id}"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Tasdiqlash (Saytda)", "url": confirm_url}
        ]]
    }
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "reply_markup": keyboard}
    requests.post(url, json=payload)

# 2. BAZAGA ULANISH
def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# --- AVTOMATIK TASDIQLASH (Telegramdan kelganda) ---
query_params = st.query_params
if "task" in query_params and query_params["task"] == "confirm":
    order_id = query_params.get("order_id")
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Buyurtma ma'lumotlarini olish
        cur.execute("SELECT telefon_id FROM buyurtmalar WHERE id = %s", (order_id,))
        order_data = cur.fetchone()
        if order_data:
            tel_id = order_data[0]
            cur.execute("DELETE FROM telefonlar WHERE id = %s", (tel_id,))
            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (order_id,))
            conn.commit()
            st.success("✅ Buyurtma muvaffaqiyatli tasdiqlandi va ombordan o'chirildi!")
            st.balloons() # Bayramona effekt
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Xato: {e}")

# --- ASOSIY INTERFEYS ---
st.sidebar.title("Menyu")
page = st.sidebar.radio("Sahifani tanlang:", ["Foydalanuvchi", "Admin Panel"])

if page == "Foydalanuvchi":
    st.title("📱 Telefon do'koni")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        telefonlar = cur.fetchall()
        
        if telefonlar:
            df = pd.DataFrame(telefonlar, columns=["ID", "Model nomi", "Narxi ($)"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.subheader("🛒 Sotib olish")
            tanlangan_id = st.number_input("Telefon ID sini kiriting:", min_value=1, step=1)
            
            if st.button("Sotib olish so'rovini yuborish"):
                cur.execute("SELECT model, narxi FROM telefonlar WHERE id = %s", (tanlangan_id,))
                res = cur.fetchone()
                if res:
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s) RETURNING id", (tanlangan_id, res[0]))
                    new_order_id = cur.fetchone()[0]
                    conn.commit()
                    
                    xabar = f"🔔 YANGI BUYURTMA!\n\n📱 Model: {res[0]}\n💰 Narxi: {res[1]}$\n🆔 ID: {tanlangan_id}"
                    send_telegram_msg(xabar, new_order_id)
                    st.success("✅ So'rov yuborildi! Adminga Telegramdan xabar ketdi.")
                else:
                    st.error("❌ ID topilmadi!")
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Xato: {e}")

elif page == "Admin Panel":
    st.title("🔐 Admin Panel")
    password = st.text_input("Parol:", type="password")
    if password == "admin777":
        st.write("Bu yerda omborni qo'lda boshqarishingiz mumkin.")
        # Avvalgi admin kodlari (ixtiyoriy ravishda qoldirishingiz mumkin)
