import io
import re
import pdfplumber
from google import genai
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


def sanitizar_mediciones_chison(texto_raw: str) -> str:
    """Fase 1 (Python): Limpia los signos negativos por inversión de polaridad Doppler"""
    texto_limpio = re.sub(r"-(\d+\.?\d*)", r"\1", texto_raw)
    return texto_limpio


def extraer_texto_pdf(file_bytes) -> str:
    texto_completo = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_completo += t + "\n"
    return sanitizar_mediciones_chison(texto_completo)


# PROMPT MAESTRO GOLD STANDARD
PROMPT_GOLD_STANDARD = """
Eres un asistente médico inteligente especializado en ecocardiografía que redacta reportes con el nivel clínico, rigor y estilo exacto del Dr. Diego Ross Álvarez.

TU MISIÓN:
Transformar las mediciones crudas provistas por la consola de ultrasonido en un reporte médico con EXACTAMENTE la misma estructura, densidad de datos, nomenclatura y formato compacto de tu plantilla de referencia.

REGLAS ESTRICTAS:
1. VALORES ABSOLUTOS: Todos los parámetros numéricos deben reportarse obligatoriamente como valores positivos.
2. FIDELIDAD DE DATOS: Utiliza únicamente los parámetros presentes en la entrada. No inventes valores ni asumas mediciones ausentes (ej. si no hay FACVD numérico, no emitas juicios subjetivos sobre el ventrículo derecho sin respaldo).
3. ESTRUCTURA DE SECCIONES Y SALTOS: Separa cada sección claramente con saltos de línea para mantener el orden visual.

---
### EJEMPLO DE REFERENCIA (GOLD STANDARD):

DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: USVALDO JAVIER RIVERO AGUIRRE
EDAD: 35 ANOS | ASC: 2.0 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: levemente dilatada, LAVI 39 mL/m2, diámetro AI 28 mm.
• Auricula derecha: tamaño normal, RAVI 28 mL/m2.
• Ventriculo izquierdo: masa indexada 152 gr/m2, GPR 0.54, movilidad global y segmentaria normal, no dilatado, DDVI 48 mm, SIV 13 mm, PP 12 mm, DSVI 32 mm, VTD 146 ml, VTS 58 ml, fevi simpson modificado 60%, función diastolica normal, onda E 89 cm/s, onda A 62 cm/s, E/A 1.4, TDA 130 ms, E tisular lateral 12 cm/s, E tisular medial 12 cm/s.
• Ventriculo derecho: levemente dilatado, diámetros 41x28x94 mm, función sistólica global y longitudinal normal, Tapse 30 mm, onda s tisular tricúspidea 12.8 cm/s, CAFVD 50%.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, AVM por THP 5.0 cm2, sin gradiente significativo de llenado, sin insuficiencia.
• Valvula tricuspide: morfologia normal, sin valvulopatia, sin gradiente de llenado significativo, velocidad de IT 2 m/s, gradiente 16 mmHg.
• Valvula aortica: sin insuficiencia, sin gradiente de salida significativo. AVAo por continuidad 3.7 cm2, diámetros de la raíz aórtica normal.
• Valvula pulmonar: TSVD prox distal 23 mm, prox 31 mm, TAP 150 ms, sin insuficiencia ni gradiente de salida significativo, presión sistólica pulmonar estimada 20 mmHg.
• Pericardio de aspecto normal. Sin masas o trombos. Cava 18 mm, colapso mas del 50%.

CONCLUSIONES:
1. Función sistólica de ambos ventrículos normal.
2. Función diastólica normal.
3. Sin valvulopatías.
4. Baja probabilidad de hipertensión pulmonar.
5. Hipertrofia miocárdica inducida por ejercicio.

DIAGNOSTICO:
Estudio ecocardiográfico con hipertrofia miocárdica adaptativa; función sistólica y diastólica conservadas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
---

AHORA, PROCESA LOS SIGUIENTES DATOS CRUDOS DEL NUEVO ESTUDIO BAJO ESTE MISMO ESTÁNDAR EXACTO:
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
        alignment=1,  # Centrado
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

    # Inyección del texto (respetando las líneas editadas por el doctor)
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
            with st.spinner("Procesando mediciones y aplicando plantilla..."):
                try:
                    datos_crudos = extraer_texto_pdf(uploaded_file.read())
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            PROMPT_GOLD_STANDARD,
                            f"DATOS CRUDOS DEL NUEVO ESTUDIO:\n{datos_crudos}",
                        ],
                    )
                    st.session_state["reporte_editado"] = response.text
                    st.success("¡Borrador generado con éxito!")
                except Exception as e:
                    st.error(f"Error al generar: {str(e)}")

# MÓDULO DE EDICIÓN MANUAL Y DESCARGA DE PDF OFICIAL
if st.session_state["reporte_editado"]:
    st.markdown("---")
    st.subheader("✏️ Editor Manual del Reporte")
    st.info(
        "Puede modificar cualquier dato, redacción, valor o conclusión antes de"
        " descargar el PDF oficial."
    )

    # Caja de texto para editar libremente
    st.session_state["reporte_editado"] = st.text_area(
        "Modifique el texto del reporte según su criterio clínico:",
        value=st.session_state["reporte_editado"],
        height=350,
    )

    # Botón para compilar el PDF definitivo con ReportLab
    if st.button("📥 Generar y Descargar PDF Oficial"):
        pdf_bytes = generar_pdf_reportlab(st.session_state["reporte_editado"])
        st.download_button(
            label="💾 Descargar PDF de Ecocardiograma",
            data=pdf_bytes,
            file_name="Ecocardiograma_Definitivo_Ross.pdf",
            mime="application/pdf",
        )
