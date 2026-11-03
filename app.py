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
# CONFIGURACIÓN Y PERSISTENCIA DE LOTE (APP 1 - V12.1 CEREBRO CLÍNICO)
# ====================================================================
HISTORIAL_FILE = "historial_lote_extractor_v12.json"

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

# ====================================================================
# PATRONES DE RECALL CLÍNICO ROBUSTOS (SOPORTE DUAL CHISON + ESTÁNDAR)
# ====================================================================
PATRONES_OCR_RECALL = {
    "ventriculo_izquierdo.fevi_porcentaje": [
        r"fevi", r"f\.e\.v\.i\.", r"fracci[oó]n de eyecci[oó]n", r"\bef\b", r"e\.f\.", r"\bfe\b"
    ],
    "ventriculo_izquierdo.dtdvi_mm": [
        r"dtdvi", r"dtd\s*vi", r"ddvi", r"di[aá]metro telediast[oó]lico", r"lvid(d)?"
    ],
    "ventriculo_izquierdo.dtsvi_mm": [
        r"dtsvi", r"dts\s*vi", r"dsvi", r"di[aá]metro telesist[oó]lico", r"lvid(s)?"
    ],
    "ventriculo_izquierdo.volumen_telediastolico_ml": [
        r"\bvtd\b", r"\bedv\b", r"edv\(a4c\)", r"edv\(a2c\)", r"volumen telediast[oó]lico"
    ],
    "ventriculo_izquierdo.volumen_telesistolico_ml": [
        r"\bvts\b", r"\besv\b", r"esv\(a4c\)", r"esv\(a2c\)", r"volumen telesist[oó]lico"
    ],
    "ventriculo_izquierdo.masa_miocardica_g": [
        r"vi\s*masa", r"masa", r"mass"
    ],
    "auricula_izquierda.diametro_ap_mm": [
        r"aur[ií]cula izquierda", r"ai\s*ap", r"diametro\s*ap-la", r"\bla\b", r"lad", r"di[aá]metro ai"
    ],
    "ventriculo_derecho.diametro_basal_mm": [
        r"vd\s*basal", r"vd\s*base", r"rv\s*basal", r"ventr[ií]culo derecho"
    ],
    "ventriculo_derecho.tapse_mm": [
        r"tapse"
    ],
    "hemodinamica_derecha.psap_calculada_mmhg": [
        r"psap", r"pasc", r"pap", r"tv\s*pgmax", r"vt\s*vmax"
    ]
}

st.set_page_config(
    page_title="CardioAgente | Extractor Clínico Maestro v12.1",
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
        <h2 style='margin:0; font-size: 24px;'>🧬 CardioAgente - Extractor Clínico Maestro v12.1 (Chison Dual & Autocalibrado)</h2>
        <p style='margin:5px 0 0 0; font-size: 14px;'>Dr. Diego Ross Álvarez | Soporte Dual de Nomenclatura | Conversión Fisiológica Automática | Geometría VI y Hemodinamia Real</p>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Configuración del Cerebro Clínico")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.info(
        "Directiva v12.1:\n"
        "• Compatible con presets antiguos y nuevos de Chison EBit 60\n"
        "• Autoconversión cm->mm, s->ms y limpieza de signos (-)\n"
        "• Filtro anti-falsos positivos en motilidad normal\n"
        "• Umbrales ASE ajustados por sexo y RWT"
    )


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
            if any(err in error_str.lower() for err in ["503", "unavailable", "high demand", "rate limit", "timeout"]):
                if intento < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e
    duracion = round(time.time() - t_inicio, 3)
    raise Exception(f"Error de red/modelo en {model_name} tras reintentos (Duración: {duracion}s).")


