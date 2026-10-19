import io
import re
import pdfplumber
from google import genai
import streamlit as st

# Configuración de la interfaz en Streamlit
st.set_page_config(
    page_title="CardioAgente - Dr. Diego Ross Álvarez", layout="wide"
)

st.title("CardioAgente - Generador de Ecocardiogramas")
st.subheader("Dr. Diego Ross Álvarez | Cardiólogo - Electrofisiólogo")

# Campo para la API Key en la barra lateral
api_key = st.sidebar.text_input("Gemini API Key", type="password")


def sanitizar_mediciones_chison(texto_raw: str) -> str:
    """Fase 1 (Python): Limpia los signos negativos por inversión de polaridad Doppler

    (ej. -0.06 s -> 0.06 s, -95.87 cm/s -> 95.87 cm/s) para asegurar valores absolutos.
    """
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


# PROMPT MAESTRO CON EJEMPLO REAL DE SU PRÁCTICA (GOLD STANDARD)
PROMPT_GOLD_STANDARD = """
Eres un asistente médico inteligente especializado en ecocardiografía que redacta reportes con el nivel clínico, rigor y estilo exacto del Dr. Diego Ross Álvarez.

TU MISIÓN:
Transformar las mediciones crudas provistas por la consola de ultrasonido en un reporte médico con EXACTAMENTE la misma estructura, densidad de datos, nomenclatura y formato compacto de tu plantilla de referencia.

REGLAS ESTRICTAS:
1. VALORES ABSOLUTOS: Todos los parámetros numéricos (THP, AVM, velocidades) deben reportarse obligatoriamente como valores positivos.
2. FIDELIDAD DE DATOS: Utiliza únicamente los parámetros presentes en la entrada. No inventes valores ni asumas mediciones ausentes.
3. ESTRUCTURA DE 8 SECCIONES: Mantén el formato de viñetas por cavidad/válvula, seguido de conclusiones numéricas y el diagnóstico integrativo.

---
### EJEMPLO DE REFERENCIA (GOLD STANDARD - TUS REPORTES REALES):

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

# Interfaz para cargar el PDF del ecógrafo
uploaded_file = st.file_uploader(
    "Cargar archivo",
    type=None
)

if uploaded_file is not None:
    st.write("ARCHIVO RECIBIDO")
    st.write(uploaded_file.name)
    st.write(uploaded_file.type)
    st.write(uploaded_file.size)
# Procesamiento automático o manual visible
if uploaded_file:
    st.success(f"Archivo cargado correctamente: {uploaded_file.name}")

    if not api_key:
        st.warning(
            "Por favor, ingrese su Gemini API Key en el panel lateral izquierdo para continuar."
        )
    else:
        if st.button("🚀 Generar Reporte Clínico"):
            with st.spinner(
                "Procesando mediciones y aplicando plantilla clínica..."
            ):
                try:
                    # Paso 1: Extracción y normalización con Python
                    datos_crudos = extraer_texto_pdf(uploaded_file.read())

                    # Paso 2: Invocación de la API de Gemini
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            PROMPT_GOLD_STANDARD,
                            f"DATOS CRUDOS DEL NUEVO ESTUDIO:\n{datos_crudos}",
                        ],
                    )

                    st.subheader("Reporte Clínico Generado")
                    st.markdown(response.text)

                    st.download_button(
                        "Descargar Reporte (.txt)",
                        response.text,
                        file_name="Reporte_Ecocardiograma_Ross.txt",
                    )

                except Exception as e:
                    st.error(f"Error al generar el reporte: {str(e)}")
