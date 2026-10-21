# Muestras definitivas con trazabilidad 1:1 estricta (Entrada Cruda vs Reporte Ross)
# Regla absoluta: Si no viene en la entrada, NO se escribe en la salida.

# ejemplos_ross_v2.py

EJEMPLO_1_NORMAL = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: ZARATE MEDINA IRVING ARAY, 25 AÑOS, ASC 1.96 m2.
AI: LAVI 22 mL/m2, diámetro 37 mm.
AD: RAVI 25 mL/m2, área 16.6 cm2.
VI: DDVI 42 mm, SIV 10 mm, PP 8 mm, VTD 124 ml, VTS 52 ml, masa indexada 71 gr/m2, GPR 0.39, FEVI Simpson 57%, Onda E 85 cm/s, Onda A 59 cm/s, E/A 1.4, TDA 160 ms, TRIV 80 ms, E' lateral 15 cm/s, E' medial 12 cm/s, E/e' 5.
VD: Diámetros 38x25x74 mm, TAPSE 24 mm, onda s' tisular 15 cm/s, FACVD 45%.
Válvula Mitral: AVM THP 4.7 cm2, sin insuficiencia.
Válvula Tricúspide: Velocidad IT 1.5 m/s, Gradiente de IT 9 mmHg.
Válvula Aórtica: Avao 3.3 cm2, vel TSVI 0.93 m/s, vel Ao 1.1 m/s, anillo 22 mm, SV 29 mm, UST 23 mm, Ao asc 27 mm.
Válvula Pulmonar: Vel TSVD 70 cm/s, vel Pulmonar 95 cm/s, TSVD prox 24 mm, TAcp 140 ms, PSAP estimada 14 mmHg.
Pericardio: Pericardio de aspecto normal.
Vena Cava Inferior: 15 mm, colapso >60%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ZARATE MEDINA IRVING ARAY
EDAD: 25 ANOS | ASC: 1.96 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: tamaño normal, lavi 22 mL/m2, diámetro AI 37 mm.
• Auricula derecha: tamaño normal, ravi 25 mL/m2, area 16.6 cm2.
• Ventriculo izquierdo: geometría normal, diámetros de cavidades normales con DDVI 42 mm, SIV 10 mm, PP 8 mm, VTD 124 ml, VTS 52 ml, masa indexada 71 gr/m2, GPR 0.39; movilidad global y segmentaria normal; función sistólica con fevi simpson modificado 57%; función diastolica normal con onda E 85 cm/s, onda A 59 cm/s, E/A 1.4, TDA 160ms, TRIV 80ms, E tisular lateral 15 cm/s, E tisular medial 12 cm/s, E/e' 5.
• Ventriculo derecho: diámetros de cavidades de 38x25x74 mm; función sistólica global y longitudinal normal con TAPSE 24 mm, onda s tisular tricuspidea 15 cm/s y FACVD 45%.
• Valvula mitral: AVM por THP 4.7 cm2, sin insuficiencia.
• Valvula tricuspide: velocidad de IT 1.5 m/seg, gradiente de IT 9 mmhg.
• Valvula aortica: Avao por continuidad 3.3 cm2, vel TSVI 0.93 m/s, vel AO 1.1 m/s, raíz de tamaño normal, anillo 22 mm, SV 29 mm, UST 23 mm, AO asc 27 mm.
• Valvula pulmonar: Vel TSVD 70 cm/s, vel Pulmonar 95 cm/s, TSVD prox 24 mm, TAcp 140ms, presión sistólica pulmonar estimada 14 mmhg.
• Pericardio de aspecto normal.
• Cava inferior: 15 mm, colapso mas del 60%.