# ====================================================================
# PROMPT DE EXTRACCIÓN ESTRICTA (CON DICCIONARIO POLIMÓRFICO CHISON)
# ====================================================================
PROMPT_EXTRACCION = """
Eres un motor de extracción de datos médicos altamente preciso especializado en ecocardiografía (incluyendo reportes tabulares desordenados de equipos Chison EBit 60). Tu ÚNICA tarea es extraer los valores numéricos y descriptivos del texto del informe proporcionado y volcarlos en el siguiente esquema JSON.

REGLAS CRÍTICAS DE MAPEO Y EQUIVALENCIAS (SOPORTE DUAL):
1. Extrae únicamente lo que esté explícitamente en el texto. Si un parámetro no existe, asigna estrictamente null. PROHIBIDO usar 0.0 por defecto.
2. EMPAREJAMIENTO DE COLUMNAS DESFASADAS: En ocasiones el OCR agrupa primero una lista vertical de etiquetas (ej. TV PGmax, VDTS AccT, Ea(MV medial), E/Ea(MV medial), Sa(MV lateral), Ea(MV lateral), E/Ea(MV lateral)) y justo debajo la lista vertical de sus valores en el mismo orden exacto. Empareja cada etiqueta con su valor correspondiente por posición secuencial.
3. DICCIONARIO DE SINÓNIMOS DEL ECÓGRAFO:
   - dtdvi_mm: busca "DDVI", "LVIDd", "DTDVI".
   - dtsvi_mm: busca "DSVI", "LVIDS", "DTSVI".
   - siv_mm: busca "SIVd", "IVSd", "SIV".
   - ppvi_mm: busca "PPd", "LVPWd", "PPVI".
   - rwt: busca "RWT" (espesor relativo de pared).
   - fevi_porcentaje: busca "FE", "FEVI", "EF".
   - volumen_telediastolico_ml: prioriza el valor integrado "EDV" o "VTD". Si solo hay planos separados, usa "EDV(A4C)" o "EDV(A2C)".
   - volumen_telesistolico_ml: prioriza "ESV" o "VTS". Si no, usa "ESV(A4C)" o "ESV(A2C)".
   - masa_miocardica_g: busca "VI masa", "LV Mass".
   - indice_masa_miocardica_g_m2: busca "VI Indice Masa", "LV Mass Index".
   - movilidad_anormal_descripcion: ATENCIÓN: Si el texto dice "sin alteraciones de la movilidad global ni segmentaria" o "movilidad conservada/normal", asigna estrictamente null. Solo pon texto aquí si existe hipocinesia, acinesia, discinesia o asincronía real.
   - auricula_izquierda: diametro_ap_mm ("Diametro Ap-LA", "LA", "AI AP"); area_cm2 ("LAa"); volumen_ml ("VAI 4C", "VAI 2C", "VAI 20"); volumen_indexado_ml_m2 ("IVAI", "LAVI").
   - ventriculo_derecho: diametro_basal_mm ("VD base", "VD basal"); tapse_mm ("TAPSE"); cafvd_porcentaje ("CAFVD", "FAC"); area_diastolica_cm2 ("RVAd"); area_sistolica_cm2 ("RVAS").
   - auricula_derecha: area_cm2 ("RAa"); volumen_ml ("VAD"); volumen_indexado_ml_m2 ("IVAD").
   - hemodinamica_derecha: velocidad_it_max_ms ("VT Vmax", "TR Vmax", "IT Vmax"); gradiente_it_pico_mmhg ("TV PGmax", "TR PGmax"); pad_estimada_mmhg ("RAP", "PAD").
   - funcion_diastolica_bruta: onda_e_cm_s ("VM E Vel", "MV E Vel"); onda_a_cm_s ("VM A Vel", "MV A Vel"); relacion_e_a ("E/A"); tda_ms ("MV DecT"); trvi_ms ("IVRT"); e_prima_septal_cm_s ("Ea(MV medial)"); e_prima_lateral_cm_s ("Ea(MV lateral)"); e_e_prima_medial ("E/Ea(MV medial)"); e_e_prima_lateral ("E/Ea(MV lateral)").
   - aorta_y_tractos: raiz_aortica_mm ("AO"); senos_valsalva_mm ("S. valsalva"); union_st_mm ("Union ST"); tsvi_diametro_mm ("TSVI Diam"); tsvi_ivt_cm ("TSVI IVT"); tsvd_diametro_mm ("VDTS Diam"); tsvd_ivt_cm ("VDTS IVT"); acct_pulmonar_ms ("VDTS AccT", "AccT").
   - valvulas: aortica_vmax_ms ("VA Vmax", "AV Vmax"); aortica_grad_max_mmhg ("AV PGmax"); aortica_grad_medio_mmhg ("AV PGmean"); pulmonar_vmax_ms ("VP Vmax", "VF Vmax"); pulmonar_grad_max_mmhg ("PV PGmax"). Si en la sección "Descripción" se menciona algún hallazgo valvular (ej. "billowing mitral, sin insuficiencia asociada"), colócalo en "hallazgos_descriptivos_adicionales".
   - pericardio_cava: cava_inferior_diametro_mm ("IVC Exp", "VCI"); cava_inferior_inspiracion_mm ("IVC Ins"); cava_colapso_porcentaje ("IVC Ins/IVC Exp").
4. UNIDADES: Convierte diámetros en centímetros (cm) a milímetros (mm) multiplicando por 10 (ej. DDVI 4.17 cm -> 41.7, TAPSE 2.21 cm -> 22.1, IVC Exp 1.35 cm -> 13.5). Ignora el signo negativo (-) en todas las velocidades Doppler.

ESTRUCTURA DE SALIDA OBLIGATORIA (JSON PURO SIN MARKDOWN):
{
  "paciente": {
    "nombre": "",
    "edad": null,
    "sexo": null,
    "peso_kg": null,
    "talla_m": null,
    "asc_m2": null,
    "fc_lpm": null,
    "pa_sistolica_mmhg": null,
    "pa_diastolica_mmhg": null
  },
  "introduccion": "",
  "ventriculo_izquierdo": {
    "dtdvi_mm": null,
    "dtsvi_mm": null,
    "siv_mm": null,
    "ppvi_mm": null,
    "rwt": null,
    "fevi_porcentaje": null,
    "volumen_telediastolico_ml": null,
    "volumen_telesistolico_ml": null,
    "volumen_latido_ml": null,
    "gasto_cardiaco_l_min": null,
    "indice_cardiaco_l_min_m2": null,
    "masa_miocardica_g": null,
    "indice_masa_miocardica_g_m2": null,
    "movilidad_anormal_descripcion": null
  },
  "auricula_izquierda": {
    "diametro_ap_mm": null,
    "volumen_ml": null,
    "volumen_indexado_ml_m2": null,
    "area_cm2": null
  },
  "ventriculo_derecho": {
    "diametro_basal_mm": null,
    "tapse_mm": null,
    "onda_s_cm_s": null,
    "cafvd_porcentaje": null,
    "area_diastolica_cm2": null,
    "area_sistolica_cm2": null
  },
  "auricula_derecha": {
    "area_cm2": null,
    "volumen_ml": null,
    "volumen_indexado_ml_m2": null
  },
  "hemodinamica_derecha": {
    "velocidad_it_max_ms": null,
    "gradiente_it_pico_mmhg": null,
    "pad_estimada_mmhg": null,
    "psap_calculada_mmhg": null
  },
  "funcion_diastolica_bruta": {
    "onda_e_cm_s": null,
    "onda_a_cm_s": null,
    "relacion_e_a": null,
    "tda_ms": null,
    "trvi_ms": null,
    "e_prima_septal_cm_s": null,
    "e_prima_lateral_cm_s": null,
    "e_e_prima_medial": null,
    "e_e_prima_lateral": null,
    "relacion_e_e_prima": null
  },
  "aorta_y_tractos": {
    "raiz_aortica_mm": null,
    "senos_valsalva_mm": null,
    "union_st_mm": null,
    "tsvi_diametro_mm": null,
    "tsvi_vmax_ms": null,
    "tsvi_ivt_cm": null,
    "tsvd_diametro_mm": null,
    "tsvd_vmax_ms": null,
    "tsvd_ivt_cm": null,
    "acct_pulmonar_ms": null
  },
  "valvulas": {
    "aortica_vmax_ms": null,
    "aortica_grad_max_mmhg": null,
    "aortica_grad_medio_mmhg": null,
    "aortica_area_cm2": null,
    "aortica_insuficiencia": null,
    "mitral_insuficiencia": null,
    "mitral_estenosis": null,
    "tricuspide_insuficiencia": null,
    "pulmonar_vmax_ms": null,
    "pulmonar_grad_max_mmhg": null,
    "pulmonar_insuficiencia": null,
    "hallazgos_descriptivos_adicionales": null
  },
  "pericardio_cava": {
    "derrame_pericardico": null,
    "cava_inferior_diametro_mm": null,
    "cava_inferior_inspiracion_mm": null,
    "cava_colapso_porcentaje": null
  }
}
"""


