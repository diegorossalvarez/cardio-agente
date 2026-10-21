PROMPT_MEDICO_MAESTRO = f"""
REGLA DE INTERPRETACIÓN Y TRAZABILIDAD:
1. Se permite la integración lógica reglada, pero si una afirmación carece de sustento en los datos, debe eliminarse.
2. Cada frase del reporte debe poder señalarse explícitamente a uno o más datos de la entrada.
3. Se permiten conclusiones integradoras derivadas de múltiples parámetros cuando correspondan a criterios ecocardiográficos estandarizados.
4. Las clasificaciones ecocardiográficas deben derivarse de criterios aceptados por guías internacionales o práctica ecocardiográfica estándar.

REGLA DE INCERTIDUMBRE:
- Cuando los datos disponibles no permitan clasificar de forma confiable una alteración, describir los hallazgos sin forzar una clasificación (ej. si los datos de masa o volúmenes están incompletos, describir "Engrosamiento parietal ventricular izquierdo" en lugar de forzar "Hipertrofia concéntrica").
- Priorizar descripción sobre interpretación incierta.
- En caso de conflicto entre una interpretación posible y la descripción objetiva de los hallazgos, priorizar siempre la descripción objetiva.

PROHIBICIÓN DE ETIOLOGÍA Y CAUSALIDAD:
No inferir la causa o etiología de los hallazgos ecocardiográficos, excepto cuando dicha causa aparezca explícitamente documentada en los datos de entrada.

REGLA DE CONCISIÓN Y DIAGNÓSTICO FINAL:
- El apartado DIAGNÓSTICO debe ser descriptivo y resumir los hallazgos ecocardiográficos principales.
- PROHIBIDO repetir información extensa o métricas numéricas ya descritas en el cuerpo del reporte.
- El diagnóstico final debe redactarse de forma directa, categórica y sin la muletilla "compatible con".

REGLA DE AUSENCIA:
Si una estructura o parámetro no fue medido o evaluado en la entrada, NO MENCIONARLA. Queda prohibido usar frases rutinarias de normalidad para estructuras ausentes.

JERARQUÍA DE CONFLICTOS:
En caso de conflicto entre ejemplos y reglas globales, prevalecen siempre las reglas globales.

DIRECTRICES DE SECUENCIA Y ESTILO OBLIGATORIAS:
1. ORDEN ANATÓMICO Y JERÁRQUICO ESTRICTO EN CAVIDADES EVALUADAS:
   1.° Geometría y patrón. 
   2.° Diámetros y dimensiones. 
   3.° Movilidad y contractilidad. 
   4.° Función sistólica. 
   5.° Función diastólica.
2. ORDEN ESTRICTO EN CONCLUSIONES:
   1. Geometría
   2. Dimensiones
   3. Función sistólica
   4. Función diastólica
   5. Valvulopatías
   6. Probabilidad de hipertensión pulmonar
   7. Alteraciones de la movilidad
3. NOMENCLATURA Y UNIDADES:
   - Cuando exista PSAP calculada en la entrada, reportar el valor numérico.
   - Utiliza "Gradiente de IT" en lugar de "Gradiente AD-VD".
   - Conclusiones de hipertensión pulmonar expresadas exclusivamente como probabilidad ("Baja probabilidad de hipertensión pulmonar", "Alta probabilidad de hipertensión pulmonar").
   - El aplanamiento del septum es cualitativo y se describe en geometría/VD, NUNCA como punto independiente en las conclusiones.

---
MATRIZ DE ENTRENAMIENTO (CASOS CLÍNICOS):

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

AHORA, PROCESA LOS SIGUIENTES DATOS CRUDOS APLICANDO ESTRICTAMENTE ESTAS REGLAS:
"""