CONCLUSIONES:
1. Geometría normal.
2. Dimensiones de cavidades normales.
3. Función sistólica de ambos ventrículos normal.
4. Función diastólica normal.
5. Sin valvulopatías.
6. Baja probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Estudio ecocardiográfico dentro de parámetros normales; sin cardiopatía estructural.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_2_HIPERTROFIA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: ALVARO DAMIAN CORREA, 34 AÑOS, ASC 2.1 m2.
AI: LAVI 30 mL/m2, diámetro 31 mm.
AD: RAVI 28 mL/m2, área 18.3 cm2.
VI: DDVI 47 mm, DSVI 32 mm, SIV 10 mm, PP 11 mm, VTD 140 ml, VTS 50 ml, masa indexada 109 gr/m2, GPR 0.49, FEVI Simpson 62%, Onda E 82 cm/s, Onda A 52 cm/s, E/A 1.5, TDA 160 ms, TRIV 90 ms, E' lateral 16 cm/s, E' medial 15 cm/s, E/e' 5.
VD: Diámetros 46x30x78 mm, onda s' tisular 12.3 cm/s.
Válvula Mitral: AVM THP 4.7 cm2, sin insuficiencia.
Válvula Tricúspide: Velocidad IT 1.4 m/s, Gradiente de IT 8 mmHg.
Válvula Aórtica: Avao 3.2 cm2, vel TSVI 1 m/s, vel Ao 1.2 m/s, SV 37 mm, UST 33 mm, Ao asc 29 mm, anillo 22 mm.
Válvula Pulmonar: Vel TSVD 88 cm/s, vel Pulmonar 1.5 m/s, TSVD prox 27 mm, TAcp 180 ms, PSAP estimada 12 mmHg.
Pericardio: Pericardio de aspecto normal.
Vena Cava Inferior: 15 mm, colapso >60%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ALVARO DAMIAN CORREA
EDAD: 34 ANOS | ASC: 2.1 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: tamaño normal, lavi 30 mL/m2, diámetro AI 31 mm.
• Auricula derecha: tamaño normal, ravi 28 mL/m2, area 18.3 cm2.
• Ventriculo izquierdo: geometría con remodelado concéntrico, diámetros con DDVI 47 mm, DSVI 32 mm, SIV 10 mm, PP 11 mm, VTD 140 ml, VTS 50 ml, masa indexada 109 gr/m2, GPR 0.49; movilidad global y segmentaria normal; función sistólica con fevi simpson modificado 62%; función diastolica normal con onda E 82 cm/s, onda A 52 cm/s, E/A 1.5, TDA 160ms, TRIV 90ms, E tisular lateral 16 cm/s, E tisular medial 15 cm/s, E/e' 5.
• Ventriculo derecho: levemente dilatado en la base, diametros 46x30x78 mm, funcion sistólica longitudinal normal con onda s tisular tricuspidea 12.3 cm/s.
• Valvula mitral: AVM por THP 4.7 cm2, sin insuficiencia.
• Valvula tricuspide: velocidad de IT 1.4 m/seg, gradiente de IT 8 mmhg.
• Valvula aortica: Avao por continuidad 3.2 cm2, vel TSVI 1 m/s, vel AO 1.2 m/s, raíz de tamaño normal, anillo 22 mm, SV 37 mm, UST 33 mm, AO asc 29 mm.
• Valvula pulmonar: Vel TSVD 88 cm/s, vel Pulmonar 1.5 m/s, TSVD prox 27 mm, TAcp 180ms, presión sistólica pulmonar estimada 12 mmhg.
• Pericardio de aspecto normal.
• Cava inferior: 15 mm, colapso mas del 60%.