# ====================================================================
# SANITIZACIÓN Y AUTOCONVERSIÓN FISIOLÓGICA DE UNIDADES
# ====================================================================
def sanitizar_y_convertir_numero(val: Any, usar_abs: bool = True) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        num = float(val)
        return abs(num) if usar_abs else num
    if isinstance(val, str):
        val_clean = val.strip().lower()
        if not val_clean or val_clean in ["null", "none", "n/a", "no reportado", "-"]:
            return None
        match = re.search(r"([-+]?\d*\.?\d+)", val_clean)
        if match:
            try:
                num = float(match.group(1))
                return abs(num) if usar_abs else num
            except ValueError:
                return None
    return None

def autoconvertir_cm_a_mm(val: Optional[float], umbral_cm_max: float) -> Optional[float]:
    """Si el valor es menor al umbral fisiológico en mm, viene en cm -> multiplica por 10."""
    if val is None:
        return None
    if 0 < val <= umbral_cm_max:
        return round(val * 10.0, 2)
    return round(val, 2)

def autoconvertir_velocidad_ms(val: Optional[float]) -> Optional[float]:
    """Si una velocidad esperada en m/s es > 15, viene en cm/s -> divide entre 100."""
    if val is None:
        return None
    if val > 15.0:
        return round(val / 100.0, 2)
    return round(val, 2)

def autoconvertir_velocidad_cms(val: Optional[float]) -> Optional[float]:
    """Si una velocidad esperada en cm/s es < 3.5, viene en m/s -> multiplica por 100."""
    if val is None:
        return None
    if 0 < val < 3.5:
        return round(val * 100.0, 2)
    return round(val, 2)

def autoconvertir_tiempo_ms(val: Optional[float]) -> Optional[float]:
    """Si un tiempo esperado en ms (TDA, IVRT, AccT) es < 3.0, viene en segundos -> * 1000."""
    if val is None:
        return None
    if 0 < val < 3.0:
        return round(val * 1000.0, 1)
    return round(val, 1)

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

