import streamlit as st
import psycopg2
import pandas as pd

# 1. Bazaga ulanish funksiyasi
def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# Sidebar navigatsiya
st.sidebar.title("Menyu")
page = st.sidebar.radio("Sahifani tanlang:", ["Foydalanuvchi", "Admin Panel"])

# --- FOYDALANUVCHI SAHIFASI ---
if page == "Foydalanuvchi":
    st.title("📱 Telefon do'koni")
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Ombordagi telefonlarni olish
        cur.execute("SELECT id, model, narxi FROM telefonlar ORDER BY id DESC")
        telefonlar = cur.fetchall()
        
        if telefonlar:
            st.subheader("Mavjud telefonlar ro'yxati")
            df = pd.DataFrame(telefonlar, columns=["ID", "Model nomi", "Narxi ($)"])
            
            # Jadvalni 0, 1, 2 raqamlarsiz (indexsiz) chiqarish
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.write("---")
            st.subheader("🛒 Sotib olish")
            tanlangan_id = st.number_input("Sotib olmoqchi bo'lgan telefon ID sini kiriting:", min_value=1, step=1)
            
            if st.button("Sotib olish so'rovini yuborish"):
                cur.execute("SELECT model FROM telefonlar WHERE id = %s", (tanlangan_id,))
                res = cur.fetchone()
                if res:
                    # Buyurtmalar jadvaliga yozish
                    cur.execute("INSERT INTO buyurtmalar (telefon_id, model) VALUES (%s, %s)", (tanlangan_id, res[0]))
                    conn.commit()
                    st.success(f"✅ {res[0]} uchun so'rov yuborildi! Admin tasdiqlashini kuting.")
                else:
                    st.error("❌ Bunday ID dagi telefon topilmadi!")
        else:
            st.info("Hozircha ombor bo'sh.")
        
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
        tab1, tab2 = st.tabs(["🆕 Yangi telefon qo'shish", "📑 Buyurtmalarni boshqarish"])
        
        with tab1:
            model_nomi = st.text_input("Telefon modeli:")
            narxi = st.number_input("Narxi ($):", min_value=0, step=10)
            if st.button("Omborga qo'shish"):
                if model_nomi:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (model_nomi, narxi))
                    conn.commit()
                    st.success(f"{model_nomi} omborga qo'shildi!")
                    cur.close()
                    conn.close()
                else:
                    st.warning("Model nomini kiriting!")

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
                            # Ombordan o'chirish
                            cur.execute("DELETE FROM telefonlar WHERE id = %s", (order[1],))
                            # Buyurtmani yopish
                            cur.execute("UPDATE buyurtmalar SET holat = 'Sotildi' WHERE id = %s", (order[0],))
                            conn.commit()
                            st.rerun()
            else:
                st.write("Hozircha yangi buyurtmalar yo'q.")
            cur.close()
            conn.close()
    
    elif password != "":
        st.error("Parol noto'g'ri!")