CONCLUSIONES:
1. Remodelado concéntrico del ventrículo izquierdo.
2. Dimensiones de cavidades normales (excepto dilatación basal leve de ventrículo derecho).
3. Función sistólica de ventrículo izquierdo conservada y función sistólica longitudinal de ventrículo derecho normal.
4. Función diastólica normal.
5. Sin valvulopatías.
6. Baja probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Remodelado concéntrico ventricular izquierdo; función sistólica y diastólica conservadas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_3_FEVI_DEPRIMIDA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: HUGO MARTINEZ VALENCIA, 46 AÑOS, ASC 2.12 m2.
AI: Diámetro AI 46 mm, área AI 21.3 cm2.
AD: Área AD 19.3 cm2.
VI: DDVI 55 mm, DSVI 43 mm, SIV 11 mm, PP 11 mm, VTD 176 ml, VTS 134 ml, masa indexada 135.8 gr/m2, GPR 0.39.
Trastornos segmentarios VI: Acinesia apical, discinesia anteroapical, inferoapical, septoapical y lateroapical, acinesia inferoseptal medial/basal, acinesia anteroseptal basal/medial.
FEVI Simpson biplano 24%. Onda E 84 cm/s, Onda A 69 cm/s, E/A 1.2, TDA 130 ms, E' lateral 7.9 cm/s, E' medial 6.6 cm/s, E/e' medial 12.7, E/e' lateral 10.6.
VD: Diámetro basal 40 mm, TAPSE 16 mm, onda s' tisular 6.7 cm/s.
Válvula Mitral: AVM THP 5.6 cm2, gradiente medio 2.8 mmHg.
Válvula Tricúspide: Velocidad IT 2.29 m/s, Gradiente de IT 21 mmHg.
Válvula Aórtica: Vmax 67 cm/s, gradiente medio 0.5 mmHg. SV 35 mm, UST 33 mm, Ao tubular 36 mm.
Válvula Pulmonar: TSVD Vmax 56 cm/s, gradiente medio 0.5 mmHg, PSAP estimada 26 mmHg.
Vena Cava Inferior: 19 mm, colapso >50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: HUGO MARTINEZ VALENCIA
EDAD: 46 ANOS | ASC: 2.12 m²

Se realizo ecocardiograma transtoracico en reposo, ventana acústica aceptable, ritmo sinusal.

• Auricula izquierda: dilatada, diámetro AI 46 mm, área AI 21.3 cm².
• Auricula derecha: área AD 19.3 cm².
• Ventriculo izquierdo: geometría con hipertrofia excéntrica, diámetros dilatados con DDVI 55 mm, DSVI 43 mm, SIV 11 mm, PP 11 mm, VTD 176 ml, VTS 134 ml, masa indexada 135.8 gr/m2, GPR 0.39; trastorno segmentario de la contractilidad miocárdica caracterizado por acinesia apical, discinesia anteroapical, inferoapical, septoapical y lateroapical, acinesia inferoseptal medial y basal, acinesia anteroseptal basal y medial; función sistólica con fevi simpson biplano 24% (severamente deprimida); función diastólica con onda E 84 cm/s, onda A 69 cm/s, E/A 1.2, TDA 130 ms, E tisular lateral 7.9 cm/s, E tisular medial 6.6 cm/s, E/e' medial 12.7, E/e' lateral 10.6.
• Ventriculo derecho: dilatado en su porción basal (diámetro basal 40 mm); función sistólica longitudinal deprimida con TAPSE 16 mm y onda s tisular tricúspidea 6.7 cm/s.
• Valvula mitral: AVM por THP 5.6 cm2, gradiente medio 2.8 mmHg.
• Valvula tricuspide: velocidad de IT 2.29 m/s, gradiente de IT 21 mmHg.
• Valvula aortica: Vmax 67 cm/s, gradiente medio 0.5 mmHg. Raíz aórtica: senos de Valsalva 35 mm, unión sinotubular 33 mm, aorta tubular 36 mm.
• Valvula pulmonar: TSVD Vmax 56 cm/s, gradiente medio 0.5 mmHg, presión sistólica pulmonar estimada 26 mmHg.
• Cava inferior: 19 mm con colapso mayor al 50%.

CONCLUSIONES:
1. Hipertrofia excéntrica del ventrículo izquierdo.
2. Dilatación de cavidades izquierdas y porción basal de ventrículo derecho.
3. Función sistólica de ventrículo izquierdo severamente deprimida (FEVI 24%) y disfunción sistólica longitudinal de ventrículo derecho.
4. Función diastólica normal en parámetros evaluados.
5. Sin valvulopatías significativas.
6. Baja probabilidad de hipertensión pulmonar.
7. Alteración severa de la motilidad segmentaria (acinesia/discinesia apical y antero/inferoseptal).

