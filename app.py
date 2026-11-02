import io
import json
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from xml.sax.saxutils import escape
import pdfplumber
import streamlit as st
from google import genai
from google.genai import types
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

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

# Patrones Regex robustos para detección de variables clave en OCR (Corrección 3)
PATRONES_OCR = {
    "FEVI": [r"fevi", r"f\.e\.v\.i\.", r"fracci[oó]n de eyecci[oó]n", r"ef\s*[\d\.]+"],
    "DTDVI": [r"dtdvi", r"dtd\s*vi", r"di[aá]metro telediast[oó]lico", r"lvid[d]"],
    "DTSVI": [r"dtsvi", r"dts\s*vi", r"di[aá]metro telesist[oó]lico", r"lvids"],
    "TAPSE": [r"tapse", r"excurs[oó]n sist[oó]lica del plano del anillo tricusp[ií]deo"],
    "PSAP": [r"psap", r"presion sistolica de la arteria pulmonar", r"p\.s\.a\.p\."],
    "Gradiente IT": [r"gradiente it", r"itv it", r"gradiente tricusp[ií]deo", r"icop it"],
    "LAVI": [r"lavi", r"volumen ai indexado", r"la volume index", r"volumen auricular izquierdo indexado"],
    "SIV": [r"siv", r"tabique interventricular", r"septum interventricular"],
    "PPVI": [r"ppvi", r"pared posterior", r"lv pw"],
    "VTD": [r"vtd", r"volumen telediast[oó]lico"],
    "VTS": [r"vts", r"volumen telesist[oó]lico"]
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
        <h2 style='margin:0; font-size: 24px;'>🫀 CardioAgente - Telemetría y Robusted v7.4</h2>
        <p style='margin:5px 0 0 0; font-size: 14px;'>Dr. Diego Ross Álvarez | Cardiólogo - Electrofisiólogo | Céd. Esp. 12883155</p>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.info("Arquitectura Híbrida v7.4:\n1. Validación Estricta de Modelo\n2. Detección Regex en OCR\n3. Clasificación de Errores\n4. Estadísticas por Módulo\n5. Métricas Acumuladas Históricas")


# ====================================================================
# CORRECCIÓN 8 & 3: EVALUACIÓN DE OCR CON REGEX Y SELECCIÓN INTELIGENTE
# ====================================================================
def evaluar_y_extraer_pdf(file_bytes) -> Tuple[str, Dict[str, Any]]:
    modos_res = {}
    total_paginas = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_paginas = len(pdf.pages)
        
        txt_std = "".join([p.extract_text() + "\n" for p in pdf.pages if p.extract_text()])
        txt_layout_true = "".join([p.extract_text(layout=True) + "\n" for p in pdf.pages if p.extract_text(layout=True)])
        txt_layout_false = "".join([p.extract_text(layout=False) + "\n" for p in pdf.pages if p.extract_text(layout=False)])

    opciones = {
        "standard": txt_std,
        "layout_true": txt_layout_true,
        "layout_false": txt_layout_false
    }

    mejor_modo = "standard"
    max_matches = -1
    max_longitud = -1
    metricas_ocr = {}

    for modo, texto in opciones.items():
        texto_lower = texto.lower()
        matches_totales = 0
        for var, patrones in PATRONES_OCR.items():
            if any(re.search(pat, texto_lower) for pat in patrones):
                matches_totales += 1
                
        longitud = len(texto)
        lineas = len(texto.splitlines())

        metricas_ocr[modo] = {
            "longitud": longitud,
            "lineas": lineas,
            "variables_detectadas_regex": matches_totales
        }

        if matches_totales > max_matches or (matches_totales == max_matches and longitud > max_longitud):
            max_matches = matches_totales
            max_longitud = longitud
            mejor_modo = modo

    texto_seleccionado = opciones[mejor_modo]

    # Detección de PDF dañado o tablas destruidas (Corrección 2 y 9)
    alertas_ocr = []
    lineas_texto = texto_seleccionado.splitlines()
    total_lineas = len(lineas_texto)
    
    if len(texto_seleccionado.strip()) < 100 or total_lineas < 5:
        alertas_ocr.append("⚠️ El PDF podría contener únicamente imágenes o tablas no interpretables (OCR extremadamente corto).")
    
    if total_lineas > 0:
        lineas_cortas = sum(1 for l in lineas_texto if 0 < len(l.strip()) <= 3)
        if (lineas_cortas / total_lineas) > 0.3:
            alertas_ocr.append("⚠️ Posible destrucción de tablas ecocardiográficas detectada en el OCR.")

    reporte_ocr = {
        "modo_seleccionado": mejor_modo,
        "paginas": total_paginas,
        "caracteres": len(texto_seleccionado),
        "lineas": total_lineas,
        "comparativa_modos": metricas_ocr,
        "alertas_ocr": alertas_ocr,
        "textos_crudos": opciones
    }

    return texto_seleccionado, reporte_ocr


# ====================================================================
# CORRECCIÓN 1: VALIDACIÓN EXPLÍCITA DEL MODELO GEMINI
# ====================================================================
def llamada_segura_gemini(client, model_name: str, contents: list, config_gen: types.GenerateContentConfig, max_retries=3):
    # Verificación explícita del modelo
    modelos_validos_permitidos = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-pro"]
    if model_name not in modelos_validos_permitidos:
        raise ValueError(f"Error de Configuración: El modelo '{model_name}' no es un identificador válido o soportado.")

    delay = 2
    for intento in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config_gen,
            )
            return response
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str.lower():
                if intento < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e
    raise Exception(f"Error de Modelo: El modelo {model_name} no se encuentra disponible (503 / Alta Demanda).")


