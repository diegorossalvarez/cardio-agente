import io
import numpy as np
from google import genai
from google.genai import types
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

st.set_page_config(
    page_title="CardioAgente - Dr. Diego Ross Álvarez",
    page_icon="🫀",
    layout="wide",
)

st.title("🫀 CardioAgente: Reportes Clínicos Especializados")
st.markdown(
    "Generación automática de reportes de **Ecocardiograma**, **Holter** y"
    " **Pruebas Autonómicas** en formato compacto de alto rendimiento."
)

# Sidebar
st.sidebar.header("🔑 Configuración")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

st.sidebar.header("📋 Estudio")
tipo_estudio = st.sidebar.selectbox(
    "Selecciona el tipo de estudio:",
    [
        "Ecocardiograma Transtorácico (Formato Compacto Estricto)",
        "Holter de 24 Horas",
        "Pruebas Autonómicas (Valsalva / Ortostatismo / Respiración)",
    ],
)


# Función auxiliar para cálculo de Qp/Qs
def calcular_qp_qs(diam_tsvd_mm, itv_tsvd_cm, diam_tsvi_mm, itv_tsvi_cm):
  try:
    r_vd = (diam_tsvd_mm / 10.0) / 2.0
    r_vi = (diam_tsvi_mm / 10.0) / 2.0
    area_vd = np.pi * (r_vd**2)
    area_vi = np.pi * (r_vi**2)
    sv_vd = area_vd * itv_tsvd_cm
    sv_vi = area_vi * itv_tsvi_cm
    qp_qs = sv_vd / sv_vi
    return round(qp_qs, 2)
  except Exception:
    return None


# Generación de PDF Compacto con ReportLab
def generar_pdf_compacto(titulo_estudio, texto_reporte):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=28,
      leftMargin=28,
      topMargin=28,
      bottomMargin=28,
  )
  story = []
  styles = getSampleStyleSheet()

  estilo_encabezado_nombre = ParagraphStyle(
      "EncabezadoNombre",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=13,
      textColor=colors.HexColor("#1A365D"),
      leading=15,
  )
  estilo_encabezado_sub = ParagraphStyle(
      "EncabezadoSub",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=8.5,
      textColor=colors.HexColor("#2B6CB0"),
      leading=11,
  )
  estilo_contacto = ParagraphStyle(
      "EncabezadoContacto",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=8,
      textColor=colors.HexColor("#4A5568"),
      alignment=2,
      leading=10,
  )

  col_izq = [
      Paragraph("DR. DIEGO ROSS ÁLVAREZ", estilo_encabezado_nombre),
      Paragraph(
          "Cardiólogo - Electrofisiólogo | Especialidad UNAM 12883155",
          estilo_encabezado_sub,
      ),
  ]
  col_der = [
      Paragraph("<b>WhatsApp:</b> 9812438407", estilo_contacto),
      Paragraph(
          "<b>Consultorio:</b> Zenzontle 110, Fracc. La Ceiba", estilo_contacto
      ),
      Paragraph("Villahermosa, Tabasco | CP 86127", estilo_contacto),
  ]

  tabla_membrete = Table([[col_izq, col_der]], colWidths=[4.2 * inch, 3.4 * inch])
  tabla_membrete.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
      ])
  )
  story.append(tabla_membrete)
  story.append(Spacer(1, 4))

  tabla_linea = Table([[""]], colWidths=[7.6 * inch])
  tabla_linea.setStyle(
      TableStyle(
          [("LINEABOVE", (0, 0), (-1, -1), 1.2, colors.HexColor("#1A365D"))]
      )
  )
  story.append(tabla_linea)
  story.append(Spacer(1, 6))

  estilo_titulo = ParagraphStyle(
      "TituloEstudio",
      parent=styles["Heading2"],
      fontName="Helvetica-Bold",
      fontSize=11,
      textColor=colors.HexColor("#2C5282"),
      alignment=1,
      spaceAfter=8,
  )
  story.append(Paragraph(titulo_estudio.upper(), estilo_titulo))

  estilo_cuerpo = ParagraphStyle(
      "CuerpoCompacto",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=8.5,
      textColor=colors.HexColor("#1A202C"),
      leading=11.5,
      spaceAfter=4,
  )
  estilo_seccion = ParagraphStyle(
      "SeccionHeader",
      parent=estilo_cuerpo,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1A365D"),
      fontSize=9.5,
      spaceBefore=6,
      spaceAfter=2,
  )

  lineas = texto_reporte.split("\n")
  for linea in lineas:
    linea_limpia = linea.strip().replace("*", "").replace("#", "")
    if linea_limpia:
      if (
          "SECCIÓN" in linea_limpia
          or "CONCLUSIÓN" in linea_limpia
          or linea_limpia.isupper()
      ):
        story.append(Paragraph(linea_limpia, estilo_seccion))
      else:
        story.append(Paragraph(linea_limpia, estilo_cuerpo))

  doc.build(story)
  buffer.seek(0)
  return buffer


