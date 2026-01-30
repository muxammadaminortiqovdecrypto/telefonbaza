import streamlit as st
import psycopg2
import pandas as pd

def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

st.sidebar.title("Navigatsiya")
page = st.sidebar.radio("Sahifani tanlang:", ["Foydalanuvchi", "Admin Panel"])

# --- FOYDALANUVCHI SAHIFASI ---
if page == "Foydalanuvchi":
    st.title("🛒 Telefon do'koni")
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
    telefonlar = cur.fetchall()
    
    if telefonlar:
        df = pd.DataFrame(telefonlar, columns=["ID", "Model", "Narxi ($)"])
        st.table(df)
        
        # Sotib olish bo'limi
        st.subheader("Sotib olish")
        tanlangan_id = st.number_input("Sotib olmoqchi bo'lgan telefon ID sini kiriting:", min_value=1)
        
        if st.button("Sotib olish so'rovini yuborish"):
            cur.execute("SELECT model FROM telefonlar WHERE id = %s", (tanlangan_id,))
            res = cur.fetchone()
            if res:
                cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s)", (tanlangan_id, res[0]))
                conn.commit()
                st.success(f"{res[0]} uchun so'rov yuborildi. Admin tasdiqlashini kuting.")
            else:
                st.error("Bunday ID dagi telefon topilmadi!")
    else:
        st.info("Ombor bo'sh.")
    cur.close()
    conn.close()

# --- ADMIN PANEL SAHIFASI ---
elif page == "Admin Panel":
    st.title("🔐 Admin Boshqaruvi")
    password = st.text_input("Admin parolini kiriting:", type="password")
    
    if password == "admin777":
        tab1, tab2 = st.tabs(["Yangi qo'shish", "Buyurtmalarni tasdiqlash"])
        
        with tab1:
            st.subheader("Yangi telefon qo'shish")
            model = st.text_input("Model:")
            narxi = st.number_input("Narxi ($):", min_value=0)
            if st.button("Qo'shish"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (model, narxi))
                conn.commit()
                st.success("Qo'shildi!")
                cur.close()
                conn.close()

        with tab2:
            st.subheader("Kutilayotgan buyurtmalar")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, telefon_id, model FROM buyurtmalar WHERE holat = 'Kutilmoqda'")
            orders = cur.fetchall()
            
            if orders:
                for order in orders:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"ID: {order[1]} | Model: {order[2]}")
                    if col2.button("Tasdiqlash", key=order[0]):
                        # 1. Asosiy ombordan o'chirish
                        cur.execute("DELETE FROM telefonlar WHERE id = %s", (order[1],))
                        # 2. Buyurtma holatini yangilash
                        cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (order[0],))
                        conn.commit()
                        st.experimental_rerun()
            else:
                st.write("Yangi buyurtmalar yo'q.")
            cur.close()
            conn.close()