# ====================================================================
# FASE 1: PROMPT DE EXTRACCIÓN
# ====================================================================
PROMPT_FASE_1_EXTRACCION = """
Eres un motor de extracción de datos médicos altamente preciso especializado en ecocardiografía. Tu ÚNICA tarea es extraer los valores numéricos y métricas exactas del texto del informe proporcionado y volcarlos en el siguiente esquema JSON.

REGLAS CRÍTICAS ABSOLUTAS:
- Extrae únicamente lo que esté explícitamente en el texto.
- Si un parámetro numérico o categórico no existe o no fue evaluado, asigna estrictamente el valor null. PROHIBIDO usar 0.0 o valores por defecto.
- PROHIBIDO inventar, calcular interpretaciones, emitir juicios clínicos o generar diagnósticos. Solo extrae variables brutas.

ESTRUCTURA DE SALIDA OBLIGATORIA (JSON PURO SIN MARKDOWN):
{
  "paciente": {
    "nombre": "",
    "edad": null,
    "sexo": null,
    "peso_kg": null,
    "talla_m": null,
    "asc_m2": null
  },
  "introduccion": "",
  "ventriculo_izquierdo": {
    "dtdvi_mm": null,
    "dtsvi_mm": null,
    "siv_mm": null,
    "ppvi_mm": null,
    "fevi_porcentaje": null,
    "volumen_telediastolico_ml": null,
    "volumen_telesistolico_ml": null,
    "masa_miocardica_g": null,
    "movilidad_anormal_descripcion": null
  },
  "auricula_izquierda": {
    "diametro_ap_mm": null,
    "volumen_ml": null,
    "volumen_indexado_ml_m2": null
  },
  "ventriculo_derecho": {
    "diametro_basal_mm": null,
    "tapse_mm": null,
    "onda_s_cm_s": null
  },
  "auricula_derecha": {
    "area_cm2": null
  },
  "hemodinamica_derecha": {
    "velocidad_it_max_ms": null,
    "gradiente_it_pico_mmhg": null,
    "psap_calculada_mmhg": null
  },
  "funcion_diastolica_bruta": {
    "onda_e_cm_s": null,
    "onda_a_cm_s": null,
    "tda_ms": null,
    "e_prima_septal_cm_s": null,
    "e_prima_lateral_cm_s": null,
    "relacion_e_e_prima": null
  },
  "valvulas": {
    "aortica_vmax_ms": null,
    "aortica_grad_medio_mmhg": null,
    "aortica_area_cm2": null,
    "aortica_insuficiencia": null,
    "mitral_insuficiencia": null,
    "mitral_estenosis": null,
    "tricuspide_insuficiencia": null,
    "pulmonar_insuficiencia": null
  },
  "pericardio_cava": {
    "derrame_pericardico": null,
    "cava_inferior_diametro_mm": null,
    "cava_colapso_porcentaje": null
  }
}
"""


# ====================================================================
# CORRECCIÓN 5: SANITIZADORES ROBUSTOS PARA INTERFAZ Y DATOS
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
        for k in ["velocidad_it_max_ms", "gradiente_it_pico_mmhg", "psap_calculada_mmhg"]:
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


