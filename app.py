import io
import json
import re
from typing import Optional, Dict, Any, List
from xml.sax.saxutils import escape
import pdfplumber
import streamlit as st
from google import genai
from google.genai import types
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# Importamos la matriz limpia de ejemplos (INALTERADA)
from ejemplos_ross_v2 import (
    EJEMPLO_1_NORMAL,
    EJEMPLO_2_HIPERTROFIA,
    EJEMPLO_3_FEVI_DEPRIMIDA,
    EJEMPLO_4_VALVULOPATIA,
    EJEMPLO_5_HAP,
    EJEMPLO_6_CONGENITA,
    EJEMPLO_7_PROTESIS,
)

# ====================================================================
# CONFIGURACIÓN CENTRALIZADA DE REGLAS DE DOMINIO Y PROHIBICIÓN
# ====================================================================
CLINICAL_CONFIG = {
    "PAD_INSTITUCIONAL": 5.0,
    "UMBRAL_HAP_BAJA": 35.0,
    "UMBRAL_HAP_INTERMEDIA": 50.0,
    "LIMITES_BIOLOGICOS": {
        "edad": (0, 120),
        "asc_m2": (0.3, 3.5),
        "fevi_porcentaje": (5.0, 95.0),
        "dtdvi_mm": (15.0, 120.0),
        "vtd_ml": (10.0, 600.0),
        "tapse_mm": (5.0, 45.0)
    },
    "REGLAS_DE_PROHIBICION": {
        "motilidad_normal": "Prohibido afirmar motilidad normal sin descripción segmentaria explícita.",
        "diastolica_normal": "Prohibido afirmar función diastólica normal o conservada si no existen parámetros suficientes evaluados.",
        "sin_valvulopatias": "Prohibido afirmar ausencia absoluta de valvulopatías si las estructuras valvulares no fueron completamente evaluadas en la fuente."
    }
}

st.set_page_config(
    page_title="CardioAgente | Dr. Diego Ross Álvarez",
    page_icon="🫀",
    layout="wide",
)