DIAGNOSTICO:
Disfunción sistólica severa del ventrículo izquierdo con alteraciones severas de la contractilidad segmentaria.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_4_VALVULOPATIA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: PATRICIA GOMEZ RUIZ, 62 AÑOS, ASC 1.68 m2.
AI: Diámetro AI 44 mm, LAVI 38 mL/m2.
AD: Área AD 18 cm2.
VI: DDVI 48 mm, SIV 12 mm, PP 11 mm, masa indexada 125 gr/m2, GPR 0.52, FEVI 55%, Onda E 65 cm/s, Onda A 78 cm/s, E/A 0.8, TDA 220 ms, E' lateral 7 cm/s, E' medial 6 cm/s, E/e' 10.
VD: TAPSE 20 mm, onda s' tisular 11 cm/s.
Válvula Aórtica: Calcificada con apertura restrictiva, AVAo por continuidad 0.8 cm2, Vmax Ao 4.2 m/s, Gradiente medio Ao 45 mmHg.
Válvula Mitral: Calcificación del anillo mitral, insuficiencia mitral leve.
Válvula Tricúspide: Velocidad IT 3.1 m/s, Gradiente de IT 38 mmHg.
Válvula Pulmonar: PSAP estimada 43 mmHg.
Vena Cava Inferior: 22 mm, colapso <50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: PATRICIA GOMEZ RUIZ
EDAD: 62 ANOS | ASC: 1.68 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: dilatada, diámetro AI 44 mm, LAVI 38 mL/m2.
• Auricula derecha: tamaño normal, área AD 18 cm2.
• Ventriculo izquierdo: geometría con hipertrofia concéntrica, diámetros normales con DDVI 48 mm, SIV 12 mm, PP 11 mm, masa indexada 125 gr/m2, GPR 0.52; movilidad global y segmentaria normal; función sistólica con fevi 55%; función diastólica con patrón de alteración de la relajación (onda E 65 cm/s, onda A 78 cm/s, E/A 0.8, TDA 220 ms, E' lateral 7 cm/s, E' medial 6 cm/s, E/e' 10).
• Ventriculo derecho: función sistólica longitudinal normal con TAPSE 20 mm y onda s' tisular tricúspidea 11 cm/s.
• Valvula mitral: calcificación del anillo mitral, insuficiencia mitral leve.
• Valvula tricuspide: velocidad de IT 3.1 m/s, gradiente de IT 38 mmHg.
• Valvula aortica: calcificación severa de cúspides y apertura restrictiva, estenosis aórtica severa con área valvular aórtica por continuidad de 0.8 cm2, velocidad máxima aórtica 4.2 m/s, gradiente medio aórtico de 45 mmHg.
• Valvula pulmonar: presión sistólica pulmonar estimada 43 mmHg.
• Cava inferior: 22 mm con colapso menor al 50%.

CONCLUSIONES:
1. Hipertrofia concéntrica del ventrículo izquierdo.
2. Dimensiones de cavidades ventriculares normales con aurícula izquierda dilatada.
3. Función sistólica de ventrículo izquierdo conservada y función sistólica longitudinal de ventrículo derecho normal.
4. Disfunción diastólica tipo relajación lenta del ventrículo izquierdo.
5. Estenosis aórtica severa e insuficiencia mitral leve.
6. Alta probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Estenosis aórtica severa calcificada e insuficiencia mitral leve; hipertrofia concéntrica del ventrículo izquierdo con función sistólica conservada; alta probabilidad de hipertensión pulmonar.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_5_HAP = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: ROBERTO HERNANDEZ PEREZ, 50 AÑOS, ASC 1.85 m2.
AI: Diámetro AI 34 mm.
AD: Área AD 26 cm2.
VI: DDVI 44 mm, SIV 9 mm, PP 9 mm, masa indexada 82 gr/m2, GPR 0.41, FEVI 60%, aplanamiento sistólico del septo interventricular.
VD: Diámetro basal 48 mm, medio 36 mm, longitudinal 82 mm, TAPSE 14 mm, onda s' tisular 8 cm/s.
Válvula Tricúspide: Insuficiencia tricuspidea moderada, velocidad de IT 3.8 m/s, Gradiente de IT 58 mmHg.
Válvula Pulmonar: TAP 75 ms, insuficiencia pulmonar con gradiente diastólico inicial 25 mmHg, PSAP estimada 64 mmHg.
Vena Cava Inferior: 24 mm, colapso <50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ROBERTO HERNANDEZ PEREZ
EDAD: 50 ANOS | ASC: 1.85 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: tamaño normal, diámetro AI 34 mm.
• Auricula derecha: dilatada, área AD 26 cm2.
• Ventriculo izquierdo: geometría normal, dimensiones normales con DDVI 44 mm, SIV 9 mm, PP 9 mm, masa indexada 82 gr/m2, GPR 0.41; aplanamiento sistólico del septo interventricular; movilidad global y segmentaria normal; función sistólica con fevi 60%; función diastólica normal.
• Ventriculo derecho: dilatado en su porción basal (diámetro basal 48 mm, medio 36 mm, longitudinal 82 mm); función sistólica longitudinal deprimida con TAPSE 14 mm y onda s' tisular tricúspidea 8 cm/s.
• Valvula tricuspide: insuficiencia tricuspidea moderada, velocidad de IT 3.8 m/s, gradiente de IT 58 mmHg.
• Valvula pulmonar: tiempo de aceleración pulmonar corto (TAP 75 ms), insuficiencia pulmonar con gradiente diastólico inicial de 25 mmHg, presión sistólica pulmonar estimada de 64 mmHg.
• Cava inferior: dilatada de 24 mm con colapso menor al 50%.

CONCLUSIONES:
1. Geometría normal del ventrículo izquierdo.
2. Dimensiones normales del ventrículo izquierdo y dilatación de cavidades derechas.
3. Función sistólica de ventrículo izquierdo conservada y disfunción sistólica longitudinal de ventrículo derecho.
4. Función diastólica normal del ventrículo izquierdo.
5. Insuficiencia tricúspidea moderada.
6. Alta probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Dilatación y disfunción sistólica del ventrículo derecho; alta probabilidad de hipertensión pulmonar.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_6_CONGENITA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: MARIA FERNANDA LOPEZ, 19 AÑOS, ASC 1.55 m2.
AI: Diámetro AI 32 mm.
AD: Área AD 22 cm2.
VI: DDVI 41 mm, SIV 8 mm, PP 8 mm, FEVI 65%.
VD: Diámetro basal 42 mm, TAPSE 22 mm, onda s' tisular 13 cm/s.
Septum Interauricular: Solución de continuidad tipo ostium secundum de 18 mm con flujo de izquierda a derecha por Doppler color, Qp/Qs 2.1.
Válvula Tricúspide: Insuficiencia tricuspidea leve, velocidad IT 2.8 m/s, Gradiente de IT 31 mmHg.
Válvula Pulmonar: PSAP estimada 36 mmHg.
Vena Cava Inferior: 17 mm, colapso >50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: MARIA FERNANDA LOPEZ
EDAD: 19 ANOS | ASC: 1.55 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: diámetro AI 32 mm.
• Auricula derecha: dilatada, área AD 22 cm2. Septo interauricular con solución de continuidad tipo ostium secundum de 18 mm de diámetro con cortocircuito de izquierda a derecha por Doppler color y relación de flujos Qp/Qs estimada en 2.1.
• Ventriculo izquierdo: geometría y dimensiones normales con DDVI 41 mm, SIV 8 mm, PP 8 mm; movilidad normal; función sistólica con fevi 65%.
• Ventriculo derecho: dilatado en su porción basal (42 mm); función sistólica longitudinal conservada con TAPSE 22 mm y onda s' tisular 13 cm/s.
• Valvula tricuspide: insuficiencia tricuspidea leve, velocidad de IT 2.8 m/s, gradiente de IT 31 mmHg.
• Valvula pulmonar: presión sistólica pulmonar estimada 36 mmHg.
• Cava inferior: 17 mm con colapso mayor al 50%.

CONCLUSIONES:
1. Geometría normal del ventrículo izquierdo.
2. Dimensiones normales de cavidades izquierdas con dilatación de cavidades derechas.
3. Función sistólica de ventrículo izquierdo conservada y función sistólica longitudinal de ventrículo derecho normal.
4. Función diastólica normal.
5. Comunicación interauricular tipo ostium secundum con cortocircuito de izquierda a derecha (Qp/Qs 2.1) e insuficiencia tricúspidea leve.
6. Probabilidad intermedia de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Comunicación interauricular tipo ostium secundum con cortocircuito de izquierda a derecha y dilatación de cavidades derechas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_7_PROTESIS = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: CARLOS MENDOZA RIOS, 68 AÑOS, ASC 1.88 m2.
AI: LAVI 41 mL/m2, diámetro AI 45 mm.
AD: Área AD 17 cm2.
VI: DDVI 50 mm, SIV 13 mm, PP 12 mm, masa indexada 132 gr/m2, FEVI 58%, Onda E 70 cm/s, Onda A 85 cm/s, E/e' 11.
VD: TAPSE 19 mm, onda s' tisular 11 cm/s.
Prótesis Aórtica: Biológica en posición aórtica, vel max Ao 2.6 m/s, gradiente máximo 27 mmHg, gradiente medio 14 mmHg, área por continuidad 1.4 cm2, DVI 0.38, sin fugas paravalvulares.
Válvula Mitral: Insuficiencia mitral leve.
Válvula Tricúspide: Velocidad IT 2.4 m/s, Gradiente de IT 23 mmHg.
Vena Cava Inferior: 18 mm, colapso >50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: CARLOS MENDOZA RIOS
EDAD: 68 ANOS | ASC: 1.88 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: dilatada, diámetro AI 45 mm, LAVI 41 mL/m2.
• Auricula derecha: área AD 17 cm2.
• Ventriculo izquierdo: geometría con hipertrofia concéntrica, diámetros normales con DDVI 50 mm, SIV 13 mm, PP 12 mm, masa indexada 132 gr/m2; movilidad global y segmentaria normal; función sistólica con fevi 58%; función diastólica con patrón de alteración de la relajación, E/e' 11.
• Ventriculo derecho: función sistólica longitudinal conservada con TAPSE 19 mm y onda s' tisular 11 cm/s.
• Valvula mitral: insuficiencia mitral leve.
• Valvula tricuspide: velocidad de IT 2.4 m/s, gradiente de IT 23 mmHg.
• Valvula aortica (Prótesis): prótesis biológica en posición aórtica, velocidad máxima 2.6 m/s, gradiente máximo 27 mmHg, gradiente medio 14 mmHg, área valvular por continuidad 1.4 cm2, índice de permeabilidad (DVI) 0.38; sin fugas paravalvulares.
• Cava inferior: 18 mm con colapso mayor al 50%.

CONCLUSIONES:
1. Hipertrofia concéntrica del ventrículo izquierdo.
2. Dimensiones de cavidades ventriculares normales con aurícula izquierda dilatada.
3. Función sistólica de ventrículo izquierdo conservada y función sistólica longitudinal de ventrículo derecho normal.
4. Disfunción diastólica tipo relajación lenta del ventrículo izquierdo.
5. Prótesis biológica aórtica e insuficiencia mitral leve.
6. Baja probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Prótesis biológica aórtica e insuficiencia mitral leve; hipertrofia concéntrica del ventrículo izquierdo con función sistólica conservada.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""