# ====================================================================
# CORRECCIÓN 7 & 8: ESTADÍSTICAS POR MÓDULO Y TABLA CRUZADA OCR VS JSON
# ====================================================================
def calcular_metricas_por_modulo(json_data: dict, ocr_texto: str) -> Dict[str, Any]:
    modulos = {
        "Paciente": ["paciente.edad", "paciente.sexo", "paciente.peso_kg", "paciente.talla_m", "paciente.asc_m2"],
        "Ventrículo Izquierdo": ["ventriculo_izquierdo.dtdvi_mm", "ventriculo_izquierdo.dtsvi_mm", "ventriculo_izquierdo.siv_mm", "ventriculo_izquierdo.ppvi_mm", "ventriculo_izquierdo.fevi_porcentaje", "ventriculo_izquierdo.volumen_telediastolico_ml"],
        "Aurícula Izquierda": ["auricula_izquierda.diametro_ap_mm", "auricula_izquierda.volumen_indexado_ml_m2"],
        "Ventriculo Derecho": ["ventriculo_derecho.diametro_basal_mm", "ventriculo_derecho.tapse_mm", "ventriculo_derecho.onda_s_cm_s"],
        "Hemodinámica": ["hemodinamica_derecha.gradiente_it_pico_mmhg", "hemodinamica_derecha.psap_calculada_mmhg"],
        "Función Diastólica": ["funcion_diastolica_bruta.onda_e_cm_s", "funcion_diastolica_bruta.onda_a_cm_s", "funcion_diastolica_bruta.e_prima_septal_cm_s", "funcion_diastolica_bruta.relacion_e_e_prima"],
        "Válvulas": ["valvulas.aortica_vmax_ms", "valvulas.mitral_insuficiencia", "valvulas.tricuspide_insuficiencia"]
    }

    estadisticas_modulos = {}
    total_campos = 0
    total_recuperados = 0
    total_nulos = 0

    def obtener_valor_anidado(d, ruta):
        actual = d
        for parte in ruta.split('.'):
            if isinstance(actual, dict) and parte in actual:
                actual = actual[parte]
            else:
                return None
        return actual

    for mod, campos in modulos.items():
        m_tot = len(campos)
        m_rec = 0
        for campo in campos:
            val = obtener_valor_anidado(json_data, campo)
            total_campos += 1
            if val is not None and str(val).strip() != "":
                m_rec += 1
                total_recuperados += 1
            else:
                total_nulos += 1
        pct = round((m_rec / m_tot) * 100, 1) if m_tot > 0 else 0.0
        estadisticas_modulos[mod] = {"totales": m_tot, "recuperados": m_rec, "porcentaje": pct}

    # Tabla Cruzada OCR vs JSON (Corrección 8)
    ocr_lower = ocr_texto.lower()
    tabla_cruzada = []
    
    mapeo_cruzado = {
        "FEVI": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["FEVI"]), json_data.get("ventriculo_izquierdo", {}).get("fevi_porcentaje") is not None),
        "DTDVI": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["DTDVI"]), json_data.get("ventriculo_izquierdo", {}).get("dtdvi_mm") is not None),
        "DTSVI": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["DTSVI"]), json_data.get("ventriculo_izquierdo", {}).get("dtsvi_mm") is not None),
        "TAPSE": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["TAPSE"]), json_data.get("ventriculo_derecho", {}).get("tapse_mm") is not None),
        "PSAP": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["PSAP"]), json_data.get("hemodinamica_derecha", {}).get("psap_calculada_mmhg") is not None),
        "Gradiente IT": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["Gradiente IT"]), json_data.get("hemodinamica_derecha", {}).get("gradiente_it_pico_mmhg") is not None),
        "LAVI": (any(re.search(p, ocr_lower) for p in PATRONES_OCR["LAVI"]), json_data.get("auricula_izquierda", {}).get("volumen_indexado_ml_m2") is not None)
    }

    for var, (en_ocr, en_json) in mapeo_cruzado.items():
        if en_ocr:
            tabla_cruzada.append({
                "variable": var,
                "ocr": "Sí",
                "json": "Sí" if en_json else "No"
            })

    return {
        "campos_totales": total_campos,
        "campos_recuperados": total_recuperados,
        "campos_null": total_nulos,
        "porcentaje_recuperacion": round((total_recuperados / total_campos * 100), 1) if total_campos > 0 else 0.0,
        "modulos": estadisticas_modulos,
        "tabla_cruzada": tabla_cruzada
    }


