import streamlit as st
import psycopg2

def get_connection():
    return psycopg2.connect(psql 'postgresql://neondb_owner:npg_FSj8WaqM7udA@ep-plain-block-ahq7shct-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require' )

# Ma'lumotni bazaga yuborish va inputlarni tozalash funksiyasi
def saqlash_va_tozalash():
    model = st.session_state.model_input
    narx = st.session_state.narx_input
    
    if model and narx:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO telefonlar (model, narxi) VALUES (%s, %s)", (model, narx))
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"✅ {model} muvaffaqiyatli qo'shildi!")
            
            # Inputlarni tozalash
            st.session_state.model_input = ""
            st.session_state.narx_input = 0
        except Exception as e:
            st.error(f"Xato yuz berdi: {e}")
    else:
        st.warning("Iltimos, hamma maydonlarni to'ldiring!")

st.title("📱 Telefonlar Ombori")

# Inputlarni session_state orqali bog'laymiz
st.text_input("Smartfon modeli:", key="model_input")
st.number_input("Narxi ($):", min_value=0, key="narx_input")

st.button("Baza (pgAdmin4) ga yuborish", on_click=saqlash_va_tozalash)

