import streamlit as st
import psycopg2

# 1. Bazaga ulanish funksiyasi
def get_connection():
    return psycopg2.connect('postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

st.title("📱 Telefonlar Ombori")

# 2. Ma'lumot kiritish qismi
st.subheader("Yangi telefon qo'shish")
model = st.text_input("Smartfon modeli:")
narxi = st.number_input("Narxi ($):", min_value=0)

if st.button("Baza (Neon) ga yuborish"):
    if model and narxi:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (model, narxi))
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"{model} muvaffaqiyatli saqlandi!")
        except Exception as e:
            st.error(f"Xato yuz berdi: {e}")
    else:
        st.warning("Iltimos, barcha maydonlarni toldiring!")

# 3. Ombor tugmasi va jadvalni ko'rsatish
st.write("---")
if st.button("Omborni ko'rish"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT model, narxi FROM telefonlar ORDER BY id DESC")
        malumotlar = cur.fetchall()
        
        if malumotlar:
            st.subheader("Ombordagi mavjud telefonlar:")
            st.table(malumotlar)
        else:
            st.info("Ombor hozircha bo'sh.")
            
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Ma'lumotni yuklashda xato: {e}")