def filtrar_motilidad_normal(texto_mov: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Evita que frases como 'Movilidad: sin alteraciones...' se clasifiquen como patológicas.
    Además, separa texto infiltrado (ej. 'Se observa billowing mitral...') hacia notas adicionales.
    """
    if not texto_mov:
        return None, None

     oraciones = [s.strip() for s in re.split(r'[.;\n]', texto_mov) if s.strip()]
    mov_anormal = []
    extra_valvular = []

    patrones_normales = [
        r"sin\s+alteraciones", r"conservad[ao]", r"normal",
        r"adecuad[ao]", r"sin\s+trastornos", r"no\s+se\s+observan\s+alteraciones"
    ]

    for orac in oraciones:
        orac_low = orac.lower()
        if any(w in orac_low for w in ["mitral", "aórtic", "aortic", "tricúsp", "tricusp", "pulmonar", "billow", "prolapso", "esclerosis", "insuficiencia"]):
            extra_valvular.append(orac)
            continue
        if any(re.search(pat, orac_low) for pat in patrones_normales):
            continue
        mov_anormal.append(orac)

    mov_final = ". ".join(mov_anormal) if mov_anormal else None
    extra_final = ". ".join(extra_valvular) if extra_valvular else None
    return mov_final, extra_final

def normalizar_datos(data: dict) -> dict:
    if not isinstance(data, dict):
        return data

    # 1. Paciente
    pac = data.get("paciente", {})
    if isinstance(pac, dict):
        pac["nombre"] = sanitizar_texto(pac.get("nombre")) or ""
        edad_num = sanitizar_y_convertir_numero(pac.get("edad"))
        pac["edad"] = int(edad_num) if edad_num is not None else None
        pac["sexo"] = sanitizar_texto(pac.get("sexo"))
        pac["peso_kg"] = sanitizar_y_convertir_numero(pac.get("peso_kg"))
        talla = sanitizar_y_convertir_numero(pac.get("talla_m"))
        if talla is not None and talla > 3.0:
            talla = round(talla / 100.0, 2)  # 166 cm -> 1.66 m
        pac["talla_m"] = talla
        pac["asc_m2"] = sanitizar_y_convertir_numero(pac.get("asc_m2"))
        pac["fc_lpm"] = sanitizar_y_convertir_numero(pac.get("fc_lpm"))
        pac["pa_sistolica_mmhg"] = sanitizar_y_convertir_numero(pac.get("pa_sistolica_mmhg"))
        pac["pa_diastolica_mmhg"] = sanitizar_y_convertir_numero(pac.get("pa_diastolica_mmhg"))

    # 2. Ventrículo Izquierdo
    vi = data.get("ventriculo_izquierdo", {})
    extra_de_mov = None
    if isinstance(vi, dict):
        vi["dtdvi_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vi.get("dtdvi_mm")), 12.0)
        vi["dtsvi_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vi.get("dtsvi_mm")), 10.0)
        vi["siv_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vi.get("siv_mm")), 4.0)
        vi["ppvi_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vi.get("ppvi_mm")), 4.0)
        vi["rwt"] = sanitizar_y_convertir_numero(vi.get("rwt"))
        vi["fevi_porcentaje"] = sanitizar_y_convertir_numero(vi.get("fevi_porcentaje"))
        vi["volumen_telediastolico_ml"] = sanitizar_y_convertir_numero(vi.get("volumen_telediastolico_ml"))
        vi["volumen_telesistolico_ml"] = sanitizar_y_convertir_numero(vi.get("volumen_telesistolico_ml"))
        vi["volumen_latido_ml"] = sanitizar_y_convertir_numero(vi.get("volumen_latido_ml"))
        gc = sanitizar_y_convertir_numero(vi.get("gasto_cardiaco_l_min"))
        if gc is not None and gc > 25.0:
            gc = round(gc / 1000.0, 2)  # 3579.21 ml/min -> 3.58 L/min
        vi["gasto_cardiaco_l_min"] = gc
        vi["indice_cardiaco_l_min_m2"] = sanitizar_y_convertir_numero(vi.get("indice_cardiaco_l_min_m2"))
        vi["masa_miocardica_g"] = sanitizar_y_convertir_numero(vi.get("masa_miocardica_g"))
        vi["indice_masa_miocardica_g_m2"] = sanitizar_y_convertir_numero(vi.get("indice_masa_miocardica_g_m2"))
        
        mov_raw = sanitizar_texto(vi.get("movilidad_anormal_descripcion"))
        mov_limpio, extra_de_mov = filtrar_motilidad_normal(mov_raw)
        vi["movilidad_anormal_descripcion"] = mov_limpio

    # 3. Aurícula Izquierda
    ai = data.get("auricula_izquierda", {})
    if isinstance(ai, dict):
        ai["diametro_ap_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ai.get("diametro_ap_mm")), 10.0)
        ai["volumen_ml"] = sanitizar_y_convertir_numero(ai.get("volumen_ml"))
        ai["volumen_indexado_ml_m2"] = sanitizar_y_convertir_numero(ai.get("volumen_indexado_ml_m2"))
        ai["area_cm2"] = sanitizar_y_convertir_numero(ai.get("area_cm2"))

    # 4. Ventrículo Derecho
    vd = data.get("ventriculo_derecho", {})
    if isinstance(vd, dict):
        vd["diametro_basal_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vd.get("diametro_basal_mm")), 10.0)
        vd["tapse_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(vd.get("tapse_mm")), 6.0)
        vd["onda_s_cm_s"] = autoconvertir_velocidad_cms(sanitizar_y_convertir_numero(vd.get("onda_s_cm_s")))
        vd["cafvd_porcentaje"] = sanitizar_y_convertir_numero(vd.get("cafvd_porcentaje"))
        vd["area_diastolica_cm2"] = sanitizar_y_convertir_numero(vd.get("area_diastolica_cm2"))
        vd["area_sistolica_cm2"] = sanitizar_y_convertir_numero(vd.get("area_sistolica_cm2"))

    # 5. Aurícula Derecha
    ad = data.get("auricula_derecha", {})
    if isinstance(ad, dict):
        ad["area_cm2"] = sanitizar_y_convertir_numero(ad.get("area_cm2"))
        ad["volumen_ml"] = sanitizar_y_convertir_numero(ad.get("volumen_ml"))
        ad["volumen_indexado_ml_m2"] = sanitizar_y_convertir_numero(ad.get("volumen_indexado_ml_m2"))

    # 6. Hemodinámica Derecha
    hemo = data.get("hemodinamica_derecha", {})
    if isinstance(hemo, dict):
        hemo["velocidad_it_max_ms"] = autoconvertir_velocidad_ms(sanitizar_y_convertir_numero(hemo.get("velocidad_it_max_ms")))
        hemo["gradiente_it_pico_mmhg"] = sanitizar_y_convertir_numero(hemo.get("gradiente_it_pico_mmhg"))
        hemo["pad_estimada_mmhg"] = sanitizar_y_convertir_numero(hemo.get("pad_estimada_mmhg"))
        hemo["psap_calculada_mmhg"] = sanitizar_y_convertir_numero(hemo.get("psap_calculada_mmhg"))

    # 7. Función Diastólica
    fd = data.get("funcion_diastolica_bruta", {})
    if isinstance(fd, dict):
        fd["onda_e_cm_s"] = autoconvertir_velocidad_cms(sanitizar_y_convertir_numero(fd.get("onda_e_cm_s")))
        fd["onda_a_cm_s"] = autoconvertir_velocidad_cms(sanitizar_y_convertir_numero(fd.get("onda_a_cm_s")))
        fd["relacion_e_a"] = sanitizar_y_convertir_numero(fd.get("relacion_e_a"))
        fd["tda_ms"] = autoconvertir_tiempo_ms(sanitizar_y_convertir_numero(fd.get("tda_ms")))
        fd["trvi_ms"] = autoconvertir_tiempo_ms(sanitizar_y_convertir_numero(fd.get("trvi_ms")))
        fd["e_prima_septal_cm_s"] = autoconvertir_velocidad_cms(sanitizar_y_convertir_numero(fd.get("e_prima_septal_cm_s")))
        fd["e_prima_lateral_cm_s"] = autoconvertir_velocidad_cms(sanitizar_y_convertir_numero(fd.get("e_prima_lateral_cm_s")))
        fd["e_e_prima_medial"] = sanitizar_y_convertir_numero(fd.get("e_e_prima_medial"))
        fd["e_e_prima_lateral"] = sanitizar_y_convertir_numero(fd.get("e_e_prima_lateral"))
        
        rel_ee = sanitizar_y_convertir_numero(fd.get("relacion_e_e_prima"))
        if rel_ee is None:
            eem = fd.get("e_e_prima_medial")
            eel = fd.get("e_e_prima_lateral")
            if eem is not None and eel is not None:
                rel_ee = round((eem + eel) / 2.0, 2)
            elif eem is not None:
                rel_ee = eem
            elif eel is not None:
                rel_ee = eel
        fd["relacion_e_e_prima"] = rel_ee

    # 8. Aorta y Tractos de Salida
    ao = data.get("aorta_y_tractos", {})
    if isinstance(ao, dict):
        ao["raiz_aortica_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ao.get("raiz_aortica_mm")), 8.0)
        ao["senos_valsalva_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ao.get("senos_valsalva_mm")), 8.0)
        ao["union_st_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ao.get("union_st_mm")), 8.0)
        ao["tsvi_diametro_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ao.get("tsvi_diametro_mm")), 5.0)
        ao["tsvi_vmax_ms"] = autoconvertir_velocidad_ms(sanitizar_y_convertir_numero(ao.get("tsvi_vmax_ms")))
        ao["tsvi_ivt_cm"] = sanitizar_y_convertir_numero(ao.get("tsvi_ivt_cm"))
        ao["tsvd_diametro_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(ao.get("tsvd_diametro_mm")), 6.0)
        ao["tsvd_vmax_ms"] = autoconvertir_velocidad_ms(sanitizar_y_convertir_numero(ao.get("tsvd_vmax_ms")))
        ao["tsvd_ivt_cm"] = sanitizar_y_convertir_numero(ao.get("tsvd_ivt_cm"))
        ao["acct_pulmonar_ms"] = autoconvertir_tiempo_ms(sanitizar_y_convertir_numero(ao.get("acct_pulmonar_ms")))

    # 9. Válvulas
    valv = data.get("valvulas", {})
    if isinstance(valv, dict):
        valv["aortica_vmax_ms"] = autoconvertir_velocidad_ms(sanitizar_y_convertir_numero(valv.get("aortica_vmax_ms")))
        valv["aortica_grad_max_mmhg"] = sanitizar_y_convertir_numero(valv.get("aortica_grad_max_mmhg"))
        valv["aortica_grad_medio_mmhg"] = sanitizar_y_convertir_numero(valv.get("aortica_grad_medio_mmhg"))
        valv["aortica_area_cm2"] = sanitizar_y_convertir_numero(valv.get("aortica_area_cm2"))
        valv["pulmonar_vmax_ms"] = autoconvertir_velocidad_ms(sanitizar_y_convertir_numero(valv.get("pulmonar_vmax_ms")))
        valv["pulmonar_grad_max_mmhg"] = sanitizar_y_convertir_numero(valv.get("pulmonar_grad_max_mmhg"))
        for k in ["aortica_insuficiencia", "mitral_insuficiencia", "mitral_estenosis", "tricuspide_insuficiencia", "pulmonar_insuficiencia", "hallazgos_descriptivos_adicionales"]:
            valv[k] = sanitizar_texto(valv.get(k))
        if extra_de_mov and not valv.get("hallazgos_descriptivos_adicionales"):
            valv["hallazgos_descriptivos_adicionales"] = extra_de_mov

    # 10. Pericardio y Vena Cava
    pc = data.get("pericardio_cava", {})
    if isinstance(pc, dict):
        pc["derrame_pericardico"] = sanitizar_texto(pc.get("derrame_pericardico"))
        pc["cava_inferior_diametro_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(pc.get("cava_inferior_diametro_mm")), 5.0)
        pc["cava_inferior_inspiracion_mm"] = autoconvertir_cm_a_mm(sanitizar_y_convertir_numero(pc.get("cava_inferior_inspiracion_mm")), 5.0)
        colapso = sanitizar_y_convertir_numero(pc.get("cava_colapso_porcentaje"))
        if colapso is not None and 0 < colapso <= 1.0:
            colapso = round(colapso * 100.0, 1)  # 0.79 -> 79.0%
        pc["cava_colapso_porcentaje"] = colapso

    return data


# ====================================================================
# CÁLCULO DE RECALL CLÍNICO (VERIFICACIÓN EN VIVO CON SUB-CÁLCULO PSAP)
# ====================================================================
def calcular_recall_clinico(json_data: dict, ocr_texto: str) -> Dict[str, Any]:
    ocr_lower = ocr_texto.lower()
    variables_en_ocr = 0
    variables_recuperadas = 0
    detalle_variables = []

    # Asegurar que si hay gradiente IT se pre-calcule PSAP antes del check de recall
    hemo = json_data.get("hemodinamica_derecha", {})
    if isinstance(hemo, dict) and hemo.get("psap_calculada_mmhg") is None:
        grad_it = hemo.get("gradiente_it_pico_mmhg")
        pad = hemo.get("pad_estimada_mmhg") or CLINICAL_CONFIG["PAD_INSTITUCIONAL"]
        if grad_it is not None:
            hemo["psap_calculada_mmhg"] = round(grad_it + pad, 2)

    def obtener_valor_anidado(d, ruta):
        actual = d
        for parte in ruta.split('.'):
            if isinstance(actual, dict) and parte in actual:
                actual = actual[parte]
            else:
                return None
        return actual

    for ruta_json, patrones in PATRONES_OCR_RECALL.items():
        presente_en_ocr = any(re.search(pat, ocr_lower) for pat in patrones)
        if presente_en_ocr:
            variables_en_ocr += 1
            val = obtener_valor_anidado(json_data, ruta_json)
            recuperado = val is not None and str(val).strip() != ""
            if recuperado:
                variables_recuperadas += 1
            detalle_variables.append({
                "variable": ruta_json,
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
# MOTOR ROSS V12.1 - SÍNTESIS CLÍNICA AVANZADA Y AUDITADA (ASE/EACVI)
# ====================================================================
def motor_ross_y_sintesis_estricta_v12(data: dict, recall_res: dict, tiempo_total: float, archivo_nombre: str) -> dict:
    hallazgos_relevantes = []
    alertas = []
    
    pac = data.get("paciente", {})
    es_mujer = pac.get("sexo") == "femenino"

    vi = data.get("ventriculo_izquierdo", {})
    fevi = vi.get("fevi_porcentaje")
    vtd = vi.get("volumen_telediastolico_ml")
    vts = vi.get("volumen_telesistolico_ml")
    dtdvi = vi.get("dtdvi_mm")
    dtsvi = vi.get("dtsvi_mm")
    siv = vi.get("siv_mm")
    ppvi = vi.get("ppvi_mm")
    rwt = vi.get("rwt")
    masa = vi.get("masa_miocardica_g")
    imasa = vi.get("indice_masa_miocardica_g_m2")
    movilidad = vi.get("movilidad_anormal_descripcion")

    # 1. Evaluación Sistólica VI (Corrección del Bug de Severidad y Ajuste por Sexo ASE)
    umbral_fevi_normal = 54.0 if es_mujer else 52.0
    func_txt = None
    grado_disfuncion_vi = None

    if fevi is not None:
        if fevi < umbral_fevi_normal:
            if 41.0 <= fevi < umbral_fevi_normal:
                grado_disfuncion_vi = "leve"
            elif 30.0 <= fevi < 41.0:
                grado_disfuncion_vi = "moderada"
            else:
                grado_disfuncion_vi = "severa"
            
            func_txt = f"disfunción sistólica ventricular izquierda {grado_disfuncion_vi} (FEVI: {fevi}%)"
            hallazgos_relevantes.append({
                "categoria": "ventriculo_izquierdo", 
                "hallazgo": f"Disfunción sistólica {grado_disfuncion_vi} (FEVI: {fevi}%)"
            })
        else:
            func_txt = f"función sistólica global conservada (FEVI: {fevi}%)"

    # 2. Trazabilidad de Dilatación VI (Ajustada por Sexo)
    umbral_dtdvi = 52.0 if es_mujer else 58.0
    umbral_vtd = 106.0 if es_mujer else 150.0
    dilatacion_vi = False
    causa_dilatacion = None
    if vtd is not None and vtd > umbral_vtd:
        dilatacion_vi = True
        causa_dilatacion = "volumen"
    elif dtdvi is not None and dtdvi > umbral_dtdvi:
        dilatacion_vi = True
        causa_dilatacion = "diámetro"

    if dilatacion_vi:
        alerta_dil = f"Dilatación ventricular izquierda a expensas de {causa_dilatacion} (VTD: {vtd} ml, DTDVI: {dtdvi} mm)."
        alertas.append(alerta_dil)
        hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": f"Dilatación ventricular izquierda ({causa_dilatacion})", "evidencia": {"VTD": vtd, "DTDVI": dtdvi}})

    # 3. Geometría Ventricular: Masa, Índice de Masa y RWT (Guías ASE)
    umbral_imasa = 95.0 if es_mujer else 115.0
    umbral_masa = 162.0 if es_mujer else 224.0
    hipertrofia_vi = False
    remodelado_concentrico = False
    geometria_txt = None

    if imasa is not None and imasa > umbral_imasa:
        hipertrofia_vi = True
        if rwt is not None:
            tipo_hvi = "concéntrica" if rwt > 0.42 else "excéntrica"
            geometria_txt = f"Hipertrofia ventricular izquierda {tipo_hvi} (índice de masa: {imasa} g/m², RWT: {rwt})"
        else:
            geometria_txt = f"Hipertrofia ventricular izquierda (índice de masa: {imasa} g/m²)"
        hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": geometria_txt})
    elif masa is not None and masa > umbral_masa:
        hipertrofia_vi = True
        geometria_txt = f"Aumento de la masa miocárdica ({masa} g)"
        hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": geometria_txt})
    elif rwt is not None and rwt > 0.42:
        remodelado_concentrico = True
        geometria_txt = f"Remodelado concéntrico del ventrículo izquierdo (RWT: {rwt})"
        hallazgos_relevantes.append({"categoria": "ventriculo_izquierdo", "hallazgo": geometria_txt})

    # 4. Motilidad Segmentaria (Solo si es genuinamente anormal)
    if movilidad:
        hallazgos_relevantes.append({"categoria": "motilidad", "hallazgo": f"Alteración de la motilidad segmentaria: {movilidad}"})

    # 5. Hemodinamia y PSAP (Persistencia en JSON garantizada)
    hemo = data.get("hemodinamica_derecha", {})
    pad_usada = hemo.get("pad_estimada_mmhg") or CLINICAL_CONFIG["PAD_INSTITUCIONAL"]
    psap = hemo.get("psap_calculada_mmhg")
    if psap is None and hemo.get("gradiente_it_pico_mmhg") is not None:
        psap = round(hemo.get("gradiente_it_pico_mmhg") + pad_usada, 2)
        hemo["psap_calculada_mmhg"] = psap
    
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
            hap_txt = f"PSAP estimada en {psap} mmHg (dentro de límites normales)"

    # 6. Función Diastólica
    fd = data.get("funcion_diastolica_bruta", {})
    e_wave = fd.get("onda_e_cm_s")
    a_wave = fd.get("onda_a_cm_s")
    e_e_prime = fd.get("relacion_e_e_prima")
    
    diastole_txt = None
    if e_e_prime is not None and e_e_prime > 14.0:
        diastole_txt = f"elevación de las presiones de llenado ventricular izquierdo (E/e' promedio = {e_e_prime})"
        hallazgos_relevantes.append({"categoria": "funcion_diastolica", "hallazgo": f"Presiones de llenado VI elevadas (E/e' = {e_e_prime})"})
    elif e_wave is not None and a_wave is not None and e_wave < a_wave:
        diastole_txt = f"alteración de la relajación miocárdica (patrón E < A, relación E/A de {fd.get('relacion_e_a')})"
        hallazgos_relevantes.append({"categoria": "funcion_diastolica", "hallazgo": "Disfunción diastólica grado I (alteración de la relajación)"})

    # 7. Función VD (TAPSE + S' + CAFVD)
    vd = data.get("ventriculo_derecho", {})
    vd_basal = vd.get("diametro_basal_mm")
    tapse = vd.get("tapse_mm")
    onda_s = vd.get("onda_s_cm_s")
    cafvd = vd.get("cafvd_porcentaje")
    
    vd_disfuncion = False
    if (tapse is not None and tapse < 17.0) or (onda_s is not None and onda_s < 9.5) or (cafvd is not None and cafvd < 35.0):
        vd_disfuncion = True
        hallazgos_relevantes.append({"categoria": "ventriculo_derecho", "hallazgo": f"Disfunción sistólica ventricular derecha (TAPSE: {tapse} mm, CAFVD: {cafvd}%)"})

    pc = data.get("pericardio_cava", {})
    derrame = pc.get("derrame_pericardico")
    if derrame:
        hallazgos_relevantes.append({"categoria": "pericardio", "hallazgo": f"Derrame pericárdico {derrame}"})

    # 8. Auditoría AI
    ai = data.get("auricula_izquierda", {})
    ai_ap = ai.get("diametro_ap_mm")
    ai_vol = ai.get("volumen_ml")
    ai_index = ai.get("volumen_indexado_ml_m2")
    ai_area = ai.get("area_cm2")
    
    ai_dilatacion_confirmada = False
    ai_marcador_revision = False
    if ai_index is not None and ai_index > 34.0:
        ai_dilatacion_confirmada = True
        hallazgos_relevantes.append({"categoria": "auricula_izquierda", "hallazgo": f"Dilatación auricular izquierda (LAVI: {ai_index} ml/m²)"})
    elif ai_ap is not None and ai_ap > 40.0 and ai_index is None:
        ai_marcador_revision = True

    # 9. Descripción Ecocardiográfica (Fluida, Natural y Completa)
    frases_desc = []

    vi_fragmentos = []
    if dtdvi or dtsvi: vi_fragmentos.append(f"diámetros de {dtdvi} mm en telediástole y {dtsvi} mm en telesístole")
    if vtd or vts: vi_fragmentos.append(f"volúmenes cavitarios con VTD de {vtd} ml y VTS de {vts} ml")
    if siv or ppvi:
        esp_str = f"espesores parietales de SIV: {siv} mm y PPVI: {ppvi} mm"
        if rwt is not None: esp_str += f" (RWT: {rwt})"
        vi_fragmentos.append(esp_str)
    if masa or imasa: vi_fragmentos.append(f"masa miocárdica de {masa} g (índice de masa: {imasa} g/m²)")
    
    if vi_fragmentos or func_txt or movilidad:
        base_vi = "Se observa ventrículo izquierdo con " + ", ".join(vi_fragmentos) if vi_fragmentos else "Ventrículo izquierdo"
        if func_txt: base_vi += f", evidenciando {func_txt}"
        if movilidad: base_vi += f". Se aprecian alteraciones segmentarias caracterizadas por {movilidad}"
        else: base_vi += ", sin alteraciones de la movilidad global ni segmentaria"
        frases_desc.append(base_vi + ".")

    if ai_ap or ai_vol or ai_index or ai_area:
        ai_parts = []
        if ai_ap: ai_parts.append(f"diámetro anteroposterior de {ai_ap} mm")
        if ai_area: ai_parts.append(f"área planimétrica de {ai_area} cm²")
        if ai_vol: ai_parts.append(f"volumen de {ai_vol} ml")
        if ai_index: ai_parts.append(f"volumen indexado de {ai_index} ml/m²")
        
        ai_str = f"La aurícula izquierda presenta {', '.join(ai_parts)}."
        if ai_dilatacion_confirmada:
            ai_str += " Se documenta dilatación auricular izquierda."
        elif ai_marcador_revision:
            ai_str += " (Nota: Diámetro AP elevado pendiente de correlación volumétrica)."
        frases_desc.append(ai_str)

    if vd_basal or tapse or onda_s or cafvd:
        vd_parts = []
        if vd_basal: vd_parts.append(f"diámetro basal de {vd_basal} mm")
        if tapse: vd_parts.append(f"TAPSE de {tapse} mm")
        if cafvd: vd_parts.append(f"CAFVD de {cafvd}%")
        if onda_s: vd_parts.append(f"onda tisular S' de {onda_s} cm/s")
        
        vd_str = f"Cavidades derechas con ventrículo que muestra {', '.join(vd_parts)}."
        if vd_disfuncion:
            vd_str += " Se observa alteración de la función sistólica longitudinal."
        frases_desc.append(vd_str)

    ad = data.get("auricula_derecha", {})
    ad_area = ad.get("area_cm2")
    ad_vol = ad.get("volumen_ml")
    ad_ivol = ad.get("volumen_indexado_ml_m2")
    if ad_area or ad_vol or ad_ivol:
        ad_parts = []
        if ad_area: ad_parts.append(f"área de {ad_area} cm²")
        if ad_vol: ad_parts.append(f"volumen de {ad_vol} ml")
        if ad_ivol: ad_parts.append(f"volumen indexado de {ad_ivol} ml/m²")
        frases_desc.append(f"Aurícula derecha con {', '.join(ad_parts)}.")

    ao = data.get("aorta_y_tractos", {})
    if ao.get("raiz_aortica_mm") or ao.get("senos_valsalva_mm") or ao.get("union_st_mm"):
        ao_parts = []
        if ao.get("raiz_aortica_mm"): ao_parts.append(f"anillo/raíz de {ao['raiz_aortica_mm']} mm")
        if ao.get("senos_valsalva_mm"): ao_parts.append(f"senos de Valsalva de {ao['senos_valsalva_mm']} mm")
        if ao.get("union_st_mm"): ao_parts.append(f"unión sinotubular de {ao['union_st_mm']} mm")
        frases_desc.append(f"Raíz aórtica con {', '.join(ao_parts)}.")

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
            if any(term in grado_lower for term in ["moderada", "severa", "importante", "significativa"]):
                hallazgos_relevantes.append({"categoria": "valvulas", "hallazgo": f"Insuficiencia {v_label} {grado}"})
            valv_textos.append(f"insuficiencia {v_label} {grado}")

    if valv_textos:
        frases_desc.append(f"Al examen Doppler se identifica: {', '.join(valv_textos)}.")
    if valv.get("hallazgos_descriptivos_adicionales"):
        frases_desc.append(f"Hallazgos valvulares/estructurales: {valv['hallazgos_descriptivos_adicionales']}.")
        hallazgos_relevantes.append({"categoria": "valvulas", "hallazgo": valv["hallazgos_descriptivos_adicionales"]})

    if diastole_txt:
        frases_desc.append(f"En el análisis diastólico se observa {diastole_txt}.")
    elif e_e_prime is not None:
        frases_desc.append(f"Función diastólica con relación E/e' promedio de {e_e_prime} (presiones de llenado normales).")

    if hap_txt:
        frases_desc.append(f"En la evaluación hemodinámica se registra {hap_txt}.")

    cava_d = pc.get("cava_inferior_diametro_mm")
    cava_col = pc.get("cava_colapso_porcentaje")
    if cava_d is not None:
        cava_str = f"Vena cava inferior de {cava_d} mm"
        if cava_col is not None: cava_str += f" con colapso inspiratorio de {cava_col}%"
        frases_desc.append(cava_str + ".")

    if derrame:
        frases_desc.append(f"Se documenta presencia de derrame pericárdico {derrame}.")

    descripcion_corrida = " ".join(frases_desc)

    # 10. Conclusiones Clínicas (Estrictamente Patológicas y Sincronizadas)
    conclusiones = []
    
    if grado_disfuncion_vi:
        conclusiones.append(f"Disfunción sistólica ventricular izquierda {grado_disfuncion_vi} (FEVI: {fevi}%).")
    if dilatacion_vi:
        conclusiones.append(f"Dilatación ventricular izquierda a expensas de {causa_dilatacion}.")
    if hipertrofia_vi or remodelado_concentrico:
        conclusiones.append(f"{geometria_txt}.")
    if ai_dilatacion_confirmada:
        conclusiones.append(f"Dilatación auricular izquierda (LAVI: {ai_index} ml/m²).")
    if vd_disfuncion:
        conclusiones.append(f"Disfunción sistólica del ventrículo derecho (TAPSE: {tapse} mm).")
    if diastole_txt:
        conclusiones.append(f"Disfunción diastólica con {diastole_txt}.")
    if psap is not None and psap >= CLINICAL_CONFIG["UMBRAL_HAP_BAJA"]:
        conclusiones.append(f"Elevación de la presión pulmonar sistólica estimada en {psap} mmHg.")
    if movilidad:
        conclusiones.append(f"Trastorno de la motilidad parietal segmentaria: {movilidad}.")
    if valv.get("hallazgos_descriptivos_adicionales"):
        conclusiones.append(f"{valv['hallazgos_descriptivos_adicionales']}.")
    if derrame:
        conclusiones.append(f"Derrame pericárdico {derrame}.")

    conclusiones = conclusiones[:7]
    if not conclusiones:
        conclusiones.append("Estudio ecocardiográfico sin alteraciones estructurales o funcionales mayores consignadas.")

    # 11. Diagnóstico Final (Sincronizado con Grado Real de FEVI y Geometría)
    diag_componentes = []
    
    if movilidad:
        diag_componentes.append(f"compromiso segmentario ({movilidad})")
    
    if grado_disfuncion_vi:
        diag_componentes.append(f"disfunción sistólica ventricular izquierda {grado_disfuncion_vi} (FEVI: {fevi}%)")
    
    if dilatacion_vi: 
        diag_componentes.append(f"dilatación ventricular izquierda ({causa_dilatacion})")
        
    if hipertrofia_vi or remodelado_concentrico: 
        diag_componentes.append(geometria_txt.lower())
        
    if ai_dilatacion_confirmada: 
        diag_componentes.append(f"dilatación auricular izquierda (LAVI: {ai_index} ml/m²)")
        
    if vd_disfuncion: 
        diag_componentes.append("afectación de la función sistólica del ventrículo derecho")
        
    if diastole_txt: 
        diag_componentes.append(diastole_txt)

    valv_significativas = [
        f"insuficiencia {v_label} {valv.get(vk)}" 
        for vk, v_label in [("aortica_insuficiencia", "aórtica"), ("mitral_insuficiencia", "mitral"), ("tricuspide_insuficiencia", "tricuspídea")] 
        if valv.get(vk) and any(t in str(valv.get(vk)).lower() for t in ["moderada", "severa", "importante"])
    ]
    if valv_significativas:
        diag_componentes.append("valvulopatía asociada tipo " + " y ".join(valv_significativas))
    elif valv.get("hallazgos_descriptivos_adicionales"):
        diag_componentes.append(valv["hallazgos_descriptivos_adicionales"].lower())

    if derrame:
        diag_componentes.append(f"con derrame pericárdico {derrame}")

    if diag_componentes:
        diagnostico_final = "Impresión diagnóstica: Ecocardiograma transtorácico que demuestra " + ", ".join(diag_componentes) + "."
    else:
        diagnostico_final = "Impresión diagnóstica: Ecocardiograma transtorácico sin alteraciones patológicas relevantes evaluadas."

    # 12. JSON Maestro v12.1 Completo y Trazable
    json_maestro = {
        "paciente": pac,
        "variables_ecocardiograficas": {
            "ventriculo_izquierdo": vi,
            "auricula_izquierda": ai,
            "ventriculo_derecho": vd,
            "auricula_derecha": ad,
            "hemodinamica_derecha": hemo,
            "funcion_diastolica_bruta": fd,
            "aorta_y_tractos": ao,
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
            "version_motor": "CardioAgente Extractor Maestro v12.1 (Chison Dual & Autocalibrado)"
        }
    }

    return json_maestro


# ====================================================================
# INTERFAZ STREAMLIT - APLICACIÓN 1 (V12.1)
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
            if st.button("🚀 Ejecutar Extracción y Cerebro Clínico v12.1", use_container_width=True):
                status_placeholder = st.empty()
                
                try:
                    t_inicio_total = time.time()

                    # 1. OCR
                    status_placeholder.info("🔄 Procesando OCR adaptativo del PDF...")
                    file_bytes = uploaded_file.read()
                    texto_ocr, reporte_ocr = extraer_pdf_adaptativo(file_bytes)

                    # 2. Llamada única a Gemini (Manteniendo gemini-3.8-flash)
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

                    # 3. Normalización y Síntesis v12.1
                    status_placeholder.info("🔄 Ejecutando normalización fisiológica y síntesis clínica...")
                    json_normalizado = normalizar_datos(json_crudo)
                    recall_res = calcular_recall_clinico(json_normalizado, texto_ocr)
                    
                    tiempo_total = round(time.time() - t_inicio_total, 3)

                    json_maestro_final = motor_ross_y_sintesis_estricta_v12(
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

                    status_placeholder.success(f"✅ JSON Maestro v12.1 generado con éxito en {tiempo_total}s (Recall Clínico: {recall_res['recall_clinico_pct']}%)")

                except Exception as e:
                    status_placeholder.error(f"❌ Error crítico en el Extractor: {str(e)}")

# ====================================================================
# VISUALIZACIÓN Y DESCARGA DEL JSON MAESTRO V12.1
# ====================================================================
if "json_maestro" in st.session_state:
    st.markdown("---")
    st.markdown("### 📊 Inspección del JSON Maestro v12.1 (Auditoría Final)")
    
    maestro = st.session_state["json_maestro"]
    recall = maestro.get("recall_clinico", {})
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Recall Clínico", f"{recall.get('recall_clinico_pct', 0)}%")
    with c2: st.metric("Variables Detectadas", f"{recall.get('variables_en_ocr', 0)}")
    with c3: st.metric("Variables Recuperadas", f"{recall.get('variables_recuperadas', 0)}")

    st.markdown("#### 📝 Vista Previa del Contenido Clínico Definitivo")
    st.info(f"**Diagnóstico Final:** {maestro.get('diagnostico')}")
    st.write(f"**Descripción Ecocardiográfica:** {maestro.get('descripcion_ecocardiografica')}")
    
    st.write("**Conclusiones Clínicas:**")
    for idx, c in enumerate(maestro.get("conclusiones", []), 1):
        st.markdown(f"*{idx}.* {c}")

    st.markdown("#### 📦 JSON Maestro v12.1 Completo")
    json_str = json.dumps(maestro, ensure_ascii=False, indent=2)
    
    st.code(json_str, language="json")
    
    st.download_button(
        label="💾 Descargar JSON Maestro v12.1",
        data=json_str,
        file_name=f"json_maestro_v12_{maestro.get('paciente', {}).get('nombre', 'paciente').replace(' ', '_').replace(',', '')}.json",
        mime="application/json",
        use_container_width=True
    )