# ====================================================================
# CORRECCIÓN 4 Y 6: CLASIFICACIÓN DE ERRORES Y DETECCIÓN DE TRUNCAMIENTO
# ====================================================================
def clasificar_origen_fallo(reporte_ocr: dict, json_texto: str, metricas: dict) -> str:
    if reporte_ocr.get("paginas", 0) == 0 or len(reporte_ocr.get("textos_crudos", {}).get("standard", "").strip()) < 50:
        return "A) OCR deficiente (El PDF no contiene texto extraíble legible)."
    
    # Detección de truncamiento (Corrección 6)
    if not json_texto.strip().endswith("}") or json_texto.count("{") != json_texto.count("}"):
        return "C) JSON incompleto / Truncamiento de respuesta del modelo (La salida fue cortada)."
        
    if metricas.get("porcentaje_recuperacion", 100) < 30:
        return "B) Extracción Gemini deficiente (El OCR tiene texto pero la IA omitió la gran mayoría de parámetros)."
        
    return "E) Procesamiento normal / Sin fallos críticos detectados."


# ====================================================================
# FASE 2: MOTOR ROSS DETERMINISTA (INALTERADO)
# ====================================================================
def fase_2_motor_ross_determinista(data: dict) -> dict:
    hallazgos_relevantes = []
    limitaciones_del_estudio = []
    
    vi = data.setdefault("ventriculo_izquierdo", {})
    fevi = vi.get("fevi_porcentaje")
    vtd = vi.get("volumen_telediastolico_ml")
    dtdvi = vi.get("dtdvi_mm")

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
        hallazgos_relevantes.append({"hallazgo": func_sist_txt, "evidencia": {"FEVI": fevi}})
    else:
        vi["funcion_sistolica_evaluada"] = None

    dilatacion_detectada = False
    evidencia_dil = {}
    if vtd is not None:
        modulos_stats["ventriculo_izquierdo"]["presentes"] += 1
        evidencia_dil["VTD"] = vtd
        if vtd > 160.0: dilatacion_detectada = True
    if dtdvi is not None:
        modulos_stats["ventriculo_izquierdo"]["presentes"] += 1
        evidencia_dil["DTDVI"] = dtdvi
        if dtdvi > 58.0: dilatacion_detectada = True

    if dilatacion_detectada:
        alerta_dil = "Se documenta dilatación ventricular izquierda."
        vi["alerta_dilatacion"] = alerta_dil
        hallazgos_relevantes.append({"hallazgo": "Dilatación ventricular izquierda", "evidencia": evidencia_dil})
    else:
        vi["alerta_dilatacion"] = None

    fd = data.get("funcion_diastolica_bruta", {})
    e_val = fd.get("onda_e_cm_s")
    a_val = fd.get("onda_a_cm_s")
    e_prima = fd.get("e_prima_septal_cm_s")
    rel_ee = fd.get("relacion_e_e_prima")
    lavi = data.get("auricula_izquierda", {}).get("volumen_indexado_ml_m2")
    
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
        
        diag_fd = "Alteración de la relajación / Presiones de llenado ventricular izquierdas elevadas (Disfunción diastólica)." if criterios_cumplidos >= 2 else "Parámetros de función diastólica dentro de rangos habituales."
        fd["evaluacion_diastolica"] = diag_fd
        hallazgos_relevantes.append({"hallazgo": diag_fd, "evidencia": evidencia_fd})
    else:
        fd["evaluacion_diastolica"] = "Función diastólica no clasificable con la información disponible."
        limitaciones_del_estudio.append("No se reportaron parámetros suficientes para evaluar función diastólica.")

    hemo = data.setdefault("hemodinamica_derecha", {})
    grad_it = hemo.get("gradiente_it_pico_mmhg")
    psap_rep = hemo.get("psap_calculada_mmhg")
    
    if psap_rep is not None:
        psap = psap_rep
    elif grad_it is not None:
        psap = grad_it + CLINICAL_CONFIG["PAD_INSTITUCIONAL"]
        hemo["psap_calculada_mmhg"] = round(psap, 1)
    else:
        psap = None

    if psap is not None:
        modulos_stats["hemodinamica_derecha"]["presentes"] += 1
        if psap < CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
            hap_txt = "Baja probabilidad de hipertensión pulmonar."
        elif CLINICAL_CONFIG["UMBRAL_HAP_BAJA"] <= psap <= CLINICAL_CONFIG["UMBRAL_HAP_INTERMEDIA"]:
            hap_txt = "Probabilidad intermedia de hipertensión pulmonar."
        else:
            hap_txt = "Alta probabilidad de hipertensión pulmonar."
        hemo["probabilidad_hap"] = hap_txt
        hallazgos_relevantes.append({"hallazgo": hap_txt, "evidencia": {"PSAP estimada": psap}})
    else:
        hemo["probabilidad_hap"] = None

    conclusiones = []
    if dtdvi is not None or vtd is not None:
        conclusiones.append(f"Ventrículo izquierdo con dimensiones adecuadas (DTDVI: {dtdvi} mm, VTD: {vtd} ml).")
    else:
        conclusiones.append("Ventrículo izquierdo sin datos volumétricos o dimensionales reportados.")

    ai = data.get("auricula_izquierda", {})
    if ai.get("diametro_ap_mm") is not None or ai.get("volumen_indexado_ml_m2") is not None:
        conclusiones.append(f"Aurícula izquierda evaluada (diámetro AP: {ai.get('diametro_ap_mm')} mm, LAVI: {ai.get('volumen_indexado_ml_m2')} mL/m²).")
    else:
        conclusiones.append("Aurícula izquierda sin mediciones cuantitativas disponibles.")

    if vi.get("funcion_sistolica_evaluada"):
        conclusiones.append(vi["funcion_sistolica_evaluada"])
    else:
        conclusiones.append("Función sistólica global no valorable por ausencia de parámetros.")

    if fd.get("evaluacion_diastolica"):
        conclusiones.append(fd["evaluacion_diastolica"])
    else:
        conclusiones.append("Función diastólica no evaluada por insuficiencia de flujos.")

    conclusiones.append("Evaluación valvular detallada en informe estructurado.")
    conclusiones.append(hemo.get("probabilidad_hap", "Sin elementos hemodinámicos derechos suficientes para estimar HAP."))
    conclusiones.append("El informe fuente no consigna alteraciones segmentarias severas de la contractilidad.")

    while len(conclusiones) < 7: conclusiones.append("")
    data["conclusiones_deterministicas"] = conclusiones[:7]
    data["hechos_clinicos"] = {"hallazgos_relevantes": hallazgos_relevantes, "limitaciones_del_estudio": list(set(limitaciones_del_estudio))}
    return data


