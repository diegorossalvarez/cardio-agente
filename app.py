import io
import pdfplumber
from google import genai
from google.genai import types
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from ejemplos_ross import (
    EJEMPLO_NORMAL,
    EJEMPLO_REMODELADO,
    EJEMPLO_FEVI_DEPRIMIDA,
)

# 1. Configuración de la Interfaz
st.set_page_config(
    page_title="CardioAgente - Dr. Diego Ross Álvarez", layout="wide"
)

st.title("CardioAgente - Generador de Ecocardiogramas")
st.subheader("Dr. Diego Ross Álvarez | Cardiólogo - Electrofisiólogo")

api_key = st.sidebar.text_input("Gemini API Key", type="password")


def extraer_texto_pdf(file_bytes) -> str:
    texto_completo = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_completo += t + "\n"
    return texto_completo


# PROMPT MAESTRO CON TRES EJEMPLOS Y JERARQUÍA ESTRICTA
PROMPT_MEDICO_MAESTRO = f"""
Eres un asistente médico especializado en ecocardiografía que redacta exclusivamente con el estilo, tono y formato técnico del Dr. Diego Ross Álvarez.

DIRECTRICES DE SECUENCIA Y ESTILO OBLIGATORIAS:
1. ORDEN ANATÓMICO Y JERÁRQUICO ESTRICTO EN CAVIDADES: Al describir los ventrículos, sigue obligatoriamente este orden: 
   1.° Geometría y patrón. 
   2.° Diámetros y dimensiones. 
   3.° Movilidad y contractilidad. 
   4.° Función sistólica. 
   5.° Función diastólica.
2. ORDEN ESTRICTO EN CONCLUSIONES: Las conclusiones numéricas deben seguir indefectiblemente esta secuencia:
   1. Geometría
   2. Dimensiones
   3. Función sistólica de ambos ventrículos
   4. Función diastólica
   5. Valvulopatías
   6. Probabilidad de hipertensión pulmonar
   7. Alteraciones de la movilidad
3. TONO SECO Y DIRECTO: Sin introducciones largas, florituras literarias o frases de IA (como "es importante destacar"). Ve directo al dato clínico.
4. CERO INFERENCIAS DE ETIOLOGÍA: Prohibido asumir etiologías si no están explícitas en los datos crudos.

---
EJEMPLOS DE REFERENCIA DE TU ESTILO Y SECUENCIA:

CASO 1 (NORMAL):
{EJEMPLO_NORMAL}

CASO 2 (REMODELADO):
{EJEMPLO_REMODELADO}

CASO 3 (FEVI DEPRIMIDA):
{EJEMPLO_FEVI_DEPRIMIDA}
---

AHORA, PROCESA LOS SIGUIENTES DATOS CRUDOS BAJO ESTE MISMO ESTÁNDAR EXACTO:
"""


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

    color_primario = colors.HexColor("#1A365D")
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

    for linea in texto_reporte.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea, estilo_cuerpo))
            story.append(Spacer(1, 3))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


if "reporte_editado" not in st.session_state:
    st.session_state["reporte_editado"] = ""

uploaded_file = st.file_uploader(
    "Cargar archivo PDF de mediciones del ecógrafo", type=["pdf"]
)

if uploaded_file is not None:
    st.success(f"Archivo cargado correctamente: {uploaded_file.name}")

    if not api_key:
        st.warning("Por favor, ingrese su Gemini API Key en el panel lateral.")
    else:
        if st.button("🚀 Generar Borrador con IA"):
            with st.spinner("Procesando mediciones con criterio clínico de Diego Ross..."):
                try:
                    datos_crudos = extraer_texto_pdf(uploaded_file.read())
                    client = genai.Client(api_key=api_key)
                    config_gen = types.GenerateContentConfig(temperature=0.0)

                    modelos = ["gemini-3.8-flash", "gemini-3.0-flash"]
                    response = None

                    for modelo in modelos:
                        try:
                            response = client.models.generate_content(
                                model=modelo,
                                contents=[
                                    PROMPT_MEDICO_MAESTRO,
                                    f"DATOS CRUDOS EXTRAÍDOS DEL PDF:\n{datos_crudos}",
                                ],
                                config=config_gen,
                            )
                            break
                        except Exception as e:
                            if "503" in str(e) or "404" in str(e):
                                continue
                            raise

                    if response is None:
                        raise Exception(
                            "Gemini se encuentra temporalmente saturado. Intente nuevamente."
                        )

                    st.session_state["reporte_editado"] = response.text
                    st.success("¡Borrador generado con éxito!")
                except Exception as e:
                    st.error(f"Error al generar el reporte: {str(e)}")

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
