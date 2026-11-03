import io
import json
import os
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import pdfplumber
import streamlit as st
from google import genai
from google.genai import types

# ====================================================================
# CONFIGURACIÓN Y PERSISTENCIA DE LOTE (APP 1 - V10.0 CEREBRO CLÍNICO)
# ====================================================================
HISTORIAL_FILE = "historial_lote_extractor_v10.json"

def cargar_historial_disco() -> List[dict]:
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial_disco(historial: List[dict]):
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

CLINICAL_CONFIG = {
    "PAD_INSTITUCIONAL": 5.0,
    "UMBRAL_HAP_BAJA": 35.0,
    "UMBRAL_HAP_INTERMEDIA": 50.0,
}

PATRONES_OCR_RECALL = {
    "fevi_porcentaje": [r"fevi", r"f\.e\.v\.i\.", r"fracci[oó]n de eyecci[oó]n", r"ef\s*[:=]?\s*\d+"],
    "dtdvi_mm": [r"dtdvi", r"dtd\s*vi", r"di[aá]metro telediast[oó]lico"],
    "dtsvi_mm": [r"dtsvi", r"dts\s*vi", r"di[aá]metro telesist[oó]lico"],
    "tapse_mm": [r"tapse", r"excurs[oó]n sist[oó]lica"],
    "psap_calculada_mmhg": [r"psap", r"presion sistolica de la arteria pulmonar"],
    "volumen_telediastolico_ml": [r"vtd", r"volumen telediast[oó]lico"],
    "volumen_indexado_ml_m2": [r"lavi", r"volumen ai indexado", r"la volume index"]
}

st.set_page_config(
    page_title="CardioAgente | Extractor Clínico Maestro v10.0",
    page_icon="🧬",
    layout="wide",
)

st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .clinic-header {
            padding: 15px;
            background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="clinic-header">
        <h2 style='margin:0; font-size: 24px;'>🧬 CardioAgente - Extractor Clínico Maestro v10.0 (Cerebro Clínico)</h2>
        <p style='margin:5px 0 0 0; font-size: 14px;'>Dr. Diego Ross Álvarez | Redacción Humana Fluida | Cero Normalidad en Hallazgos | Diagnóstico Médico Integrado</p>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Configuración del Cerebro Clínico")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.info("Directiva v10.0:\n• Redacción médica natural y variada\n• Normalidad excluida de hallazgos relevantes\n• Conclusiones sin mediciones aisladas\n• Diagnóstico en formato de impresión clínica")


# ====================================================================
# OCR ADAPTATIVO
# ====================================================================
def extraer_pdf_adaptativo(file_bytes) -> Tuple[str, Dict[str, Any]]:
    texto_completo = ""
    total_paginas = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_paginas = len(pdf.pages)
        for p in pdf.pages:
            t = p.extract_text(layout=False)
            if not t or len(t.strip()) < 50:
                t = p.extract_text(layout=True)
            if t:
                texto_completo += t + "\n"

    caracteres = len(texto_completo)
    lineas = len(texto_completo.splitlines())
    alertas_ocr = []

    if caracteres > 35000:
        alertas_ocr.append("⚠️ Advertencia: OCR excesivamente largo (>35,000 caracteres).")
    if caracteres < 100 or lineas < 5:
        alertas_ocr.append("⚠️ El PDF podría contener únicamente imágenes o tablas no interpretables.")

    return texto_completo, {"paginas": total_paginas, "caracteres": caracteres, "lineas": lineas, "alertas_ocr": alertas_ocr}


# ====================================================================
# VALIDADOR DE EXTRACCIÓN
# ====================================================================
def validar_json_extraccion(texto_respuesta: str) -> Tuple[bool, str, Optional[dict]]:
    if not texto_respuesta or not texto_respuesta.strip():
        return False, "Respuesta vacía en Extracción.", None
    
    texto_limpio = texto_respuesta.strip()
    if not texto_limpio.endswith("}") and not texto_limpio.endswith("]"):
        return False, "JSON de extracción truncado.", None
        
    try:
        parsed = json.loads(texto_limpio)
        if not isinstance(parsed, dict):
            return False, "El JSON de extracción no es un diccionario válido.", None
        
        secciones_requeridas = ["paciente", "ventriculo_izquierdo", "auricula_izquierda", "ventriculo_derecho"]
        for sec in secciones_requeridas:
            if sec not in parsed:
                return False, f"Falta la sección obligatoria '{sec}' en extracción.", None
        return True, "OK", parsed
    except Exception as e:
        return False, f"Error de parseo JSON en extracción: {str(e)}", None


# ====================================================================
# LLAMADA SEGURA A GEMINI
# ====================================================================
def llamada_segura_gemini(client, model_name: str, contents: list, config_gen: types.GenerateContentConfig, max_retries=3):
    t_inicio = time.time()
    delay = 2
    for intento in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config_gen,
            )
            duracion = round(time.time() - t_inicio, 3)
            return response, duracion
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str.lower() or "rate limit" in error_str.lower() or "timeout" in error_str.lower():
                if intento < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e
    duracion = round(time.time() - t_inicio, 3)
    raise Exception(f"Error de red/modelo en {model_name} tras reintentos (Duración: {duracion}s).")