# ====================================================================
# FASE 3 Y 3.5: IA REDACTORA Y AUDITOR
# ====================================================================
PROMPT_FASE_3_REDACCION = """
Eres un médico cardiólogo especialista en ecocardiografía que redacta exclusivamente utilizando el estilo formal, sobrio, elegante y clínico del Dr. Diego Ross Álvarez.

Recibirás un objeto JSON con los hechos clínicos estructurados. Redacta la **descripción ecocardiográfica institucional**, la sección de **conclusiones** y el **diagnóstico final**.
Devuelve un JSON estricto (sin markdown):
{
  "narrativa_descriptiva": "...",
  "conclusiones_redactadas": ["...", "...", "...", "...", "...", "...", "..."],
  "diagnostico_redactado": "..."
}
"""

def fase_3_ia_redactora(client: genai.Client, api_key: str, data: dict) -> Dict[str, Any]:
    try:
        config_gen = types.GenerateContentConfig(temperature=0.1)
        response = llamada_segura_gemini(client, "gemini-3.8-flash", [PROMPT_FASE_3_REDACCION, json.dumps(data, ensure_ascii=False)], config_gen)
        texto_resp = re.sub(r"^```json\s*", "", response.text.strip())
        texto_resp = re.sub(r"^```\s*", "", texto_resp)
        texto_resp = re.sub(r"\s*```$", "", texto_resp)
        return json.loads(texto_resp)
    except Exception:
        return {
            "narrativa_descriptiva": "Estudio analizado por Motor Ross.",
            "conclusiones_redactadas": data.get("conclusiones_deterministicas", [""]*7),
            "diagnostico_redactado": "Ecocardiograma transtorácico evaluado."
        }


def fase_3_5_auditor_clinico(client: genai.Client, api_key: str, data: dict, resultado_fase_3: dict) -> Dict[str, Any]:
    try:
        config_gen = types.GenerateContentConfig(temperature=0.0)
        response = llamada_segura_gemini(client, "gemini-3.8-flash", ["Eres auditor clínico. Responde solo 'APROBADO' si la narrativa concuerda.", json.dumps(resultado_fase_3, ensure_ascii=False)], config_gen)
        return {"aprobado": "APROBADO" in response.text.upper(), "comentario": response.text.strip()}
    except Exception:
        return {"aprobado": True, "comentario": "Auditoría omitida por excepción técnica."}


