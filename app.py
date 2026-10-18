import io
from google import genai
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
    "Generación automática de reportes e interpretación de **Ecocardiograma (9"
    " secciones)**, **Holter 24h** y **Pruebas Autonómicas**."
)

# Sidebar
st.sidebar.header("🔑 Configuración")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

st.sidebar.header("📋 Estudio")
tipo_estudio = st.sidebar.selectbox(
    "Selecciona el tipo de estudio:",
    [
        "Ecocardiograma Transtorácico (9 Secciones)",
        "Holter de 24 Horas",
        "Pruebas Autonómicas (Valsalva / Ortostatismo / Respiración)",
    ],
)


# Función para generar el PDF con ReportLab
def generar_pdf_clinico(titulo_estudio, texto_reporte):
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

  # Estilos personalizados
  estilo_encabezado_nombre = ParagraphStyle(
      "EncabezadoNombre",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=14,
      textColor=colors.HexColor("#1A365D"),
      leading=16,
  )

  estilo_encabezado_sub = ParagraphStyle(
      "EncabezadoSub",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=9,
      textColor=colors.HexColor("#2B6CB0"),
      leading=12,
  )

  estilo_contacto = ParagraphStyle(
      "EncabezadoContacto",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=8,
      textColor=colors.HexColor("#4A5568"),
      alignment=2,  # Derecha
      leading=11,
  )

  # Tabla de Membrete
  col_izquierda = [
      Paragraph("DR. DIEGO ROSS ÁLVAREZ", estilo_encabezado_nombre),
      Paragraph(
          "Cardiólogo - Electrofisiólogo | Especialidad UNAM 12883155",
          estilo_encabezado_sub,
      ),
  ]

  col_derecha = [
      Paragraph("<b>WhatsApp:</b> 9812438407", estilo_contacto),
      Paragraph(
          "<b>Consultorio:</b> Zenzontle 110, Fracc. La Ceiba", estilo_contacto
      ),
      Paragraph("Villahermosa, Tabasco | CP 86127", estilo_contacto),
  ]

  tabla_membrete = Table([[col_izquierda, col_derecha]], colWidths=[4.2 * inch, 3.2 * inch])
  tabla_membrete.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
      ])
  )
  story.append(tabla_membrete)

  # Línea divisoria azul
  story.append(Spacer(1, 6))
  tabla_linea = Table([[""]], colWidths=[7.4 * inch])
  tabla_linea.setStyle(
      TableStyle([
          ("LINEABOVE", (0, 0), (-1, -1), 1.5, colors.HexColor("#1A365D")),
      ])
  )
  story.append(tabla_linea)
  story.append(Spacer(1, 10))

  # Título del Estudio
  estilo_titulo_estudio = ParagraphStyle(
      "TituloEstudio",
      parent=styles["Heading2"],
      fontName="Helvetica-Bold",
      fontSize=12,
      textColor=colors.HexColor("#2C5282"),
      alignment=1,  # Centrado
      spaceAfter=12,
  )
  story.append(Paragraph(titulo_estudio.upper(), estilo_titulo_estudio))

  # Cuerpo del Reporte
  estilo_cuerpo = ParagraphStyle(
      "CuerpoReporte",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=9.5,
      textColor=colors.HexColor("#1A202C"),
      leading=14,
      spaceAfter=6,
  )

  # Procesar párrafos
  lineas = texto_reporte.split("\n")
  for linea in lineas:
    linea_limpia = linea.strip().replace("*", "").replace("#", "")
    if linea_limpia:
      if (
          linea_limpia.isupper()
          or "SECCIÓN" in linea_limpia
          or "CONCLUSIÓN" in linea_limpia
      ):
        estilo_seccion = ParagraphStyle(
            "SeccionHeader",
            parent=estilo_cuerpo,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1A365D"),
            fontSize=10,
            spaceBefore=8,
        )
        story.append(Paragraph(linea_limpia, estilo_seccion))
      else:
        story.append(Paragraph(linea_limpia, estilo_cuerpo))

  doc.build(story)
  buffer.seek(0)
  return buffer


# Interfaz de Usuario
dictado = st.text_area(
    "Pega o dicta la información del estudio:",
    height=220,
    placeholder=(
        "Ejemplo para Eco: VTDVI 110 ml, VTSVI 40 ml, FEVI 60%, E 85 cm/s, A 60"
        " cm/s, e' septal 9 cm/s, IT con velocidad 2.8 m/s, VCI 1.8 cm con"
        " colapso >50%..."
    ),
)

if st.button("🚀 Generar Reporte Médico en PDF", type="primary"):
  if not api_key:
    st.error(
        "Por favor ingresa tu Gemini API Key en la barra lateral izquierda."
    )
  elif not dictado.strip():
    st.warning("Ingresa los datos o el dictado del estudio.")
  else:
    with st.spinner("Procesando datos con IA y maquetando PDF..."):
      try:
        client = genai.Client(api_key=api_key)

        prompt_maestro = f"""
                Eres un asistente experto en cardiología para el Dr. Diego Ross Álvarez.
                Procesa la siguiente información de un {tipo_estudio}.

                REGLAS ESTRICTAS PARA ECOCARDIOGRAMA:
                1. Organiza la información obligatoriamente en 9 secciones.
                2. Unidades de Doppler: Flujo continuo (ej. IT) en m/s. Flujo pulsado (ej. onda E, A, e') en cm/s. Sin duplicar unidades ni mezclar nomenclaturas.
                3. Calcula PSAP sumando el gradiente por IT + PAD (estimada por VCI).
                4. Incluye la conclusión en 8 puntos claros y jerarquizados.
                5. Genera texto plano limpio, sin marcas de markdown (*, #, **).

                REGLAS PARA HOLTER Y PRUEBAS AUTONÓMICAS:
                - Presenta la interpretación clínica estandarizada (Valsalva, ortostatismo 30:15, respuesta respiratoria).

                DATOS DEL ESTUDIO:
                {dictado}
                """

        response = client.models.generate_content(
            model="gemini-3.8-flash", contents=prompt_maestro
        )
        texto_generado = response.text

        # Generar PDF
        pdf_bytes = generar_pdf_clinico(tipo_estudio, texto_generado)

        st.success("¡Reporte generado e imprimible con éxito!")

        col1, col2 = st.columns(2)
        with col1:
          st.download_button(
              label="📥 Descargar PDF para Imprimir / WhatsApp",
              data=pdf_bytes,
              file_name=f"Reporte_{tipo_estudio.replace(' ', '_')}.pdf",
              mime="application/pdf",
              use_container_width=True,
          )
        with col2:
          with st.expander("👁️ Ver texto extraído"):
            st.write(texto_generado)

      except Exception as e:
        st.error(f"Error al procesar: {e}")
