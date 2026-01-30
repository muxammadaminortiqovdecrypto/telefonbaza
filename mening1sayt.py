import streamlit as st
import psycopg2
import pandas as pd
import requests

# 1. TELEGRAM SOZLAMALARI (O'zingiznikini kiriting)
TG_TOKEN = "8442153084:AAEftF3_JykYzbWdymcrjArZ8ceP6c-qgfE"
TG_CHAT_ID = "1685342390"

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Telegram xabarnoma yuborishda xato: {e}")

# 2. BAZAGA ULANISH
def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

st.sidebar.title("Menyu")
page = st.sidebar.radio("Sahifani tanlang:", ["Foydalanuvchi", "Admin Panel"])

# --- FOYDALANUVCHI SAHIFASI ---
if page == "Foydalanuvchi":
    st.title("📱 Telefon do'koni")
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        telefonlar = cur.fetchall()
        
        if telefonlar:
            st.subheader("Mavjud telefonlar")
            df = pd.DataFrame(telefonlar, columns=["ID", "Model nomi", "Narxi ($)"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.write("---")
            st.subheader("🛒 Sotib olish")
            tanlangan_id = st.number_input("Telefon ID sini kiriting:", min_value=1, step=1)
            
            if st.button("Sotib olish so'rovini yuborish"):
                cur.execute("SELECT model, narxi FROM telefonlar WHERE id = %s", (tanlangan_id,))
                res = cur.fetchone()
                if res:
                    # Bazaga buyurtmani yozish
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s)", (tanlangan_id, res[0]))
                    conn.commit()
                    
                    # TELEGRAMGA XABAR YUBORISH
                    xabar = f"🔔 YANGI BUYURTMA!\n\n📱 Model: {res[0]}\n💰 Narxi: {res[1]}$\n🆔 ID: {tanlangan_id}\n\nAdmin panelga kirib tasdiqlang!"
                    send_telegram_msg(xabar)
                    
                    st.success(f"✅ {res[0]} uchun so'rov yuborildi va Adminga Telegram orqali xabar berildi!")
                else:
                    st.error("❌ Bunday ID dagi telefon topilmadi!")
        else:
            st.info("Ombor hozircha bo'sh.")
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Xato yuz berdi: {e}")

# --- ADMIN PANEL SAHIFASI ---
elif page == "Admin Panel":
    st.title("🔐 Admin boshqaruv paneli")
    password = st.text_input("Admin parolini kiriting:", type="password")
    
    if password == "admin777":
        st.success("Xush kelibsiz, Admin!")
        tab1, tab2 = st.tabs(["🆕 Yangi qo'shish", "📑 Buyurtmalarni boshqarish"])
        
        with tab1:
            model_nomi = st.text_input("Telefon modeli:")
            narxi_val = st.number_input("Narxi ($):", min_value=0, step=10)
            if st.button("Omborga qo'shish"):
                if model_nomi:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (model_nomi, narxi_val))
                    conn.commit()
                    st.success(f"{model_nomi} omborga qo'shildi!")
                    cur.close()
                    conn.close()
                    st.rerun()

        with tab2:
            st.subheader("Kutilayotgan buyurtmalar")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, telefon_id, model FROM buyurtmalar WHERE holat = 'Kutilmoqda'")
            orders = cur.fetchall()
            
            if orders:
                for order in orders:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"🆔 ID: {order[1]} | 📱 Model: {order[2]}")
                    with col2:
                        if st.button("Tasdiqlash", key=f"btn_{order[0]}"):
                            cur.execute("DELETE FROM telefonlar WHERE id = %s", (order[1],))
                            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (order[0],))
                            conn.commit()
                            st.rerun()
            else:
                st.write("Hozircha yangi buyurtmalar yo'q.")
            cur.close()
            conn.close()
    elif password != "":
        st.error("Parol noto'g'ri!")