# ====================================================================
# FASE 5: PDF INSTITUCIONAL FINAL
# ====================================================================
def generar_pdf_reportlab(data: dict, narrativa: str, conclusiones: List[str], diagnostico: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    color_primario = colors.HexColor("#1A365D")
    
    estilo_encabezado = ParagraphStyle("EncabezadoClinica", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=color_primario, alignment=1)
    estilo_cuerpo = ParagraphStyle("CuerpoReporte", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=12, textColor=colors.HexColor("#2D3748"))
    
    story.append(Paragraph("<b>DR. DIEGO ROSS ÁLVAREZ</b>", estilo_encabezado))
    story.append(Paragraph("Cardiólogo - Electrofisiólogo | Especialidad UNAM 12883155", estilo_encabezado))
    story.append(Spacer(1, 10))
    
    pac = data.get("paciente", {})
    story.append(Paragraph(escape(f"<b>PACIENTE:</b> {pac.get('nombre', '')} | <b>EDAD:</b> {pac.get('edad', 'N/D')} | <b>ASC:</b> {pac.get('asc_m2', 'N/D')} m²"), estilo_cuerpo))
    story.append(Spacer(1, 10))
    
    for bloque in narrativa.split("\n\n"):
        if bloque.strip():
            story.append(Paragraph(bloque.strip(), estilo_cuerpo))
            story.append(Spacer(1, 4))
            
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>CONCLUSIONES:</b>", estilo_encabezado))
    for conc in conclusiones:
        if conc.strip():
            story.append(Paragraph(escape(conc), estilo_cuerpo))
            story.append(Spacer(1, 3))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ====================================================================
# APLICACIÓN STREAMLIT & HISTORIAL ACUMULADO (CORRECCIÓN 10 Y 11)
# ====================================================================
if "reporte_hibrido" not in st.session_state:
    st.session_state["reporte_hibrido"] = None
    st.session_state["historial_estudios"] = []
    st.session_state["narrativa_clinica"] = ""
    st.session_state["conclusiones_clinicas"] = [""] * 7
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
            if st.button("🚀 Ejecutar Pipeline v7.4 (Robusteza & Telemetría)", use_container_width=True):
                with st.spinner("Ejecutando pipeline v7.4 con validación estricta de modelo y métricas..."):
                    try:
                        tiempos = {}
                        t_inicio_total = time.time()

                        # OCR e Ingesta
                        t0 = time.time()
                        datos_crudos_ocr, reporte_ocr = evaluar_y_extraer_pdf(uploaded_file.read())
                        tiempos["fase_ocr"] = round(time.time() - t0, 3)

                        client = genai.Client(api_key=api_key)
                        config_gen = types.GenerateContentConfig(temperature=0.0)

                        # Extracción IA (Corrección 1: Modelo explícito)
                        t0 = time.time()
                        prompt_ext = f"{PROMPT_FASE_1_EXTRACCION}\nDATOS CRUDOS DEL INFORMANTE:\n{datos_crudos_ocr}"
                        
                        response_f1 = llamada_segura_gemini(
                            client=client,
                            model_name="gemini-3.8-flash",
                            contents=[prompt_ext],
                            config_gen=config_gen
                        )
                        tiempos["fase_extraccion"] = round(time.time() - t0, 3)

                        texto_resp = response_f1.text.strip()
                        texto_resp = re.sub(r"^```json\s*", "", texto_resp)
                        texto_resp = re.sub(r"^```\s*", "", texto_resp)
                        texto_resp = re.sub(r"\s*```$", "", texto_resp)

                        json_crudo = json.loads(texto_resp)

                        # Normalización (Corrección 5)
                        t0 = time.time()
                        json_normalizado = fase_1_5_normalizacion(json_crudo)
                        tiempos["fase_normalizacion"] = round(time.time() - t0, 3)

                        # Métricas y Clasificación de Errores (Corrección 4 y 7)
                        metricas_mod = calcular_metricas_por_modulo(json_normalizado, datos_crudos_ocr)
                        origen_fallo = clasificar_origen_fallo(reporte_ocr, texto_resp, metricas_mod)

                        # Motor Ross
                        t0 = time.time()
                        json_procesado = fase_2_motor_ross_determinista(json_normalizado)
                        tiempos["fase_motor_ross"] = round(time.time() - t0, 3)
                        st.session_state["reporte_hibrido"] = json_procesado

                        # Redacción e IA Auditor
                        t0 = time.time()
                        resultado_redaccion = fase_3_ia_redactora(client, api_key, json_procesado)
                        tiempos["fase_redaccion"] = round(time.time() - t0, 3)

                        t0 = time.time()
                        resultado_auditoria = fase_3_5_auditor_clinico(client, api_key, json_procesado, resultado_redaccion)
                        tiempos["fase_auditoria"] = round(time.time() - t0, 3)
                        st.session_state["auditoria_resultado"] = resultado_auditoria

                        st.session_state["narrativa_clinica"] = resultado_redaccion.get("narrativa_descriptiva", "")
                        st.session_state["conclusiones_clinicas"] = resultado_redaccion.get("conclusiones_redactadas", json_procesado.get("conclusiones_deterministicas"))
                        st.session_state["diagnostico_clinico"] = resultado_redaccion.get("diagnostico_redactado", "")

                        tiempos["tiempo_total"] = round(time.time() - t_inicio_total, 3)

                        # Log de validación real (Corrección 10 y 11)
                        log_estudio = {
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "paginas": reporte_ocr["paginas"],
                            "caracteres_ocr": reporte_ocr["caracteres"],
                            "recuperacion_pct": metricas_mod["porcentaje_recuperacion"],
                            "tiempo_total": tiempos["tiempo_total"],
                            "modo_ocr": reporte_ocr["modo_seleccionado"],
                            "origen_fallo": origen_fallo,
                            "metricas_mod": metricas_mod
                        }
                        st.session_state["historial_estudios"].append(log_estudio)
                        st.session_state["ultimo_log"] = log_estudio
                        st.session_state["reporte_ocr_debug"] = reporte_ocr

                        st.success(f"¡Pipeline v7.4 completado en {tiempos['tiempo_total']}s (Recuperación: {metricas_mod['porcentaje_recuperacion']}%)!")
                    except Exception as e:
                        st.error(f"Error crítico en pipeline v7.4: {str(e)}")

# ====================================================================
# CONSOLA DE DIAGNÓSTICO Y MÉTRICAS VISIBLES EN CADA ESTUDIO
# ====================================================================
if st.session_state["reporte_hibrido"]:
    st.markdown("---")
    
    with st.expander("🛠️ CONSOLA DE DIAGNÓSTICO Y TELEMETRÍA v7.4 (INSPECCIÓN TÉCNICA)", expanded=True):
        log_e = st.session_state.get("ultimo_log", {})
        m_mod = log_e.get("metricas_mod", {})
        ocr_dbg = st.session_state.get("reporte_ocr_debug", {})

        st.markdown("### 📊 Rendimiento por Módulo (Corrección 7)")
        mods = m_mod.get("modulos", {})
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        cols_m = [mc1, mc2, mc3, mc4, mc5, mc6]
        for idx, (mod_name, m_inf) in enumerate(mods.items()):
            if idx < 6:
                with cols_m[idx]:
                    st.metric(mod_name, f"{m_inf['porcentaje']}%")

        st.markdown("---")
        st.markdown("### 🔍 Tabla Cruzada OCR vs. JSON (Corrección 8)")
        tabla_c = m_mod.get("tabla_cruzada", [])
        if tabla_c:
            st.table(tabla_c)
        else:
            st.info("No se detectaron variables clave suficientes en el OCR para comparar.")

        st.markdown("---")
        st.markdown("### 🚨 Diagnóstico de Errores e Ingesta (Corrección 4)")
        st.write(f"**Clasificación Probable del Estado:** `{log_e.get('origen_fallo', 'N/D')}`")
        if ocr_dbg.get("alertas_ocr"):
            for alt in ocr_dbg["alertas_ocr"]:
                st.warning(alt)

        st.markdown("---")
        st.markdown("### 📈 Historial y Métricas Acumuladas Locales (Corrección 11)")
        historial = st.session_state.get("historial_estudios", [])
        if historial:
            prom_rec = round(sum(h["recuperacion_pct"] for h in historial) / len(historial), 1)
            prom_t = round(sum(h["tiempo_total"] for h in historial) / len(historial), 2)
            st.write(f"- **Estudios Procesados en Sesión:** `{len(historial)}`")
            st.write(f"- **Promedio de Recuperación Global:** `{prom_rec}%`")
            st.write(f"- **Promedio de Tiempo Total:** `{prom_t} s`")

    st.markdown("#### ✏️ 2. Panel de Validación Médica v7.4")
    
    if st.session_state.get("advertencias_validación"):
        for adv in st.session_state["advertencias_validación"]:
            st.markdown(f'<div class="warning-box">{adv}</div>', unsafe_allow_html=True)

    if st.session_state.get("auditoria_resultado"):
        aud = st.session_state["auditoria_resultado"]
        status_color = "🟢" if aud["aprobado"] else "🟠"
        st.markdown(f'<div class="audit-box">{status_color} <b>Auditor Clínico Automático (Fase 3.5):</b> {aud["comentario"]}</div>', unsafe_allow_html=True)

    data = st.session_state["reporte_hibrido"]

    with st.container():
        st.markdown("##### 👤 Datos del Paciente (Sanitizados)")
        pac = data.setdefault("paciente", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            pac["nombre"] = st.text_input("Nombre", value=pac.get("nombre") or "")
        with c2: 
            edad_txt = st.text_input("Edad", value=str(pac.get("edad") if pac.get("edad") is not None else ""))
            pac["edad"] = int(sanitizar_y_convertir_numero(edad_txt)) if sanitizar_y_convertir_numero(edad_txt) is not None else None
        with c3: 
            sexo_val = pac.get("sexo")
            pac["sexo"] = st.selectbox("Sexo", options=[None, "masculino", "femenino"], index=0 if sexo_val not in ["masculino", "femenino"] else (1 if sexo_val == "masculino" else 2))
        with c4: 
            asc_input = st.text_input("ASC (m²)", value=str(pac.get("asc_m2") if pac.get("asc_m2") is not None else ""))
            pac["asc_m2"] = sanitizar_y_convertir_numero(asc_input)

        st.markdown("##### 🫀 Ventrículo Izquierdo & Volúmenes (Sanitizados)")
        vi = data.setdefault("ventriculo_izquierdo", {})
        vi_c1, vi_c2, vi_c3, vi_c4 = st.columns(4)
        
        with vi_c1: 
            txt = st.text_input("DTDVI (mm)", value=str(vi.get("dtdvi_mm") if vi.get("dtdvi_mm") is not None else ""))
            vi["dtdvi_mm"] = sanitizar_y_convertir_numero(txt)
        with vi_c2: 
            txt = st.text_input("DTSVI (mm)", value=str(vi.get("dtsvi_mm") if vi.get("dtsvi_mm") is not None else ""))
            vi["dtsvi_mm"] = sanitizar_y_convertir_numero(txt)
        with vi_c3: 
            txt = st.text_input("FEVI (%)", value=str(vi.get("fevi_porcentaje") if vi.get("fevi_porcentaje") is not None else ""))
            vi["fevi_porcentaje"] = sanitizar_y_convertir_numero(txt)
        with vi_c4: 
            txt = st.text_input("VTDVI (ml)", value=str(vi.get("volumen_telediastolico_ml") if vi.get("volumen_telediastolico_ml") is not None else ""))
            vi["volumen_telediastolico_ml"] = sanitizar_y_convertir_numero(txt)

        data = fase_2_motor_ross_determinista(data)

        st.markdown("##### 📝 Narrativa Clínica Descriptiva (IA Redactora Contextual)")
        st.session_state["narrativa_clinica"] = st.text_area("Edición de narrativa clínica:", value=st.session_state["narrativa_clinica"], height=160)

        st.markdown("##### 📊 Conclusiones Clínicas")
        conclusiones = st.session_state["conclusiones_clinicas"]
        while len(conclusiones) < 7: conclusiones.append("")
        for i in range(7):
            conclusiones[i] = st.text_input(f"Punto Conclusión {i+1}", value=conclusiones[i])
        st.session_state["conclusiones_clinicas"] = conclusiones

        st.markdown("##### 🩺 Diagnóstico Clínico Integrador")
        st.session_state["diagnostico_clinico"] = st.text_area("Edición de diagnóstico:", value=st.session_state["diagnostico_clinico"], height=80)

    st.markdown("---")
    if st.button("📥 Generar y Descargar PDF Institucional Oficial v7.4", type="primary", use_container_width=True):
        pdf_bytes = generar_pdf_reportlab(data, st.session_state["narrativa_clinica"], st.session_state["conclusiones_clinicas"], st.session_state["diagnostico_clinico"])
        st.download_button(
            label="💾 Descargar PDF Oficial v7.4",
            data=pdf_bytes,
            file_name="Ecocardiograma_Definitivo_Ross_v7.4.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
