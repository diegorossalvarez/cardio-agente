import io
import pdfplumber
from google import genai
from google.genai import types
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Importamos la nueva matriz limpia
from ejemplos_ross_v2 import (
    EJEMPLO_1_NORMAL,
    EJEMPLO_2_HIPERTROFIA,
    EJEMPLO_3_FEVI_DEPRIMIDA,
    EJEMPLO_4_VALVULOPATIA,
    EJEMPLO_5_HAP,
    EJEMPLO_6_CONGENITA,
    EJEMPLO_7_PROTESIS,
)

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


PROMPT_MEDICO_MAESTRO = f"""
REGLA CRÍTICA ABSOLUTA:
Cada afirmación, número, medición o hallazgo presente en el reporte DEBE DERIVAR DIRECTAMENTE DE LOS DATOS DE ENTRADA.
Si un dato no aparece en la entrada, NO DEBE APARECER EN LA SALIDA.
Está estrictamente prohibido inventar o inferir: dimensiones, volúmenes, áreas, masas, trombos, derrames, parámetros del VD, parámetros de las aurículas, parámetros valvulares, etiología o diagnósticos clínicos no expresamente proporcionados.

REGLA DE PROHIBICIÓN DE DIAGNÓSTICOS ETIOLÓGICOS:
Queda estrictamente prohibido diagnosticar o escribir en el reporte:
- Miocardiopatía dilatada
- Cardiopatía hipertensiva
- Cardiopatía isquémica
- Enfermedad degenerativa
- Origen reumático
- Etiología congénita
salvo que dichas palabras exactas o diagnósticos explícitos aparezcan expresamente en los datos de entrada.

REGLA DE AUSENCIA:
Si una estructura no fue evaluada o no aparecen datos de ella en la entrada: NO MENCIONARLA.
Ejemplo: Si no existen datos del ventrículo derecho, NO escribir "Ventrículo derecho normal". Simplemente omitir el punto o viñeta correspondiente.

DIRECTRICES DE SECUENCIA Y ESTILO OBLIGATORIAS:
1. ORDEN ANATÓMICO Y JERÁRQUICO ESTRICTO EN CAVIDADES: Al describir los ventrículos presentes, sigue este orden:
   1.° Geometría y patrón. 
   2.° Diámetros y dimensiones. 
   3.° Movilidad y contractilidad. 
   4.° Función sistólica. 
   5.° Función diastólica.
2. ORDEN ESTRICTO EN CONCLUSIONES (Solo incluir puntos correspondientes a estructuras evaluadas):
   1. Geometría
   2. Dimensiones
   3. Función sistólica de ambos ventrículos (o del ventrículo evaluado)
   4. Función diastólica
   5. Valvulopatías
   6. Probabilidad de hipertensión pulmonar
   7. Alteraciones de la movilidad
3. TONO SECO Y DIRECTO: Sin introducciones largas ni frases de rellenado.
4. NOMENCLATURA Y UNIDADES:
   - Usa "Gradiente de IT" en lugar de "Gradiente AD-VD".
   - Conclusiones de hipertensión pulmonar exclusivamente en términos de probabilidad (ej. "Baja probabilidad de hipertensión pulmonar", "Alta probabilidad de hipertensión pulmonar").
   - El aplanamiento del septum es un parámetro cualitativo que va en la descripción/geometría del ventrículo, NUNCA como punto independiente en las conclusiones.

---
MATRIZ DE ENTRENAMIENTO (ENTRADA Y SALIDA EXPERTA RASTREABLE 1:1):

CASO 1 (NORMAL):
{EJEMPLO_1_NORMAL}

CASO 2 (HIPERTROFIA / REMODELADO):
{EJEMPLO_2_HIPERTROFIA}

CASO 3 (FEVI DEPRIMIDA / TRASTORNO SEGMENTARIO):
{EJEMPLO_3_FEVI_DEPRIMIDA}

CASO 4 (VALVULOPATÍA SEVERA):
{EJEMPLO_4_VALVULOPATIA}

CASO 5 (HIPERTENSIÓN PULMONAR / REPERCUSIÓN DERECHA):
{EJEMPLO_5_HAP}

CASO 6 (CARDIOPATÍA CONGÉNITA CON SHUNT):
{EJEMPLO_6_CONGENITA}

CASO 7 (PRÓTESIS VALVULAR):
{EJEMPLO_7_PROTESIS}
---

AHORA, PROCESA LOS SIGUIENTES DATOS CRUDOS APLICANDO ESTRICTAMENTE LAS REGLAS DE FIDELIDAD Y AUSENCIA (SIN INVENTAR NINGÚN DATO QUE NO ESTÉ ABAJO):
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