# Opciones de entrada de datos
opcion_entrada = st.radio(
    "Selecciona el método para ingresar los datos del estudio:",
    ["📄 Subir PDF del ecógrafo", "✍️ Pegar texto / Dictado de voz"],
    horizontal=True,
)

pdf_file = None
dictado = ""

if opcion_entrada == "📄 Subir PDF del ecógrafo":
  pdf_file = st.file_uploader(
      "Carga el PDF con las mediciones o reporte del equipo:",
      type=["pdf"],
      help="Sube el archivo PDF generado por el ecógrafo (Chison, Vinno, etc.)",
  )
else:
  dictado = st.text_area(
      "Pega el texto del ecógrafo o dicta el estudio:",
      height=200,
      placeholder="Pega aquí la tabla del ecógrafo o el dictado de voz...",
  )

if st.button("🚀 Generar Reporte Médico en PDF", type="primary"):
  if not api_key:
    st.error(
        "Por favor ingresa tu Gemini API Key en la barra lateral izquierda."
    )
  elif opcion_entrada == "📄 Subir PDF del ecógrafo" and pdf_file is None:
    st.warning("Por favor selecciona y sube un archivo PDF.")
  elif (
      opcion_entrada == "✍️ Pegar texto / Dictado de voz" and not dictado.strip()
  ):
    st.warning("Por favor ingresa el texto o dictado del estudio.")
  else:
    with st.spinner("Procesando estudio y aplicando reglas estrictas..."):
      try:
        client = genai.Client(api_key=api_key)

        prompt_maestro = f"""
                Eres un asistente experto en cardiología para el Dr. Diego Ross Álvarez.
                Procesa la información del siguiente {tipo_estudio}.

                REGLAS ESTRICTAS E INQUEBRANTABLES:
                1. FIDELIDAD ABSOLUTA Y CERO INVENTOS:
                   - Extrae ÚNICAMENTE los datos explícitos de la fuente (ya sea texto o tablas dentro del PDF).
                   - PROHIBIDO mezclar parámetros o asignar valores de un ventrículo a otro.
                   - Si un dato no viene en el archivo o texto, omítelo. Sin comentarios ni adjetivos dramáticos ("marcadas alteraciones", "asustar", etc.). Rigor seco y clínico.

                2. NORMALIZACIÓN DE VELOCIDADES Y SIGNOS:
                   - Las velocidades tisulares (e', Sa) deben reportarse en **cm/s** con valor strictly POSITIVO (PROHIBIDO usar signos negativos como -6.59, reportar "e' septal 6.59 cm/s").
                   - Flujos continuos (IT, Vmáx) en **m/s**. Dimensiones lineales en **mm**.
                   - AccT / TAcp del TSVD en segundos (s).

                3. CONDICIONAL DE Qp/Qs (CORTOCIRCUITOS / SHUNTS):
                   - SOLO calcula y reporta la relación Qp/Qs si existe un CORTOCIRCUITO o SHUNT intracardíaco/extracardíaco explícito con flujo aumentado (ej. CIA, CIV, PCA, ventana aortopulmonar, drenaje venoso anómalo).
                   - NO calcules ni reportes Qp/Qs en valvulopatías aisladas (incluyendo válvula aórtica bicúspide sin shunt), cardiopatía isquémica, hipertensiva o miocardiopatías.

                4. ESTRUCTURA DE 9 SECCIONES Y CONCLUSIÓN DE 8 PUNTOS:
                   - Sección 4: Incluir Onda E (cm/s), Onda A (cm/s), E/A, e' septal/lateral positivos (cm/s), E/e' septal/lateral y movilidad descrita objetivamente.
                   - Sección 7: Incluir AccT pulmonar (s) y PSAP estimada calculada como Gradiente IT + PAD.
                   - Conclusión Obligatoria (8 puntos):
                     1. Geometría VI con IMVI y RWT explícitos entre paréntesis (ej. Hipertrofia excéntrica [IMVI 135.8 g/m² y RWT 0.39]).
                     2. Tamaño de cavidades indicando medidas clave que justifican la dilatación (ej. Dilatación moderada de aurícula izquierda [diámetro AP 46.3 mm] y ventrículo izquierdo [diámetro diastólico 55.3 mm]).
                     3. Función sistólica biventricular separada: VI por Simpson (ej. Disfunción sistólica global severa con FEVI por Simpson de 23.59%) y VD por TAPSE (ej. Disfunción sistólica longitudinal con TAPSE de 16.2 mm). NO inventes función radial/strain/3D si no se mide.
                     4. Función diastólica con valores explícitos de E/e' y estado de presiones de llenado (ej. Relajación alterada con relación E/e' septal de 12.70 y lateral de 10.59, indicando presiones de llenado limítrofes).
                     5. Movilidad descrita objetivamente sin dramatismos ni adjetivos subjetivos.
                     6. Análisis valvular ("Sin valvulopatía significativa" en aórtica/mitral si aplica, índice Doppler si está presente, y grado de insuficiencia tricúspide).
                     7. Probabilidad de hipertensión pulmonar (categoría directa como "Probabilidad baja", sin citar "guías ASE" ni repetir la cifra de PSAP).
                     8. Diagnóstico integrativo preciso y profesional (ej. Cardiopatía de probable origen isquémico con zonas de infarto antiguo, disfunción sistólica global severa del VI, hipertrofia excéntrica y presiones de llenado limítrofes).
                """

        # Preparar los contenidos para Gemini segun el metodo de entrada
        contents_input = [prompt_maestro]

        if opcion_entrada == "📄 Subir PDF del ecógrafo" and pdf_file is not None:
          pdf_bytes = pdf_file.read()
          contents_input.append(
              types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
          )
        else:
          contents_input.append(f"\nTEXTO O DATOS DEL ESTUDIO:\n{dictado}")

        response = client.models.generate_content(
            model="gemini-3.8-flash", contents=contents_input
        )
        texto_generado = response.text

        pdf_resultado_bytes = generar_pdf_compacto(tipo_estudio, texto_generado)

        st.success("¡Reporte generado con éxito!")

        col1, col2 = st.columns(2)
        with col1:
          st.download_button(
              label="📥 Descargar PDF Impresión / WhatsApp",
              data=pdf_resultado_bytes,
              file_name=f"Reporte_{tipo_estudio.replace(' ', '_')}.pdf",
              mime="application/pdf",
              use_container_width=True,
          )
        with col2:
          with st.expander("👁️ Ver texto procesado"):
            st.write(texto_generado)

      except Exception as e:
        st.error(f"Error al procesar el archivo o texto: {e}")
