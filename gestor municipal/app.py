import streamlit as st
import pandas as pd
from datetime import date
import json
import os
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestor de Prioridades", layout="wide")

DATA_FILE = "tareas.json"

# --- USUARIOS AUTORIZADOS ---
names = ["Administrador", "Secretaria", "Intendente"]
usernames = ["admin", "secretaria", "intendente"]
passwords = ["1234", "abcd", "municipio"]

authenticator = stauth.Authenticate(
    names,
    usernames,
    passwords,
    "gestor_cookie",
    "clave_ultrasecreta",
    cookie_expiry_days=30
)

# --- LOGIN ---
name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

if authentication_status == False:
    st.error("❌ Usuario o contraseña incorrectos")
elif authentication_status == None:
    st.warning("🔐 Por favor, ingresa tus credenciales")

# --- SOLO SI ESTÁ LOGUEADO ---
if authentication_status:

    authenticator.logout("Cerrar sesión", "sidebar")

    st.title("📋 Gestor de Prioridades Municipales")
    st.caption(f"👤 Sesión iniciada como: {name}")

    # --- FUNCIONES ---
    def cargar_tareas():
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def guardar_tareas():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.tasks, f, ensure_ascii=False, indent=2)

    # --- INICIALIZACIÓN ---
    if "tasks" not in st.session_state:
        st.session_state.tasks = cargar_tareas()

    if "categories" not in st.session_state:
        st.session_state.categories = {
            "obras": {"name": "Obras Públicas"},
            "social": {"name": "Desarrollo Social"},
            "seguridad": {"name": "Seguridad"},
            "educacion": {"name": "Educación"},
            "salud": {"name": "Salud"},
            "admin": {"name": "Administrativo"},
            "concejo": {"name": "Concejo Municipal"},
            "otro": {"name": "Otro"},
        }

    priorities = {
        "urgente": "🔴 Urgente (Hoy)",
        "importante": "🟠 Importante (Esta Semana)",
        "planificar": "🟡 Planificar (Este Mes)",
        "largo_plazo": "🟢 Largo Plazo",
    }

    # --- TAREAS URGENTES ---
    tareas_urgentes = [t for t in st.session_state.tasks if t["priority"] == "urgente" and not t["completed"]]
    if tareas_urgentes:
        st.warning(f"⚠️ Tienes {len(tareas_urgentes)} tarea(s) URGENTE(S) pendiente(s)!")
        for t in tareas_urgentes:
            st.markdown(f"🔴 **{t['title']}** — Responsable: {t['responsible'] or 'No asignado'} — Límite: {t['deadline']}")

    # --- PANEL LATERAL ---
    st.sidebar.header("➕ Agregar nueva tarea")

    title = st.sidebar.text_input("Título de la tarea")
    category = st.sidebar.selectbox("Categoría", list(st.session_state.categories.keys()))
    priority = st.sidebar.selectbox("Prioridad", list(priorities.keys()))
    responsible = st.sidebar.text_input("Responsable")
    deadline = st.sidebar.date_input("Fecha límite", date.today())
    notes = st.sidebar.text_area("Notas adicionales")

    if st.sidebar.button("Agregar tarea"):
        if title.strip():
            new_task = {
                "id": len(st.session_state.tasks) + 1,
                "title": title,
                "category": category,
                "priority": priority,
                "responsible": responsible,
                "deadline": str(deadline),
                "completed": False,
                "notes": notes,
            }
            st.session_state.tasks.append(new_task)
            guardar_tareas()
            st.sidebar.success("✅ Tarea agregada correctamente")
            st.toast("Tarea agregada ✅")
        else:
            st.sidebar.warning("⚠️ Debes ingresar un título.")

    # --- FILTROS ---
    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)
    with col1:
        filter_cat = st.selectbox("Filtrar por categoría", ["todas"] + list(st.session_state.categories.keys()))
    with col2:
        filter_pri = st.selectbox("Filtrar por prioridad", ["todas"] + list(priorities.keys()))

    filtered = [
        t for t in st.session_state.tasks
        if (filter_cat == "todas" or t["category"] == filter_cat)
        and (filter_pri == "todas" or t["priority"] == filter_pri)
    ]

    # --- LISTA DE TAREAS ---
    st.subheader("📌 Lista de tareas")

    if not filtered:
        st.info("No hay tareas registradas o coincidentes con el filtro.")
    else:
        for t in filtered:
            color = (
                "🟥" if t["priority"] == "urgente"
                else "🟧" if t["priority"] == "importante"
                else "🟨" if t["priority"] == "planificar"
                else "🟩"
            )
            estado = "✅ Completada" if t["completed"] else "⏳ Pendiente"

            with st.expander(f"{color} {t['title']} — {estado}", expanded=False, key=f"exp_{t['id']}"):
                st.markdown(f"**Categoría:** {st.session_state.categories[t['category']]['name']}")
                st.markdown(f"**Responsable:** {t['responsible'] or 'No asignado'}")
                st.markdown(f"**Fecha límite:** {t['deadline']}")
                st.markdown(f"**Notas:** {t['notes'] or '-'}")

                col1, col2 = st.columns(2)
                with col1:
                    if not t["completed"]:
                        if st.button(f"✅ Completar", key=f"done_{t['id']}"):
                            t["completed"] = True
                            guardar_tareas()
                            st.toast(f"Tarea '{t['title']}' completada ✅")
                            st.experimental_rerun()
                with col2:
                    if st.button(f"🗑️ Eliminar", key=f"del_{t['id']}"):
                        st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != t["id"]]
                        guardar_tareas()
                        st.toast(f"Tarea '{t['title']}' eliminada 🗑️")
                        st.experimental_rerun()

    # --- EXPORTAR ---
    if st.button("📤 Exportar a CSV"):
        if st.session_state.tasks:
            df = pd.DataFrame(st.session_state.tasks)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar archivo CSV", csv, "tareas.csv", "text/csv")
        else:
            st.warning("No hay tareas para exportar.")