# ====================================================================
# PROMPT DE EXTRACCIÓN ESTRICTA
# ====================================================================
PROMPT_EXTRACCION = """
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
# SANITIZACIÓN Y NORMALIZACIÓN
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

def normalizar_datos(data: dict) -> dict:
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
# CÁLCULO DE RECALL CLÍNICO
# ====================================================================
def calcular_recall_clinico(json_data: dict, ocr_texto: str) -> Dict[str, Any]:
    ocr_lower = ocr_texto.lower()
    variables_en_ocr = 0
    variables_recuperadas = 0
    detalle_variables = []

    def obtener_valor_anidado(d, ruta):
        actual = d
        for parte in ruta.split('.'):
            if isinstance(actual, dict) and parte in actual:
                actual = actual[parte]
            else:
                return None
        return actual

    for campo_json, patrones in PATRONES_OCR_RECALL.items():
        presente_en_ocr = any(re.search(pat, ocr_lower) for pat in patrones)
        if presente_en_ocr:
            variables_en_ocr += 1
            val = obtener_valor_anidado(json_data, campo_json)
            recuperado = val is not None and str(val).strip() != ""
            if recuperado:
                variables_recuperadas += 1
            detalle_variables.append({
                "variable": campo_json,
                "en_ocr": "Sí",
                "recuperado_json": "Sí" if recuperado else "No"
            })

    recall_pct = round((variables_recuperadas / variables_en_ocr * 100), 1) if variables_en_ocr > 0 else 100.0

    if recall_pct >= 80:
        calificacion = "Excelente (Alta fidelidad clínica)"
    elif recall_pct >= 50:
        calificacion = "Aceptable (Extracción parcial estándar)"
    else:
        calificacion = "Deficiente (Pérdida significativa de datos detectables)"

    return {
        "variables_en_ocr": variables_en_ocr,
        "variables_recuperadas": variables_recuperadas,
        "recall_clinico_pct": recall_pct,
        "calificacion_recall": calificacion,
        "detalle_variables": detalle_variables
    }


# ====================================================================
# MOTOR ROSS V10.0 - SÍNTESIS CLÍNICA HUMANA Y RIGUROSA
# ====================================================================
def motor_ross_y_sintesis_estricta_v10(data: dict, recall_res: dict, tiempo_total: float, archivo_nombre: str) -> dict:
    hallazgos_relevantes = []
    alertas = []
    
    vi = data.get("ventriculo_izquierdo", {})
    fevi = vi.get("fevi_porcentaje")
    vtd = vi.get("volumen_telediastolico_ml")
    dtdvi = vi.get("dtdvi_mm")
    dtsvi = vi.get("dtsvi_mm")
    siv = vi.get("siv_mm")
    ppvi = vi.get("ppvi_mm")
    movilidad = vi.get("movilidad_anormal_descripcion")

    # 1. Evaluación Sistólica VI (Normalidad NO entra en hallazgos_relevantes)
    func_txt = None
    if fevi is not None:
        if fevi < 52.0:
            if 41.0 <= fevi < 52.0:
                func_txt = f"disfunción sistólica ventricular izquierda leve (FEVI: {fevi}%)"
                hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": f"Disfunción sistólica leve (FEVI: {fevi}%)"})
            elif 30.0 <= fevi < 41.0:
                func_txt = f"disfunción sistólica ventricular izquierda moderada (FEVI: {fevi}%)"
                hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": f"Disfunción sistólica moderada (FEVI: {fevi}%)"})
            else:
                func_txt = f"disfunción sistólica ventricular izquierda severa (FEVI: {fevi}%)"
                hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": f"Disfunción sistólica severa (FEVI: {fevi}%)"})
        else:
            func_txt = f"función sistólica global conservada (FEVI: {fevi}%)"

    dilatacion_vi = (dtdvi is not None and dtdvi > 58.0) or (vtd is not None and vtd > 160.0)
    if dilatacion_vi:
        alerta_dil = "Dilatación ventricular izquierda."
        alertas.append(alerta_dil)
        hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": alerta_dil, "evidencia": {"DTDVI": dtdvi, "VTD": vtd}})

    if movilidad:
        hallazgos_relevantes.append({"categoria": "motilidad", "hallazgo": f"Alteración segmentaria: {movilidad}"})

    # 2. Hemodinamia y PSAP
    hemo = data.get("hemodinamica_derecha", {})
    psap = hemo.get("psap_calculada_mmhg") or (hemo.get("gradiente_it_pico_mmhg") + CLINICAL_CONFIG["PAD_INSTITUCIONAL"] if hemo.get("gradiente_it_pico_mmhg") is not None else None)
    
    hap_txt = None
    if psap is not None:
        if psap >= CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
            if psap <= CLINICAL_CONFIG["UMBRAL_HAP_INTERMEDIA"]:
                hap_txt = f"presión sistólica de arteria pulmonar estimada en {psap} mmHg (probabilidad intermedia de hipertensión pulmonar)"
                hallazgos_relevantes.append({"categoria": "hemodinamica", "hallazgo": "Probabilidad intermedia de hipertensión pulmonar", "PSAP": psap})
            else:
                hap_txt = f"presión sistólica de arteria pulmonar estimada en {psap} mmHg (alta probabilidad de hipertensión pulmonar)"
                hallazgos_relevantes.append({"categoria": "hemodinamica", "hallazgo": "Alta probabilidad de hipertensión pulmonar", "PSAP": psap})
        else:
            hap_txt = f"PSAP estimada en {psap} mmHg"

    # 3. Derrama Pericárdico (Prioridad diagnóstica alta)
    pc = data.get("pericardio_cava", {})
    derrame = pc.get("derrame_pericardico")
    if derrame:
        hallazgos_relevantes.append({"categoria": "pericardio", "hallazgo": f"Derrame pericárdico {derrame}"})

    # 4. Construcción de Descripción Ecocardiográfica (Fluida, Natural, Sin Repeticiones de "Ventriculo con...")
    frases_desc = []

    # Bloque VI
    vi_fragmentos = []
    if dtdvi or dtsvi: vi_fragmentos.append(f"dimensiones internas de {dtdvi} mm en telediástole y {dtsvi} mm en telesístole")
    if siv or ppvi: vi_fragmentos.append(f"grosores parietales de SIV: {siv} mm y PPVI: {ppvi} mm")
    if vtd: vi_fragmentos.append(f"volumen telediastólico de {vtd} ml")
    
    if vi_fragmentos or func_txt or movilidad:
        base_vi = "Se observa ventrículo izquierdo con " + ", ".join(vi_fragmentos) if vi_fragmentos else "Ventrículo izquierdo"
        if func_txt: base_vi += f", evidenciando {func_txt}"
        if movilidad: base_vi += f". Se aprecia alteración de motilidad: {movilidad}"
        frases_desc.append(base_vi + ".")

    # Bloque Aurícula Izquierda
    ai = data.get("auricula_izquierda", {})
    ai_ap = ai.get("diametro_ap_mm")
    ai_vol = ai.get("volumen_ml")
    ai_index = ai.get("volumen_indexado_ml_m2")
    if ai_ap or ai_vol or ai_index:
        ai_parts = []
        if ai_ap: ai_parts.append(f"diámetro anteroposterior de {ai_ap} mm")
        if ai_vol: ai_parts.append(f"volumen de {ai_vol} ml")
        if ai_index: ai_parts.append(f"volumen indexado de {ai_index} ml/m²")
        
        ai_str = f"La aurícula izquierda presenta {', '.join(ai_parts)}."
        if ai_index is not None and ai_index > 34.0:
            ai_str += " Se documenta dilatación auricular."
            hallazgos_relevantes.append({"categoria": "auricula_izquierda", "hallazgo": f"Dilatación auricular izquierda (LAVI: {ai_index} ml/m²)"})
        frases_desc.append(ai_str)

    # Bloque Ventrículo y Aurícula Derecha
    vd = data.get("ventriculo_derecho", {})
    vd_basal = vd.get("diametro_basal_mm")
    tapse = vd.get("tapse_mm")
    onda_s = vd.get("onda_s_cm_s")
    if vd_basal or tapse or onda_s:
        vd_parts = []
        if vd_basal: vd_parts.append(f"diámetro basal de {vd_basal} mm")
        if tapse: vd_parts.append(f"TAPSE de {tapse} mm")
        if onda_s: vd_parts.append(f"onda S' de {onda_s} cm/s")
        
        vd_str = f"Cavidades derechas con ventrículo que muestra {', '.join(vd_parts)}."
        if tapse is not None and tapse < 16.0:
            vd_str += " Se observa reducción de la excursión longitudinal sistólica."
            hallazgos_relevantes.append({"categoria": "ventriculo_derecho", "hallazgo": f"Disfunción sistólica VD (TAPSE: {tapse} mm)"})
        frases_desc.append(vd_str)

    ad = data.get("auricula_derecha", {})
    ad_area = ad.get("area_cm2")
    if ad_area:
        frases_desc.append(f"Aurícula derecha con área planimétrica de {ad_area} cm².")

    # Bloque Valvular (Filtro de Insuficiencias Leves/Mínimas)
    valv = data.get("valvulas", {})
    valv_textos = []
    for v_key, v_label in [
        ("aortica_insuficiencia", "aórtica"), 
        ("mitral_insuficiencia", "mitral"), 
        ("tricuspide_insuficiencia", "tricuspídea"), 
        ("pulmonar_insuficiencia", "pulmonar")
    ]:
        grado = valv.get(v_key)
        if grado:
            grado_lower = str(grado).lower()
            # Criterio uniforme: Leves o mínimas solo en descripción; moderadas/severas a conclusiones y hallazgos
            if any(term in grado_lower for term in ["moderada", "severa", "importante", "significativa", "grado"]):
                hallazgos_relevantes.append({"categoria": "valvulas", "hallazgo": f"Insuficiencia {v_label} {grado}"})
            valv_textos.append(f"insuficiencia {v_label} {grado}")

    if valv.get("aortica_vmax_ms") or valv.get("aortica_grad_medio_mmhg"):
        vmax = valv.get("aortica_vmax_ms")
        gmed = valv.get("aortica_grad_medio_mmhg")
        valv_textos.append(f"válvula aórtica con velocidad máxima de {vmax} m/s y gradiente medio de {gmed} mmHg")

    if valv_textos:
        frases_desc.append(f"A examen Doppler color y espectral se identifica: {', '.join(valv_textos)}.")

    if hap_txt:
        frases_desc.append(f"En la evaluación hemodinámica se registra {hap_txt}.")

    cava_d = pc.get("cava_inferior_diametro_mm")
    cava_col = pc.get("cava_colapso_porcentaje")
    if cava_d is not None:
        cava_str = f"Vena cava inferior con calibre de {cava_d} mm"
        if cava_col is not None: cava_str += f" y colapsibilidad inspiratoria de {cava_col}%"
        frases_desc.append(cava_str + ".")

    if derrame:
        frases_desc.append(f"Se documenta presencia de derrame pericárdico de características {derrame}.")

    descripcion_corrida = " ".join(frases_desc)

    # 5. Conclusiones Clínicas (EXCLUSIVAMENTE alteraciones y diagnósticos, Cero Mediciones Aisladas)
    conclusiones = []
    
    if fevi is not None and fevi < 52.0:
        conclusiones.append(f"Disfunción sistólica ventricular izquierda de grado {('leve' if fevi >= 41 else ('moderado' if fevi >= 30 else 'severo'))} (FEVI: {fevi}%).")
    if dilatacion_vi:
        conclusiones.append("Dilatación ventricular izquierda.")
    if ai_index is not None and ai_index > 34.0:
        conclusiones.append(f"Dilatación auricular izquierda significativa (LAVI: {ai_index} ml/m²).")
    if tapse is not None and tapse < 16.0:
        conclusiones.append(f"Disfunción sistólica del ventrículo derecho (TAPSE: {tapse} mm).")
    if psap is not None and psap >= CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
        conclusiones.append(f"Elevación de la presión sistólica de la arteria pulmonar estimada en {psap} mmHg.")
    if movilidad:
        conclusiones.append(f"Trastorno de la motilidad parietal segmentaria: {movilidad}.")
    
    for vk, v_label in [("aortica_insuficiencia", "aórtica"), ("mitral_insuficiencia", "mitral"), ("tricuspide_insuficiencia", "tricuspídea")]:
        grado = valv.get(vk)
        if grado:
            g_low = str(grado).lower()
            if any(term in g_low for term in ["moderada", "severa", "importante", "significativa"]):
                conclusiones.append(f"Insuficiencia {v_label} {grado}.")

    if derrame:
        conclusiones.append(f"Derrame pericárdico: {derrame}.")

    conclusiones = conclusiones[:7]
    if not conclusiones:
        conclusiones.append("Estudio ecocardiográfico sin alteraciones estructurales o funcionales mayores consignadas.")

    # 6. Diagnóstico Final (Impresión Clínica Integrada, No Lista de Variables)
    diag_componentes = []
    if fevi is not None:
        if fevi < 52.0:
            diag_componentes.append(f"disfunción sistólica ventricular izquierda ({fevi}%)")
        else:
            diag_componentes.append("función sistólica global conservada")
    
    if dilatacion_vi: diag_componentes.append("con remodelado/dilatación ventricular izquierda")
    if ai_index is not None and ai_index > 34.0: diag_componentes.append("dilatación auricular izquierda")
    if movilidad: diag_componentes.append(f"trastorno de motilidad ({movilidad})")
    
    valv_significativas = [f"insuficiencia {v_label} {valv.get(vk)}" for vk, v_label in [("aortica_insuficiencia", "aórtica"), ("mitral_insuficiencia", "mitral"), ("tricuspide_insuficiencia", "tricuspídea")] if valv.get(vk) and any(t in str(valv.get(vk)).lower() for t in ["moderada", "severa", "importante"])]
    if valv_significativas:
        diag_componentes.append("valvulopatía significativa tipo " + " y ".join(valv_significativas))

    if psap is not None and psap >= CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
        diag_componentes.append(f"estimación de PSAP elevada ({psap} mmHg)")

    if derrame:
        diag_componentes.append(f" derrame pericárdico ({derrame})")

    if diag_componentes:
        # Construcción sintáctica de impresión médica real
        diagnostico_final = "Impresión diagnóstica: Ecocardiograma transtorácico que demuestra " + ", ".join(diag_componentes) + "."
    else:
        diagnostico_final = "Impresión diagnóstica: Ecocardiograma transtorácico sin alteraciones patológicas relevantes evaluadas."

    # 7. JSON Maestro v10.0 con Trazabilidad Completa
    json_maestro = {
        "paciente": data.get("paciente", {}),
        "variables_ecocardiograficas": {
            "ventriculo_izquierdo": vi,
            "auricula_izquierda": ai,
            "ventriculo_derecho": vd,
            "auricula_derecha": data.get("auricula_derecha", {}),
            "hemodinamica_derecha": hemo,
            "funcion_diastolica_bruta": data.get("funcion_diastolica_bruta", {}),
            "valvulas": valv,
            "pericardio_cava": pc
        },
        "hechos_clinicos": {
            "hallazgos_relevantes": hallazgos_relevantes
        },
        "alertas_automaticas": alertas,
        "recall_clinico": recall_res,
        "descripcion_ecocardiografica": descripcion_corrida,
        "conclusiones": conclusiones,
        "diagnostico": diagnostico_final,
        "metadatos": {
            "fecha_procesamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "archivo_fuente": archivo_nombre,
            "tiempo_total_segundos": tiempo_total,
            "version_motor": "CardioAgente Extractor Maestro v10.0 (Clínico Fino)"
        }
    }

    return json_maestro


# ====================================================================
# INTERFAZ STREAMLIT - APLICACIÓN 1 (V10.0)
# ====================================================================
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("#### 📂 Ingesta de Estudio Ecocardiográfico (PDF)")
    uploaded_file = st.file_uploader("Cargar reporte del ecógrafo", type=["pdf"])

if uploaded_file is not None:
    with col1:
        st.success(f"Archivo vinculado: {uploaded_file.name}")

    if not api_key:
        with col2:
            st.warning("⚠️ Ingrese su API Key de Gemini en el panel lateral.")
    else:
        with col1:
            if st.button("🚀 Ejecutar Extracción y Cerebro Clínico v10.0", use_container_width=True):
                status_placeholder = st.empty()
                
                try:
                    t_inicio_total = time.time()

                    # 1. OCR
                    status_placeholder.info("🔄 Procesando OCR adaptativo del PDF...")
                    file_bytes = uploaded_file.read()
                    texto_ocr, reporte_ocr = extraer_pdf_adaptativo(file_bytes)

                    # 2. Llamada única a Gemini
                    status_placeholder.info("🔄 Extrayendo datos estructurados con Gemini (1 sola llamada)...")
                    client = genai.Client(api_key=api_key)
                    config_gen = types.GenerateContentConfig(temperature=0.0)
                    prompt_ext = f"{PROMPT_EXTRACCION}\nDATOS CRUDOS DEL INFORMANTE:\n{texto_ocr}"
                    
                    response, dur_ext = llamada_segura_gemini(
                        client=client,
                        model_name="gemini-3.8-flash",
                        contents=[prompt_ext],
                        config_gen=config_gen
                    )
                    
                    texto_resp = re.sub(r"^```json\s*", "", response.text.strip())
                    texto_resp = re.sub(r"^```\s*", "", texto_resp)
                    texto_resp = re.sub(r"\s*```$", "", texto_resp)

                    valido, msg, json_crudo = validar_json_extraccion(texto_resp)
                    if not valido:
                        raise ValueError(f"Fallo de validación en Extracción: {msg}")

                    # 3. Normalización y Síntesis Fina v10.0
                    status_placeholder.info("🔄 Ejecutando normalización y síntesis clínica fluida...")
                    json_normalizado = normalizar_datos(json_crudo)
                    recall_res = calcular_recall_clinico(json_normalizado, texto_ocr)
                    
                    tiempo_total = round(time.time() - t_inicio_total, 3)

                    json_maestro_final = motor_ross_y_sintesis_estricta_v10(
                        json_normalizado, 
                        recall_res, 
                        tiempo_total, 
                        uploaded_file.name
                    )

                    st.session_state["json_maestro"] = json_maestro_final

                    historial = cargar_historial_disco()
                    historial.append({
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "archivo": uploaded_file.name,
                        "recall_pct": recall_res["recall_clinico_pct"],
                        "tiempo_total": tiempo_total
                    })
                    guardar_historial_disco(historial)

                    status_placeholder.success(f"✅ JSON Maestro v10.0 generado con éxito en {tiempo_total}s (Recall Clínico: {recall_res['recall_clinico_pct']}%)")

                except Exception as e:
                    status_placeholder.error(f"❌ Error crítico en el Extractor: {str(e)}")

# ====================================================================
# VISUALIZACIÓN Y DESCARGA DEL JSON MAESTRO V10.0
# ====================================================================
if "json_maestro" in st.session_state:
    st.markdown("---")
    st.markdown("### 📊 Inspección del JSON Maestro v10.0 (Cerebro Clínico Fino)")
    
    maestro = st.session_state["json_maestro"]
    recall = maestro.get("recall_clinico", {})
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Recall Clínico", f"{recall.get('recall_clinico_pct', 0)}%")
    with c2: st.metric("Variables Detectadas", f"{recall.get('variables_en_ocr', 0)}")
    with c3: st.metric("Variables Recuperadas", f"{recall.get('variables_recuperadas', 0)}")

    st.markdown("#### 📝 Vista Previa del Contenido Clínico de Alta Fidelidad")
    st.info(f"**Diagnóstico Final:** {maestro.get('diagnostico')}")
    st.write(f"**Descripción Ecocardiográfica:** {maestro.get('descripcion_ecocardiografica')}")
    
    st.write("**Conclusiones Clínicas:**")
    for idx, c in enumerate(maestro.get("conclusiones", []), 1):
        st.markdown(f"*{idx}.* {c}")

    st.markdown("#### 📦 JSON Maestro v10.0 Completo")
    json_str = json.dumps(maestro, ensure_ascii=False, indent=2)
    
    st.code(json_str, language="json")
    
    st.download_button(
        label="💾 Descargar JSON Maestro v10.0",
        data=json_str,
        file_name=f"json_maestro_v10_{maestro.get('paciente', {}).get('nombre', 'paciente').replace(' ', '_')}.json",
        mime="application/json",
        use_container_width=True
    )