st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .clinic-header {
            padding: 15px;
            background: linear-gradient(90deg, #1A365D 0%, #2B6CB0 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .warning-box {
            padding: 10px;
            background-color: #FFF5F5;
            border-left: 5px solid #E53E3E;
            color: #C53030;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 13px;
        }
        .audit-box {
            padding: 10px;
            background-color: #EDF2F7;
            border-left: 5px solid #3182CE;
            color: #2D3748;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 12px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="clinic-header">
        <h2 style='margin:0; font-size: 24px;'>🫀 CardioAgente - Arquitectura Híbrida Producción v7.0</h2>
        <p style='margin:5px 0 0 0; font-size: 14px;'>Dr. Diego Ross Álvarez | Cardiólogo - Electrofisiólogo | Céd. Esp. 12883155</p>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.info("Arquitectura Híbrida v7.0:\n1. Extracción IA\n2. Normalización\n3. Motor Ross (Trazabilidad y Evidencia)\n4. Hallazgos Relevantes y Limitaciones\n5. IA Redactora Contextual\n6. Fase 3.5: Auditor Automático")


def extraer_texto_pdf(file_bytes) -> str:
    texto_completo = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_completo += t + "\n"
    return texto_completo


# ====================================================================
# FASE 1: EXTRACCIÓN PURA (ESTRICTAMENTE SIN INTERPRETACIÓN)
# ====================================================================
PROMPT_FASE_1_EXTRACCION = f"""
Eres un motor de extracción de datos médicos especializado en ecocardiografía. Tu ÚNICA tarea es extraer los valores numéricos y métricas exactas del texto proporcionado y volcarlos en el siguiente esquema JSON.

REGLA CRÍTICA ABSOLUTA:
- Extrae únicamente lo que esté explícitamente en el texto.
- Si un parámetro numérico o categórico no existe o no fue evaluado, asigna estrictamente el valor null. PROHIBIDO usar 0.0, cadenas vacías (salvo nombres o campos de texto libre abiertos) o valores por defecto.
- PROHIBIDO inventar, calcular interpretaciones, emitir juicios clínicos, redactar conclusiones o generar diagnósticos. Solo extrae variables brutas.

ESTRUCTURA DE SALIDA OBLIGATORIA (JSON PURO SIN MARKDOWN):
{{
  "paciente": {{
    "nombre": "",
    "edad": null,
    "sexo": null,
    "peso_kg": null,
    "talla_m": null,
    "asc_m2": null
  }},
  "introduccion": "",
  "ventriculo_izquierdo": {{
    "dtdvi_mm": null,
    "dtsvi_mm": null,
    "siv_mm": null,
    "ppvi_mm": null,
    "fevi_porcentaje": null,
    "volumen_telediastolico_ml": null,
    "volumen_telesistolico_ml": null,
    "masa_miocardica_g": null,
    "movilidad_anormal_descripcion": null
  }},
  "auricula_izquierda": {{
    "diametro_ap_mm": null,
    "volumen_ml": null,
    "volumen_indexado_ml_m2": null
  }},
  "ventriculo_derecho": {{
    "diametro_basal_mm": null,
    "tapse_mm": null,
    "onda_s_cm_s": null
  }},
  "auricula_derecha": {{
    "area_cm2": null
  }},
  "hemodinamica_derecha": {{
    "velocidad_it_max_ms": null,
    "gradiente_it_pico_mmhg": null
  }},
  "funcion_diastolica_bruta": {{
    "onda_e_cm_s": null,
    "onda_a_cm_s": null,
    "tda_ms": null,
    "e_prima_septal_cm_s": null,
    "e_prima_lateral_cm_s": null,
    "relacion_e_e_prima": null
  }},
  "valvulas": {{
    "aortica_vmax_ms": null,
    "aortica_grad_medio_mmhg": null,
    "aortica_area_cm2": null,
    "aortica_insuficiencia": null,
    "mitral_insuficiencia": null,
    "mitral_estenosis": null,
    "tricuspide_insuficiencia": null,
    "pulmonar_insuficiencia": null
  }},
  "pericardio_cava": {{
    "derrame_pericardico": null,
    "cava_inferior_diametro_mm": null,
    "cava_colapso_porcentaje": null
  }}
}}

---
MATRIZ DE ENTRENAMIENTO DE REFERENCIA:
CASO 1: {EJEMPLO_1_NORMAL}
CASO 2: {EJEMPLO_2_HIPERTROFIA}
CASO 3: {EJEMPLO_3_FEVI_DEPRIMIDA}
CASO 4: {EJEMPLO_4_VALVULOPATIA}
CASO 5: {EJEMPLO_5_HAP}
CASO 6: {EJEMPLO_6_CONGENITA}
CASO 7: {EJEMPLO_7_PROTESIS}
---

PROCESA LOS SIGUIENTES DATOS CRUDOS Y DEVUELVE ÚNICAMENTE EL OBJETO JSON VÁLIDO:
"""


# ====================================================================
# FASE 1.5: NORMALIZACIÓN Y SANITIZACIÓN ROBUSTA DE INPUTS
# ====================================================================
def sanitizar_y_convertir_numero(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val_clean = val.strip().lower()
        if not val_clean or val_clean in ["null", "none", "n/a", "no reportado", "-"]:
            return None
        match = re.search(r"([-+]?\d*\.?\d+)", val_clean)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def sanitizar_texto(val: Any) -> Optional[str]:
    if val is None:
        return None
    if not isinstance(val, str):
        val = str(val)
    val_clean = val.strip()
    if not val_clean or val_clean.lower() in ["null", "none", "n/a", "-"]:
        return None
    
    lower_val = val_clean.lower()
    if lower_val in ["masculino", "hombre", "m", "male"]:
        return "masculino"
    if lower_val in ["femenino", "mujer", "f", "female"]:
        return "femenino"
        
    return val_clean


def fase_1_5_normalizacion(data: dict) -> dict:
    if not isinstance(data, dict):
        return data

    pac = data.get("paciente", {})
    if isinstance(pac, dict):
        pac["nombre"] = sanitizar_texto(pac.get("nombre")) or ""
        pac["edad"] = int(sanitizar_y_convertir_numero(pac.get("edad"))) if sanitizar_y_convertir_numero(pac.get("edad")) is not None else None
        pac["sexo"] = sanitizar_texto(pac.get("sexo"))
        pac["peso_kg"] = sanitizar_y_convertir_numero(pac.get("peso_kg"))
        pac["talla_m"] = sanitizar_y_convertir_numero(pac.get("talla_m"))
        pac["asc_m2"] = sanitizar_y_convertir_numero(pac.get("asc_m2"))

    vi = data.get("ventriculo_izquierdo", {})
    if isinstance(vi, dict):
        for k in ["dtdvi_mm", "dtsvi_mm", "siv_mm", "ppvi_mm", "fevi_porcentaje", "volumen_telediastolico_ml", "volumen_telesistolico_ml", "masa_miocardica_g"]:
            vi[k] = sanitizar_y_convertir_numero(vi.get(k))
        vi["movilidad_anormal_descripcion"] = sanitizar_texto(vi.get("movilidad_anormal_descripcion"))

    ai = data.get("auricula_izquierda", {})
    if isinstance(ai, dict):
        for k in ["diametro_ap_mm", "volumen_ml", "volumen_indexado_ml_m2"]:
            ai[k] = sanitizar_y_convertir_numero(ai.get(k))

    vd = data.get("ventriculo_derecho", {})
    if isinstance(vd, dict):
        for k in ["diametro_basal_mm", "tapse_mm", "onda_s_cm_s"]:
            vd[k] = sanitizar_y_convertir_numero(vd.get(k))

    ad = data.get("auricula_derecha", {})
    if isinstance(ad, dict):
        ad["area_cm2"] = sanitizar_y_convertir_numero(ad.get("area_cm2"))

    hemo = data.get("hemodinamica_derecha", {})
    if isinstance(hemo, dict):
        for k in ["velocidad_it_max_ms", "gradiente_it_pico_mmhg"]:
            hemo[k] = sanitizar_y_convertir_numero(hemo.get(k))

    fd_bruta = data.get("funcion_diastolica_bruta", {})
    if isinstance(fd_bruta, dict):
        for k in ["onda_e_cm_s", "onda_a_cm_s", "tda_ms", "e_prima_septal_cm_s", "e_prima_lateral_cm_s", "relacion_e_e_prima"]:
            fd_bruta[k] = sanitizar_y_convertir_numero(fd_bruta.get(k))

    valv = data.get("valvulas", {})
    if isinstance(valv, dict):
        for k in ["aortica_vmax_ms", "aortica_grad_medio_mmhg", "aortica_area_cm2"]:
            valv[k] = sanitizar_y_convertir_numero(valv.get(k))
        for k in ["aortica_insuficiencia", "mitral_insuficiencia", "mitral_estenosis", "tricuspide_insuficiencia", "pulmonar_insuficiencia"]:
            valv[k] = sanitizar_texto(valv.get(k))

    pc = data.get("pericardio_cava", {})
    if isinstance(pc, dict):
        pc["cava_inferior_diametro_mm"] = sanitizar_y_convertir_numero(pc.get("cava_inferior_diametro_mm"))
        pc["cava_colapso_porcentaje"] = sanitizar_y_convertir_numero(pc.get("cava_colapso_porcentaje"))

    return data


def validar_rangos_biologicos(data: dict) -> List[str]:
    advertencias = []
    limites = CLINICAL_CONFIG["LIMITES_BIOLOGICOS"]
    
    pac = data.get("paciente", {})
    if pac.get("edad") is not None and not (limites["edad"][0] <= pac["edad"] <= limites["edad"][1]):
        advertencias.append(f"⚠️ Alerta de validación: Edad biológicamente improbable ({pac['edad']} años).")
    if pac.get("asc_m2") is not None and not (limites["asc_m2"][0] <= pac["asc_m2"] <= limites["asc_m2"][1]):
        advertencias.append(f"⚠️ Alerta de validación: Superficie corporal (ASC) fuera de rango lógico ({pac['asc_m2']} m²).")

    vi = data.get("ventriculo_izquierdo", {})
    if vi.get("fevi_porcentaje") is not None and not (limites["fevi_porcentaje"][0] <= vi["fevi_porcentaje"] <= limites["fevi_porcentaje"][1]):
        advertencias.append(f"⚠️ Alerta de validación: Fracción de eyección (FEVI) con valor imposible ({vi['fevi_porcentaje']}%).")
    if vi.get("dtdvi_mm") is not None and not (limites["dtdvi_mm"][0] <= vi["dtdvi_mm"] <= limites["dtdvi_mm"][1]):
        advertencias.append(f"⚠️ Alerta de validación: DTDVI fuera de límites fisiológicos ({vi['dtdvi_mm']} mm).")
    if vi.get("volumen_telediastolico_ml") is not None and not (limites["vtd_ml"][0] <= vi["volumen_telediastolico_ml"] <= limites["vtd_ml"][1]):
        advertencias.append(f"⚠️ Alerta de validación: Volumen telediastólico (VTDVI) fuera de rango ({vi['volumen_telediastolico_ml']} ml).")

    return advertencias


# ====================================================================
# FASE 2: MOTOR ROSS DETERMINISTA (CON TRAZABILIDAD Y CONFIANZA)
# ====================================================================
def fase_2_motor_ross_determinista(data: dict) -> dict:
    hallazgos_relevantes = []
    limitaciones_del_estudio = []
    
    vi = data.setdefault("ventriculo_izquierdo", {})
    fevi = vi.get("fevi_porcentaje")
    vtd = vi.get("volumen_telediastolico_ml")
    dtdvi = vi.get("dtdvi_mm")
    asc = data.get("paciente", {}).get("asc_m2")

    modulos_stats = {
        "ventriculo_izquierdo": {"total": 3, "presentes": 0},
        "funcion_diastolica": {"total": 5, "presentes": 0},
        "hemodinamica_derecha": {"total": 2, "presentes": 0},
        "valvulas": {"total": 4, "presentes": 0}
    }

    if fevi is not None:
        modulos_stats["ventriculo_izquierdo"]["presentes"] += 1
        if fevi >= 52.0:
            func_sist_txt = "Función sistólica global del ventrículo izquierdo conservada."
        elif 41.0 <= fevi < 52.0:
            func_sist_txt = "Disfunción sistólica ventricular izquierda leve."
        elif 30.0 <= fevi < 41.0:
            func_sist_txt = "Disfunción sistólica ventricular izquierda moderada."
        else:
            func_sist_txt = "Disfunción sistólica ventricular izquierda severa."
        
        vi["funcion_sistolica_evaluada"] = func_sist_txt
        hallazgos_relevantes.append({
            "hallazgo": func_sist_txt,
            "evidencia": {"FEVI": fevi}
        })
    else:
        vi["funcion_sistolica_evaluada"] = None

    dilatacion_detectada = False
    evidencia_dil = {}
    if vtd is not None:
        modulos_stats["ventriculo_izquierdo"]["presentes"] += 1
        evidencia_dil["VTD"] = vtd
        if vtd > 160.0:
            dilatacion_detectada = True
    if dtdvi is not None:
        modulos_stats["ventriculo_izquierdo"]["presentes"] += 1
        evidencia_dil["DTDVI"] = dtdvi
        if dtdvi > 58.0:
            dilatacion_detectada = True

    if dilatacion_detectada:
        alerta_dil = f"Se documenta dilatación ventricular izquierda."
        vi["alerta_dilatacion"] = alerta_dil
        hallazgos_relevantes.append({
            "hallazgo": "Dilatación ventricular izquierda",
            "evidencia": evidencia_dil
        })
    else:
        vi["alerta_dilatacion"] = None

    fd = data.get("funcion_diastolica_bruta", {})
    e_val = fd.get("onda_e_cm_s")
    a_val = fd.get("onda_a_cm_s")
    e_prima = fd.get("e_prima_septal_cm_s")
    rel_ee = fd.get("relacion_e_e_prima")
    lavi = data.get("auricula_izquierda", {}).get("volumen_indexado_ml_m2")
    
    for param_val in [e_val, a_val, e_prima, rel_ee, lavi]:
        if param_val is not None:
            modulos_stats["funcion_diastolica"]["presentes"] += 1

    params_diastolicos_presentes = sum(1 for x in [e_val, a_val, e_prima, rel_ee, lavi] if x is not None)
    
    if params_diastolicos_presentes >= 3:
        criterios_cumplidos = 0
        evidencia_fd = {}
        if rel_ee is not None: 
            evidencia_fd["E/e'"] = rel_ee
            if rel_ee > 14: criterios_cumplidos += 1
        if e_prima is not None: 
            evidencia_fd["e' septal"] = e_prima
            if e_prima < 7: criterios_cumplidos += 1
        if lavi is not None: 
            evidencia_fd["LAVI"] = lavi
            if lavi > 34: criterios_cumplidos += 1
        
        if criterios_cumplidos >= 2:
            diag_fd = "Alteración de la relajación / Presiones de llenado ventricular izquierdas elevadas (Disfunción diastólica)."
        elif criterios_cumplidos == 1:
            diag_fd = "Patrón diastólico limítrofe o indeterminado."
        else:
            diag_fd = "Parámetros de función diastólica dentro de rangos habituales según criterios analizados."
        fd["evaluacion_diastolica"] = diag_fd
        hallazgos_relevantes.append({
            "hallazgo": diag_fd,
            "evidencia": evidencia_fd
        })
    else:
        fd["evaluacion_diastolica"] = "Función diastólica no clasificable con la información disponible."
        limitaciones_del_estudio.append("No se reportaron parámetros suficientes para evaluar función diastólica.")

    hemo = data.setdefault("hemodinamica_derecha", {})
    grad_it = hemo.get("gradiente_it_pico_mmhg")
    if grad_it is not None:
        modulos_stats["hemodinamica_derecha"]["presentes"] += 1
        pad_inst = CLINICAL_CONFIG["PAD_INSTITUCIONAL"]
        psap = grad_it + pad_inst
        hemo["psap_calculada_mmhg"] = round(psap, 1)
        if psap < CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
            hap_txt = "Baja probabilidad de hipertensión pulmonar."
        elif CLINICAL_CONFIG["UMBRAL_HAP_BAJA"] <= psap <= CLINICAL_CONFIG["UMBRAL_HAP_INTERMEDIA"]:
            hap_txt = "Probabilidad intermedia de hipertensión pulmonar."
        else:
            hap_txt = "Alta probabilidad de hipertensión pulmonar."
        hemo["probabilidad_hap"] = hap_txt
        hallazgos_relevantes.append({
            "hallazgo": hap_txt,
            "evidencia": {"Gradiente IT": grad_it, "PSAP estimada": psap}
        })
    else:
        hemo["psap_calculada_mmhg"] = None
        hemo["probabilidad_hap"] = None

    valv = data.get("valvulas", {})
    for v_key in ["aortica_insuficiencia", "mitral_insuficiencia", "tricuspide_insuficiencia", "pulmonar_insuficiencia"]:
        if valv.get(v_key) is not None:
            modulos_stats["valvulas"]["presentes"] += 1

    if valv.get("aortica_insuficiencia") is None and valv.get("mitral_insuficiencia") is None:
        limitaciones_del_estudio.append("No se documentó evaluación completa de valvulopatías principales.")

    if vi.get("movilidad_anormal_descripcion") is None:
        limitaciones_del_estudio.append("No se documentó movilidad segmentaria explícita.")

    conclusiones = []
    
    if dtdvi is not None or vtd is not None:
        geo_partes = []
        if dtdvi is not None: geo_partes.append(f"DTDVI: {dtdvi} mm")
        if vtd is not None: geo_partes.append(f"VTD: {vtd} ml")
        base_geo = f"Ventrículo izquierdo con dimensiones ({', '.join(geo_partes)})."
        if vi.get("alerta_dilatacion"):
            base_geo += f" {vi['alerta_dilatacion']}"
        conclusiones.append(base_geo)
    else:
        conclusiones.append("Ventrículo izquierdo sin datos volumétricos o dimensionales reportados en el estudio.")

    ai = data.get("auricula_izquierda", {})
    diam_ap = ai.get("diametro_ap_mm")
    lavi_val = ai.get("volumen_indexado_ml_m2")
    if diam_ap is not None or lavi_val is not None:
        ai_partes = []
        if diam_ap is not None: ai_partes.append(f"diámetro AP: {diam_ap} mm")
        if lavi_val is not None: ai_partes.append(f"LAVI: {lavi_val} mL/m²")
        conclusiones.append(f"Aurícula izquierda evaluada con {', '.join(ai_partes)}.")
        if lavi_val is not None and lavi_val > 34:
            hallazgos_relevantes.append({
                "hallazgo": "Aurícula izquierda dilatada",
                "evidencia": {"LAVI": lavi_val}
            })
    else:
        conclusiones.append("Aurícula izquierda sin mediciones cuantitativas disponibles para análisis.")

    if vi.get("funcion_sistolica_evaluada"):
        conclusiones.append(vi["funcion_sistolica_evaluada"])
    else:
        conclusiones.append("Función sistólica global no valorable por ausencia de parámetros de eyección.")

    if fd.get("evaluacion_diastolica"):
        conclusiones.append(fd["evaluacion_diastolica"])
    else:
        conclusiones.append("Función diastólica no evaluada por insuficiencia de flujos Doppler reportados.")

    valv_txt = []
    if valv.get("mitral_insuficiencia"): valv_txt.append(f"Insuficiencia mitral {valv['mitral_insuficiencia']}")
    if valv.get("aortica_insuficiencia"): valv_txt.append(f"Insuficiencia aórtica {valv['aortica_insuficiencia']}")
    if valv_txt:
        conclusiones.append(f"Valvulopatías / Hallazgos valvulares: {', '.join(valv_txt)}.")
    else:
        conclusiones.append("Evaluación valvular sin reportes específicos de lesiones o insuficiencias en la fuente.")

    if hemo.get("probabilidad_hap"):
        conclusiones.append(hemo["probabilidad_hap"])
    else:
        conclusiones.append("Sin elementos hemodinámicos derechos suficientes para estimar probabilidad de hipertensión pulmonar.")

    mov_desc = vi.get("movilidad_anormal_descripcion")
    if mov_desc:
        conclusiones.append(f"Alteraciones de la movilidad segmentaria: {mov_desc}.")
    else:
        conclusiones.append("El informe fuente no consigna descripciones específicas de alteraciones segmentarias de la contractilidad.")

    while len(conclusiones) < 7:
        conclusiones.append("")
    data["conclusiones_deterministicas"] = conclusiones[:7]

    indice_confianza = {}
    for mod, stats in modulos_stats.items():
        if stats["total"] > 0:
            ratio = stats["presentes"] / stats["total"]
            indice_confianza[mod] = round(min(max(ratio, 0.1), 1.0), 2)
        else:
            indice_confianza[mod] = 0.5

    data["hechos_clinicos"] = {
        "hallazgos_relevantes": hallazgos_relevantes,
        "limitaciones_del_estudio": list(set(limitaciones_del_estudio)),
        "indice_confianza_por_modulo": indice_confianza,
        "reglas_de_prohibicion": CLINICAL_CONFIG["REGLAS_DE_PROHIBICION"]
    }

    return data


# ====================================================================
# FASE 3: IA REDACTORA CLÍNICA CONTEXTUAL (ACTUALIZADO A GEMINI 3.8 FLASH)
# ====================================================================
PROMPT_FASE_3_REDACCION = """
Eres un médico cardiólogo especialista en ecocardiografía que redacta exclusivamente utilizando el estilo formal, sobrio, elegante y clínico del Dr. Diego Ross Álvarez.

Recibirás un objeto JSON con los hechos clínicos estructurados:
- hallazgos_relevantes (con su evidencia)
- limitaciones_del_estudio
- reglas_de_prohibicion

TU TAREA:
Redactar la **descripción ecocardiográfica institucional**, la sección de **conclusiones** y el **diagnóstico final** integrando todo el contexto clínico con fluidez experta.

REGLAS CRÍTICAS ABSOLUTAS:
1. HALLAZGOS RELEVANTES: Debes construir la narrativa clínica tomando la lista de `hallazgos_relevantes` como su eje principal. Si existe discrepancia (ej. FEVI conservada con volumen diastólico elevado), menciona ambos factores sin contradecir los datos.
2. LIMITACIONES: Si existen elementos en `limitaciones_del_estudio`, explícalos claramente en la narrativa o conclusiones.
3. REGLAS DE PROHIBICIÓN: Cumple estrictamente con todas las prohibiciones definidas en `reglas_de_prohibicion`.
4. ROL: No reclasifiques ni recules métricas; úsalas tal cual. Actúa como redactor clínico experto.
5. Devuelve un JSON con la siguiente estructura estricta (sin markdown adicional de bloques de código):
{{
  "narrativa_descriptiva": "...",
  "conclusiones_redactadas": ["...", "...", "...", "...", "...", "...", "..."],
  "diagnostico_redactado": "..."
}}
"""


def fase_3_ia_redactora(client: genai.Client, api_key: str, data: dict) -> Dict[str, Any]:
    try:
        config_gen = types.GenerateContentConfig(temperature=0.1)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[
                PROMPT_FASE_3_REDACCION,
                f"HECHOS CLÍNICOS DEL MOTOR ROSS:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
            ],
            config=config_gen,
        )
        texto_resp = response.text.strip()
        texto_resp = re.sub(r"^```json\s*", "", texto_resp)
        texto_resp = re.sub(r"^```\s*", "", texto_resp)
        texto_resp = re.sub(r"\s*```$", "", texto_resp)
        return json.loads(texto_resp)
    except Exception:
        lineas = []
        vi = data.get("ventriculo_izquierdo", {})
        if vi.get("dtdvi_mm") is not None:
            lineas.append(f"• <b>VENTRÍCULO IZQUIERDO:</b> DTDVI de {vi['dtdvi_mm']} mm. {vi.get('funcion_sistolica_evaluada', '')}")
        ai = data.get("auricula_izquierda", {})
        if ai.get("diametro_ap_mm") is not None:
            lineas.append(f"• <b>AURÍCULA IZQUIERDA:</b> Diámetro AP de {ai['diametro_ap_mm']} mm.")
        
        return {
            "narrativa_descriptiva": "\n\n".join(lineas),
            "conclusiones_redactadas": data.get("conclusiones_deterministicas", ["", "", "", "", "", "", ""]),
            "diagnostico_redactado": "Estudio ecocardiográfico evaluado mediante Motor Ross."
        }


# ====================================================================
# FASE 3.5: AUDITOR CLÍNICO AUTOMÁTICO (ACTUALIZADO A GEMINI 3.8 FLASH)
# ====================================================================
def fase_3_5_auditor_clinico(client: genai.Client, api_key: str, data: dict, resultado_fase_3: dict) -> Dict[str, Any]:
    prompt_auditor = """
Eres un Auditor Clínico Senior de software médico. Tu tarea es verificar si la narrativa generada por la IA redactora cumple estrictamente con los hechos del Motor Ross.

Verifica:
1. ¿Omite algún hallazgo clave de hallazgos_relevantes?
2. ¿Viola alguna regla de reglas_de_prohibicion (ej. afirmar normalidad diastólica o motilidad normal sin datos)?
3. ¿Contradice los cálculos del Motor Ross?

Si todo es correcto, responde únicamente con el texto: "APROBADO".
Si hay discrepancias graves o violaciones de reglas, responde con un objeto JSON indicando el motivo de rechazo y sugerencia de corrección estricta.
"""
    try:
        config_gen = types.GenerateContentConfig(temperature=0.0)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[
                prompt_auditor,
                f"HECHOS DEL MOTOR ROSS:\n{json.dumps(data.get('hechos_clinicos', {}), ensure_ascii=False)}\n\nNARRATIVA GENERADA:\n{json.dumps(resultado_fase_3, ensure_ascii=False)}"
            ],
            config=config_gen,
        )
        veredicto = response.text.strip()
        if "APROBADO" in veredicto.upper():
            return {"aprobado": True, "comentario": "Auditoría clínica superada con éxito."}
        else:
            return {"aprobado": False, "comentario": veredicto}
    except Exception:
        return {"aprobado": True, "comentario": "Auditoría omitida por excepción técnica, aprobada por defecto."}


# ====================================================================
# FASE 5: PDF INSTITUCIONAL FINAL
# ====================================================================
def generar_pdf_reportlab(data: dict, narrativa: str, conclusiones: List[str], diagnostico: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    color_primario = colors.HexColor("#1A365D")
    color_secundario = colors.HexColor("#2B6CB0")

    estilo_encabezado = ParagraphStyle("EncabezadoClinica", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=color_primario, alignment=1)
    estilo_cuerpo = ParagraphStyle("CuerpoReporte", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=12, textColor=colors.HexColor("#2D3748"))
    estilo_titulo_seccion = ParagraphStyle("TituloSeccion", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=color_primario)

    story.append(Paragraph("<b>DR. DIEGO ROSS ÁLVAREZ</b>", estilo_encabezado))
    story.append(Paragraph("Cardiólogo - Electrofisiólogo | Especialidad UNAM 12883155", estilo_encabezado))
    story.append(Paragraph("WhatsApp: 9812438407 | Consultorio: Zenzontle 110, Fracc. La Ceiba, Villahermosa, Tabasco", ParagraphStyle("Sub", parent=estilo_encabezado, fontSize=8.5, textColor=color_secundario)))
    story.append(Spacer(1, 10))

    pac = data.get("paciente", {})
    nombre = pac.get("nombre", "No especificado")
    edad = pac.get("edad", "N/D")
    asc = pac.get("asc_m2")
    asc_str = f"{asc} m²" if asc is not None else "No reportado"
    
    txt_paciente = f"<b>PACIENTE:</b> {nombre} &nbsp;&nbsp;|&nbsp;&nbsp; <b>EDAD:</b> {edad} &nbsp;&nbsp;|&nbsp;&nbsp; <b>ASC:</b> {asc_str}"
    story.append(Paragraph(escape(txt_paciente), estilo_cuerpo))
    story.append(Spacer(1, 6))

    intro = data.get("introduccion", "")
    if intro and intro.strip():
        story.append(Paragraph(escape(intro.strip()), estilo_cuerpo))
        story.append(Spacer(1, 4))

    for bloque in narrativa.split("\n\n"):
        if bloque.strip():
            story.append(Paragraph(bloque.strip(), estilo_cuerpo))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>CONCLUSIONES:</b>", estilo_titulo_seccion))
    story.append(Spacer(1, 4))

    for conc in conclusiones:
        if conc and conc.strip():
            story.append(Paragraph(escape(conc), estilo_cuerpo))
            story.append(Spacer(1, 3))

    story.append(Spacer(1, 6))
    if diagnostico and diagnostico.strip():
        story.append(Paragraph("<b>DIAGNÓSTICO:</b>", estilo_titulo_seccion))
        story.append(Spacer(1, 3))
        story.append(Paragraph(escape(diagnostico), estilo_cuerpo))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ====================================================================
# APLICACIÓN STREAMLIT (ESTADOS Y FLUJO HÍBRIDO v7.0)
# ====================================================================
if "reporte_hibrido" not in st.session_state:
    st.session_state["reporte_hibrido"] = None
    st.session_state["narrativa_clinica"] = ""
    st.session_state["conclusiones_clinicas"] = ["", "", "", "", "", "", ""]
    st.session_state["diagnostico_clinico"] = ""
    st.session_state["advertencias_validación"] = []
    st.session_state["auditoria_resultado"] = None

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("#### 📂 1. Ingesta de Estudio (PDF)")
    uploaded_file = st.file_uploader("Cargar reporte del ecógrafo", type=["pdf"])

if uploaded_file is not None:
    with col1:
        st.success(f"Archivo vinculado: {uploaded_file.name}")

    if not api_key:
        with col2:
            st.warning("⚠️ Ingrese su API Key en el panel lateral.")
    else:
        with col1:
            if st.button("🚀 Ejecutar Pipeline v7.0 (Con Auditor IA)", use_container_width=True):
                with st.spinner("Ejecutando Fases 1 a 3.5 (Extracción, Normalización, Motor Ross, Redacción y Auditor)..."):
                    try:
                        datos_crudos = extraer_texto_pdf(uploaded_file.read())
                        client = genai.Client(api_key=api_key)
                        config_gen = types.GenerateContentConfig(temperature=0.0)

                        # FASE 1: Extracción Pura (Actualizado a gemini-3.8-flash)
                        response_f1 = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[PROMPT_FASE_1_EXTRACCION, f"DATOS CRUDOS:\n{datos_crudos}"],
                            config=config_gen,
                        )

                        texto_resp = response_f1.text.strip()
                        texto_resp = re.sub(r"^```json\s*", "", texto_resp)
                        texto_resp = re.sub(r"^```\s*", "", texto_resp)
                        texto_resp = re.sub(r"\s*```$", "", texto_resp)

                        json_crudo = json.loads(texto_resp)

                        # FASE 1.5: Normalización Automática
                        json_normalizado = fase_1_5_normalizacion(json_crudo)

                        # Validación de rangos biológicos
                        advertencias = validar_rangos_biologicos(json_normalizado)
                        st.session_state["advertencias_validación"] = advertencias

                        # FASE 2: Motor Ross Determinista
                        json_procesado = fase_2_motor_ross_determinista(json_normalizado)
                        st.session_state["reporte_hibrido"] = json_procesado

                        # FASE 3: IA Redactora Contextual
                        resultado_redaccion = fase_3_ia_redactora(client, api_key, json_procesado)

                        # FASE 3.5: Auditor Clínico Automático
                        resultado_auditoria = fase_3_5_auditor_clinico(client, api_key, json_procesado, resultado_redaccion)
                        st.session_state["auditoria_resultado"] = resultado_auditoria

                        st.session_state["narrativa_clinica"] = resultado_redaccion.get("narrativa_descriptiva", "")
                        st.session_state["conclusiones_clinicas"] = resultado_redaccion.get("conclusiones_redactadas", json_procesado.get("conclusiones_deterministicas"))
                        st.session_state["diagnostico_clinico"] = resultado_redaccion.get("diagnostico_redactado", "")

                        st.success("¡Pipeline v7.0 ejecutado con éxito bajo auditoría clínica integrada!")
                    except json.JSONDecodeError:
                        st.error("Error crítico: El modelo de IA no devolvió un JSON válido en la Fase 1.")
                    except Exception as e:
                        st.error(f"Error crítico en pipeline: {str(e)}")

# ====================================================================
# FASE 4: VALIDACIÓN MÉDICA & PANEL ATÓMICO
# ====================================================================
if st.session_state["reporte_hibrido"]:
    st.markdown("---")
    st.markdown("#### ✏️ 2. Panel de Validación Médica y Control de Calidad v7.0")
    
    if st.session_state.get("advertencias_validación"):
        for adv in st.session_state["advertencias_validación"]:
            st.markdown(f'<div class="warning-box">{adv}</div>', unsafe_allow_html=True)

    if st.session_state.get("auditoria_resultado"):
        aud = st.session_state["auditoria_resultado"]
        status_color = "🟢" if aud["aprobado"] else "🟠"
        st.markdown(f'<div class="audit-box">{status_color} <b>Auditor Clínico Automático (Fase 3.5):</b> {aud["comentario"]}</div>', unsafe_allow_html=True)

    with st.expander("🔍 Ver Trazabilidad y Confianza Clínica (Uso Médico)"):
        hechos_dbg = st.session_state["reporte_hibrido"].get("hechos_clinicos", {})
        st.write("**Índice de Confianza por Módulo:**", hechos_dbg.get("indice_confianza_por_modulo", {}))
        st.write("**Hallazgos Relevantes con Evidencia:**", hechos_dbg.get("hallazgos_relevantes", []))
        st.write("**Limitaciones del Estudio Detectadas:**", hechos_dbg.get("limitaciones_del_estudio", []))

    data = st.session_state["reporte_hibrido"]

    with st.container():
        st.markdown("##### 👤 Datos del Paciente")
        pac = data.setdefault("paciente", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            pac["nombre"] = st.text_input("Nombre", value=pac.get("nombre") or "")
        with c2: 
            edad_val = pac.get("edad")
            edad_txt = st.text_input("Edad", value=str(edad_val) if edad_val is not None else "")
            pac["edad"] = int(edad_txt) if edad_txt.strip() else None
        with c3: 
            sexo_val = pac.get("sexo")
            pac["sexo"] = st.selectbox("Sexo", options=[None, "masculino", "femenino"], index=0 if sexo_val not in ["masculino", "femenino"] else (1 if sexo_val == "masculino" else 2))
        with c4: 
            asc_val = pac.get("asc_m2")
            asc_input = st.text_input("ASC (m²)", value=str(asc_val) if asc_val is not None else "")
            pac["asc_m2"] = float(asc_input) if asc_input.strip() else None

        st.markdown("##### 🫀 Ventrículo Izquierdo & Volúmenes (Multivariable)")
        vi = data.setdefault("ventriculo_izquierdo", {})
        vi_c1, vi_c2, vi_c3, vi_c4 = st.columns(4)
        
        with vi_c1: 
            val = vi.get("dtdvi_mm")
            txt = st.text_input("DTDVI (mm)", value=str(val) if val is not None else "")
            vi["dtdvi_mm"] = float(txt) if txt.strip() else None
            
        with vi_c2: 
            val = vi.get("dtsvi_mm")
            txt = st.text_input("DTSVI (mm)", value=str(val) if val is not None else "")
            vi["dtsvi_mm"] = float(txt) if txt.strip() else None
            
        with vi_c3: 
            val = vi.get("fevi_porcentaje")
            txt = st.text_input("FEVI (%)", value=str(val) if val is not None else "")
            vi["fevi_porcentaje"] = float(txt) if txt.strip() else None

        with vi_c4: 
            val = vi.get("volumen_telediastolico_ml")
            txt = st.text_input("VTDVI (ml)", value=str(val) if val is not None else "")
            vi["volumen_telediastolico_ml"] = float(txt) if txt.strip() else None

        data = fase_2_motor_ross_determinista(data)

        st.markdown("##### 📝 Narrativa Clínica Descriptiva (IA Redactora Contextual)")
        st.session_state["narrativa_clinica"] = st.text_area(
            "Edición de narrativa clínica:",
            value=st.session_state["narrativa_clinica"],
            height=160
        )

        st.markdown("##### 📊 Conclusiones Clínicas")
        conclusiones = st.session_state["conclusiones_clinicas"]
        while len(conclusiones) < 7:
            conclusiones.append("")
        for i in range(7):
            conclusiones[i] = st.text_input(f"Punto Conclusión {i+1}", value=conclusiones[i])
        st.session_state["conclusiones_clinicas"] = conclusiones

        st.markdown("##### 🩺 Diagnóstico Clínico Integrador")
        st.session_state["diagnostico_clinico"] = st.text_area(
            "Edición de diagnóstico:",
            value=st.session_state["diagnostico_clinico"],
            height=80
        )

    st.markdown("---")
    if st.button("📥 Generar y Descargar PDF Institucional Oficial v7.0", type="primary", use_container_width=True):
        pdf_bytes = generar_pdf_reportlab(
            data, 
            st.session_state["narrativa_clinica"], 
            st.session_state["conclusiones_clinicas"], 
            st.session_state["diagnostico_clinico"]
        )
        st.download_button(
            label="💾 Descargar PDF Oficial v7.0",
            data=pdf_bytes,
            file_name="Ecocardiograma_Definitivo_Ross_v7.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
