import streamlit as st
import pandas as pd
from datetime import date
import json
import os

st.set_page_config(page_title="Gestor de Prioridades", layout="wide")

# --- ARCHIVO DE GUARDADO ---
DATA_FILE = "tareas.json"

# --- Funciones auxiliares ---
def cargar_tareas():
    """Carga las tareas desde un archivo JSON (si existe)."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_tareas():
    """Guarda las tareas actuales en un archivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.tasks, f, ensure_ascii=False, indent=2)

# --- Inicialización de datos ---
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

# --- Título principal ---
st.title("📋 Gestor de Prioridades Municipales")

# --- Aviso de tareas urgentes ---
tareas_urgentes = [t for t in st.session_state.tasks if t["priority"] == "urgente" and not t["completed"]]
if tareas_urgentes:
    st.warning(f"⚠️ Tienes {len(tareas_urgentes)} tarea(s) URGENTE(S) pendiente(s)!")
    for t in tareas_urgentes:
        st.markdown(f"🔴 **{t['title']}** — Responsable: {t['responsible'] or 'No asignado'} — Límite: {t['deadline']}")

# --- Panel lateral para agregar tarea ---
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
        st.rerun()
    else:
        st.sidebar.warning("⚠️ Debes ingresar un título.")

# --- Filtros ---
st.subheader("🔍 Filtros")
col1, col2 = st.columns(2)
with col1:
    filter_cat = st.selectbox(
        "Filtrar por categoría", ["todas"] + list(st.session_state.categories.keys())
    )
with col2:
    filter_pri = st.selectbox(
        "Filtrar por prioridad", ["todas"] + list(priorities.keys())
    )

# --- Aplicar filtros ---
filtered = [
    t
    for t in st.session_state.tasks
    if (filter_cat == "todas" or t["category"] == filter_cat)
    and (filter_pri == "todas" or t["priority"] == filter_pri)
]

# --- Mostrar tareas ---
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
        with st.expander(f"{color} {t['title']} — {estado}"):
            st.markdown(f"**Categoría:** {st.session_state.categories[t['category']]['name']}")
            st.markdown(f"**Responsable:** {t['responsible'] or 'No asignado'}")
            st.markdown(f"**Fecha límite:** {t['deadline']}")
            st.markdown(f"**Notas:** {t['notes'] or '-'}")

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button(f"✅ Completar {t['id']}", key=f"done_{t['id']}"):
                    t["completed"] = True
                    guardar_tareas()
                    st.success(f"Tarea '{t['title']}' marcada como completada.")
                    st.rerun()
            with cols[1]:
                if st.button(f"🗑️ Eliminar {t['id']}", key=f"del_{t['id']}"):
                    st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != t["id"]]
                    guardar_tareas()
                    st.warning(f"Tarea '{t['title']}' eliminada.")
                    st.rerun()

# --- Exportar CSV ---
if st.button("📤 Exportar a CSV"):
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar archivo CSV", csv, "tareas.csv", "text/csv")
    else:
        st.warning("No hay tareas para exportar.")
