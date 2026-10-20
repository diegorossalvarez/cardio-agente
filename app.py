import io
import pdfplumber
from google import genai
from google.genai import types
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. Configuración de la Interfaz
st.set_page_config(
    page_title="CardioAgente - Dr. Diego Ross Álvarez", layout="wide"
)

st.title("CardioAgente - Generador de Ecocardiogramas")
st.subheader("Dr. Diego Ross Álvarez | Cardiólogo - Electrofisiólogo")

api_key = st.sidebar.text_input("Gemini API Key", type="password")


def extraer_texto_pdf(file_bytes) -> str:
    """Extrae el texto completo del PDF de la consola Chison limpiamente."""
    texto_completo = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_completo += t + "\n"
    return texto_completo


# PROMPT MÉDICO CLINICAMENTE BLINDADO (CERO ALUCINACIONES)
PROMPT_MEDICO_BLINDADO = """
Eres un asistente médico especializado en ecocardiografía estricta que redacta reportes clínicos para el Dr. Diego Ross Álvarez.

MISIÓN:
Analizar las mediciones ecocardiográficas extraídas de la consola de ultrasonido y generar un informe bien estructurado, ordenado y clínicamente preciso.

REGLAS CLÍNICAS ESTRICTAS DE CERO SUPOSICIÓN:
1. VALORES ABSOLUTOS: Interpreta velocidades, gradientes y tiempos como valores absolutos si provienen de inversiones del espectro Doppler.
2. FIDELIDAD ABSOLUTA DE DATOS (CRÍTICO): Utiliza EXCLUSIVAMENTE las mediciones presentes en el texto recibido. 
   - PROHIBIDO emitir juicios cualitativos sobre el Ventrículo Derecho (ej. decir "función sistólica del VD disminuida o deprimida") a menos que poseas el valor cuantitativo explícito en el texto (como FACVD o onda s' tisular). Si solo tienes TAPSE, reporta únicamente el valor del TAPSE sin calificar globalmente la función del VD si no hay sustento matemático.
   - Si un parámetro no existe en los datos crudos, omítelo por completo; nunca asumas ni inventes hallazgos.
3. ESTRUCTURA DEL INFORME:
   Organiza el reporte obligatoriamente en las siguientes secciones separadas por saltos de línea:
   - DATOS DEL PACIENTE (Nombre, Edad, ASC)
   - ECOCARDIOGRAMA TRANSTORÁCICO (Texto descriptivo ordenado por cavidades: Aurícula Izquierda, Aurícula Derecha, Ventrículo Izquierdo, Ventrículo Derecho, Válvulas Mitral/Aórtica/Tricúspide/Pulmonar, Pericardio y Cava Inferior).
   - CONCLUSIONES (Puntos numerados objetivos basados estrictamente en las mediciones).
   - DIAGNÓSTICO INTEGRATIVO.

ESTILO Y FIRMA:
Al final del informe incluye obligatoriamente la firma institucional:
DR ROSS ALVAREZ DIEGO
Cardiólogo Clínico | Cédula 12883155 | Avalado por la UNAM
Electrofisiólogo egresado CMN 20 de Noviembre
9812438407
"""


# Función para generar el PDF formal con ReportLab
def generar_pdf_reportlab(texto_reporte: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    color_primario = colors.HexColor("#1A365D")  # Azul marino médico
    color_secundario = colors.HexColor("#2B6CB0")

    estilo_encabezado = ParagraphStyle(
        "EncabezadoClinica",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=color_primario,
        alignment=1,
    )

    estilo_cuerpo = ParagraphStyle(
        "CuerpoReporte",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
    )

    # Membrete institucional fijo
    story.append(Paragraph("<b>DR. DIEGO ROSS ÁLVAREZ</b>", estilo_encabezado))
    story.append(
        Paragraph(
            "Cardiólogo - Electrofisiólogo | Especialidad UNAM 12883155",
            estilo_encabezado,
        )
    )
    story.append(
        Paragraph(
            "WhatsApp: 9812438407 | Consultorio: Zenzontle 110, Fracc. La Ceiba,"
            " Villahermosa, Tabasco",
            ParagraphStyle(
                "Sub", parent=estilo_encabezado, fontSize=8.5, textColor=color_secundario
            ),
        )
    )
    story.append(Spacer(1, 10))

    # Inyección del texto
    for linea in texto_reporte.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea, estilo_cuerpo))
            story.append(Spacer(1, 3))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# Inicializar estado en sesión para la edición
if "reporte_editado" not in st.session_state:
    st.session_state["reporte_editado"] = ""

# Interfaz de carga
uploaded_file = st.file_uploader(
    "Cargar archivo PDF de mediciones del ecógrafo", type=["pdf"]
)

if uploaded_file is not None:
    st.success(f"Archivo cargado correctamente: {uploaded_file.name}")

    if not api_key:
        st.warning("Por favor, ingrese su Gemini API Key en el panel lateral.")
    else:
        if st.button("🚀 Generar Borrador con IA"):
            with st.spinner("Procesando mediciones y aplicando filtros clínicos..."):
                try:
                    datos_crudos = extraer_texto_pdf(uploaded_file.read())
                    client = genai.Client(api_key=api_key)

                    # Configuración estricta de temperatura (Cero creatividad, total apego a datos)
                    config_gen = types.GenerateContentConfig(
                        temperature=0.0
                    )

                    # Llamada con fallback automático entre modelos flash para máxima robustez
                    response = None
                    try:
                        modelos = [
    "gemini-3.8-flash",
    "gemini-3.0-flash",
]

response = None

for modelo in modelos:
    try:
        response = client.models.generate_content(
            model=modelo,
            contents=[
                PROMPT_MEDICO,
                f"DATOS CRUDOS EXTRAÍDOS DEL PDF:\n{datos_crudos}",
            ],
            config=config_gen,
        )
        break

    except Exception as e:
        if "503" in str(e):
            continue
        raise

if response is None:
    raise Exception(
        "Gemini se encuentra temporalmente saturado. Intente nuevamente en unos minutos."
    )

                    except Exception:
                        # Fallback automático a gemini-2.5-flash o alternativo si se satura
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[
                                PROMPT_MEDICO_BLINDADO,
                                f"DATOS CRUDOS EXTRAÍDOS DEL PDF:\n{datos_crudos}",
                            ],
                            config=config_gen,
                        )

                    st.session_state["reporte_editado"] = response.text
                    st.success("¡Borrador generado con éxito!")
                except Exception as e:
                    st.error(f"Error al generar el reporte: {str(e)}")

# MÓDULO DE EDICIÓN MANUAL Y DESCARGA DE PDF OFICIAL
if st.session_state["reporte_editado"]:
    st.markdown("---")
    st.subheader("✏️ Editor Manual del Reporte")
    st.info(
        "Verifique los datos clínicos. Puede modificar cualquier valor, redacción"
        " o conclusión antes de descargar el PDF oficial."
    )

    st.session_state["reporte_editado"] = st.text_area(
        "Modifique el texto del reporte según su criterio médico:",
        value=st.session_state["reporte_editado"],
        height=350,
    )

    if st.button("📥 Generar y Descargar PDF Oficial"):
        pdf_bytes = generar_pdf_reportlab(st.session_state["reporte_editado"])
        st.download_button(
            label="💾 Descargar PDF de Ecocardiograma",
            data=pdf_bytes,
            file_name="Ecocardiograma_Definitivo_Ross.pdf",
            mime="application/pdf",
        )
11
