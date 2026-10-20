# Matriz de entrenamiento definitiva (Few-Shot Learning con Criterio Clínico de Entrada y Salida)
# Dr. Diego Ross Álvarez - Estructura y Estilo Clínico Riguroso

EJEMPLO_1_NORMAL = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: ZARATE MEDINA IRVING ARAY, 25 AÑOS, ASC 1.96 m2.
DDVI: 42 mm, SIV: 10 mm, PP: 8 mm, VTD: 124 ml, VTS: 52 ml, Masa indexada: 71 gr/m2, GPR: 0.39.
FEVI (Simpson): 57%, TAPSE: 24 mm, Onda s' tricúspidea: 15 cm/s.
Onda E: 85 cm/s, Onda A: 59 cm/s, E/A: 1.4, TDA: 160 ms, E' lateral: 15 cm/s, E' medial: 12 cm/s, E/e': 5.
Válvula Aórtica: AVAo 3.3 cm2, Vel TSVI: 0.93 m/s, Vel Ao: 1.1 m/s.
Válvula Mitral: AVM 4.7 cm2, sin insuficiencia.
Válvula Tricúspide: Velocidad IT: 1.5 m/s, Gradiente de IT: 9 mmHg.
Vena Cava Inferior: 15 mm, colapso >60%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ZARATE MEDINA IRVING ARAY
EDAD: 25 ANOS | ASC: 1.96 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: geometría y patrón normal, tamaño normal, lavi 22 mL/m2, diámetro AI 37 mm, sin masas o trombos.
• Auricula derecha: geometría y patrón normal, tamaño normal, ravi 25 mL/m2, area 16.6 cm2, sin masas o trombos.
• Ventriculo izquierdo: geometría y patrón normal, diámetros de cavidades normales con DDVI 42 mm, SIV 10 mm, PP 8 mm, VTD 124 ml, VTS 52 ml, masa indexada 71 gr/m2, GPR 0.39; movilidad global y segmentaria normal; función sistólica con fevi simpson modificado 57%; función diastolica normal con onda E 85 cm/s, onda A 59 cm/s, E/A 1.4, TDA 160ms, TRIV 80ms, E tisular lateral 15 cm/s, E tisular medial 12 cm/s, E/e' 5.
• Ventriculo derecho: geometría y patrón normal, diámetros de cavidades normales de 38x25x74 mm; función sistólica global y longitudinal normal con onda s tisular tricuspidea 15 cm/s y CAFVD 45%.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, AVM por THP 4.7 cm2, sin gradiente significativo de llenado, sin insuficiencia.
• Valvula tricuspide: morfologia normal, sin válvulopatia, sin gradiente de llenado significativo, velocidad de IT 1.5 m/seg, gradiente de IT 9 mmhg.
• Valvula aortica: trivalva, morfologia normal, sin insuficiencia, sin gradiente de salida significativo. Avao por continuidad 3.3 cm2, vel TSVI 0.93 m/s, vel AO 1.1 m/s, raiz de tamaño normal, anillo 22 mm, SV 29 mm, UST 23 mm, AO asc 27 mm.
• Valvula pulmonar: sin insuficiencia ni gradiente significativo, Vel TSVD 70 cm/s, vel Pulmonar 95 cm/s, TSVD prox 24 mm, TAcp 140ms, presión sistólica pulmónar estimada 14 mmhg.
• Pericardio de aspecto normal. Sin masas o trombos. Cava 15 mm, colapso mas del 60%.

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
DDVI: 47 mm, SIV: 10 mm, PP: 11 mm, DSVI: 32 mm, VTD: 140 ml, VTS: 50 ml, Masa indexada: 109 gr/m2, GPR: 0.49.
FEVI (Simpson): 62%, TAPSE: N/D, Onda s' tricúspidea: 12.3 cm/s.
Onda E: 82 cm/s, Onda A: 52 cm/s, E/A: 1.5, TDA: 160 ms, E' lateral: 16 cm/s, E' medial: 15 cm/s, E/e': 5.
Válvula Aórtica: AVAo 3.2 cm2, Vel TSVI: 1 m/s, Vel Ao: 1.2 m/s.
Válvula Mitral: AVM 4.7 cm2, sin insuficiencia.
Válvula Tricúspide: Velocidad IT: 1.4 m/s, Gradiente de IT: 8 mmHg.
Vena Cava Inferior: 15 mm, colapso >60%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ALVARO DAMIAN CORREA
EDAD: 34 ANOS | ASC: 2.1 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: tamaño normal, lavi 30 mL/m2, diámetro AI 31 mm, sin masas o trombos.
• Auricula derecha: tamaño normal, ravi 28 mL/m2, area 18.3 cm2.
• Ventriculo izquierdo: geometría con remodelado concéntrico, diámetros con DDVI 47 mm, SIV 10 mm, PP 11 mm, DSVI 32 mm, VTD 140 ml, VTS 50 ml, masa indexada 109 gr/m2, GPR 0.49; movilidad global y segmentaria normal, no dilatado; función sistólica con fevi simpson modificado 62%; función diastolica normal con onda E 82 cm/s, onda A 52 cm/s, E/A 1.5, TDA 160ms, TRIV 90ms, E tisular lateral 16 cm/s, E tisular medial 15 cm/s, E/e' 5.
• Ventriculo derecho: levemente dilatado en la base, diametros 46x30x78 mm, funcion sistolica global y longitudinal normal, onda s tisular tricuspidea 12.3 cm/s, CAFVD 45%.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, AVM por THP 4.7 cm2, sin gradiente significativo de llenado, sin insuficiencia.
• Valvula tricuspide: morfologia normal, sin válvulopatia, sin gradiente de llenado significativo, velocidad de IT 1.4 m/seg, gradiente de IT 8 mmhg.
• Valvula aortica: sin insuficiencia, sin gradiente de salida significativo. Avao por continuidad 3.2 cm2, vel TSVI 1 m/s, vel AO 1.2 m/s, raiz de tamaño normal, anillo 22 mm, SV 37 mm, UST 33 mm, AO asc 29 mm.
• Valvula pulmonar: sin insuficiencia ni gradiente significativo, Vel TSVD 88 cm/s, vel Pulmonar 1.5 m/s, TSVD prox 27 mm, TAcp 180ms, presión sistólica pulmónar estimada 12 mmhg.
• Pericardio de aspecto normal. Sin masas o trombos. Cava 15 mm, colapso mas del 60%.

CONCLUSIONES:
1. Remodelado concéntrico del ventrículo izquierdo.
2. Dimensiones de cavidades normales (excepto dilatación basal leve de ventrículo derecho).
3. Función sistólica de ambos ventrículos normal.
4. Función diastólica normal.
5. Sin valvulopatías.
6. Baja probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Estudio ecocardiográfico con remodelado concéntrico ventricular izquierdo adaptativo; función sistólica y diastólica biventricular conservadas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_3_FEVI_DEPRIMIDA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: HUGO MARTINEZ VALENCIA, 46 AÑOS, ASC 2.12 m2.
DDVI: 55 mm, DSVI: 43 mm, SIV: 11 mm, PP: 11 mm, VTD: 176 ml, VTS: 134 ml, Masa indexada: 135.8 gr/m2, GPR: 0.39.
FEVI (Simpson Biplano): 24% (severamente deprimida), TAPSE: 16 mm, Onda s' tricúspidea: 6.7 cm/s.
Trastorno segmentario: Acinesia apical, discinesia anteroapical, inferoapical, septoapical, lateroapical, acinesia inferoseptal y anteroseptal.
Onda E: 84 cm/s, Onda A: 69 cm/s, E/A: 1.2, TDA: 130 ms, E' lateral: 7.9 cm/s, E' medial: 6.6 cm/s, E/e' medial: 12.7.
Válvula Aórtica: Apertura conservada, Vmax: 67 cm/s, Gradiente medio: 0.5 mmHg.
Válvula Mitral: AVM 5.6 cm2, gradiente medio 2.8 mmHg.
Válvula Tricúspide: Velocidad IT: 2.29 m/s, Gradiente de IT: 21 mmHg.
Vena Cava Inferior: 19 mm, colapso >50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: HUGO MARTINEZ VALENCIA
EDAD: 46 ANOS | ASC: 2.12 m²

Se realizo ecocardiograma transtoracico en reposo, ventana acústica aceptable, ritmo sinusal.

• Auricula izquierda: dilatada, diámetro AI 46 mm, área AI 21.3 cm².
• Auricula derecha: morfología y dimensiones normales, área AD 19.3 cm².
• Ventriculo izquierdo: geometría con hipertrofia excéntrica, diámetros dilatados con DDVI 55 mm, DSVI 43 mm, SIV 11 mm, PP 11 mm, VTD 176 ml, VTS 134 ml, masa indexada 135.8 gr/m2, GPR 0.39; trastorno segmentario de la contractilidad miocárdica caracterizado por acinesia apical, discinesia anteroapical, inferoapical, septoapical y lateroapical, adelgazamiento y acinesia inferoseptal medial y basal, acinesia anteroseptal basal y medial; función sistólica con fevi simpson biplano 24% (severamente deprimida); función diastólica con onda E 84 cm/s, onda A 69 cm/s, E/A 1.2, TDA 130 ms, E tisular lateral 7.9 cm/s, E tisular medial 6.6 cm/s, E/e' medial 12.7, E/e' lateral 10.6.
• Ventriculo derecho: dilatado en su porción basal (diámetro basal 40 mm); función sistólica longitudinal y global deprimida con Tapse 16 mm y onda s tisular tricúspidea 6.7 cm/s.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, AVM por THP 5.6 cm2, sin gradiente significativo de llenado, gradiente medio 2.8 mmHg.
• Valvula tricuspide: morfologia normal, sin datos de estenosis, velocidad de IT 2.29 m/s, gradiente de IT 21 mmHg.
• Valvula aortica: trivalva, apertura conservada, sin insuficiencia ni gradiente de salida significativo, Vmax 67 cm/s, gradiente medio 0.5 mmHg. Raíz aórtica: senos de Valsalva 35 mm, unión sinotubular 33 mm, aorta tubular 36 mm.
• Valvula pulmonar: TSVD Vmax 56 cm/s, gradiente medio 0.5 mmHg, sin gradiente de salida significativo, presión sistólica pulmonar estimada 26 mmHg.
• Pericardio de aspecto normal. Sin derrame pericárdico ni masas o trombos intracavitarios. Cava inferior 19 mm con colapso mayor al 50%.

CONCLUSIONES:
1. Hipertrofia excéntrica del ventrículo izquierdo.
2. Dilatación de cavidades izquierdas y porción basal de ventrículo derecho.
3. Función sistólica de ventrículo izquierdo severamente deprimida (FEVI 24%) y disfunción sistólica de ventrículo derecho.
4. Función diastólica normal en parámetros evaluados.
5. Sin valvulopatías significativas.
6. Baja probabilidad de hipertensión pulmonar en reposo.
7. Alteración severa de la motilidad segmentaria (acinesia/discinesia apical y antero/inferoseptal).

DIAGNOSTICO:
Estudio ecocardiográfico compatible con miocardiopatía dilatada con disfunción sistólica severa del ventrículo izquierdo y alteraciones severas de la contractilidad segmentaria.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_4_VALVULOPATIA = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: PATRICIA GOMEZ RUIZ, 62 AÑOS, ASC 1.68 m2.
DDVI: 48 mm, SIV: 12 mm, PP: 11 mm, FEVI: 55%.
Válvula Aórtica: Valva calcificada, apertura restrictiva. AVAo por continuidad: 0.8 cm2 (Estenosis aórtica severa), Vmax Ao: 4.2 m/s, Gradiente medio Ao: 45 mmHg.
Válvula Mitral: Calcificación del anillo mitral, insuficiencia mitral leve.
Válvula Tricúspide: Velocidad IT: 3.1 m/s, Gradiente de IT: 38 mmHg.
Vena Cava Inferior: 22 mm, colapso <50%.

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: PATRICIA GOMEZ RUIZ
EDAD: 62 ANOS | ASC: 1.68 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: dilatada, diámetro AI 44 mm, LAVI 38 mL/m2, sin masas o trombos.
• Auricula derecha: tamaño normal, área AD 18 cm2.
• Ventriculo izquierdo: geometría con hipertrofia concéntrica, diámetros normales con DDVI 48 mm, SIV 12 mm, PP 11 mm, masa indexada 125 gr/m2, GPR 0.52; movilidad global y segmentaria normal; función sistólica con fevi simpson modificado 55%; función diastólica con patrón de alteración de la relajación (onda E 65 cm/s, onda A 78 cm/s, E/A 0.8, TDA 220 ms, E' lateral 7 cm/s, E' medial 6 cm/s, E/e' 10).
• Ventriculo derecho: tamaño normal, TAPSE 20 mm, onda s' tisular tricúspidea 11 cm/s, CAFVD 42%.
• Valvula mitral: esclerosis y calcificación del anillo mitral, insuficiencia mitral leve, sin gradiente significativo de llenado.
• Valvula tricuspide: morfologia normal, velocidad de IT 3.1 m/s, gradiente de IT 38 mmHg.
• Valvula aortica: válvula trivalva con calcificación severa de cúspides y apertura restrictiva, estenosis aórtica severa con área valvular aórtica por continuidad de 0.8 cm2, velocidad máxima aórtica 4.2 m/s, gradiente medio aórtico de 45 mmHg, sin insuficiencia significativa. Raíz aórtica de dimensiones normales.
• Valvula pulmonar: sin alteraciones significativas, presión sistólica pulmonar estimada 43 mmHg.
• Pericardio de aspecto normal. Sin derrame pericárdico. Cava inferior 22 mm con colapso menor al 50%.

CONCLUSIONES:
1. Hipertrofia concéntrica del ventrículo izquierdo.
2. Dimensiones de cavidades ventriculares normales con aurícula izquierda dilatada.
3. Función sistólica de ambos ventrículos conservada.
4. Disfunción diastólica tipo relajación lenta del ventrículo izquierdo.
5. Estenosis aórtica severa e insuficiencia mitral leve.
6. Probabilidad moderada-alta de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Estudio ecocardiográfico compatible con estenosis aórtica severa calcificada; hipertrofia concéntrica del ventrículo izquierdo y función sistólica conservada; presiones pulmonares elevadas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""

EJEMPLO_5_HAP = """
--- DATOS DE ENTRADA (Métricas del Ecógrafo) ---
Paciente: ROBERTO HERNANDEZ PEREZ, 50 AÑOS, ASC 1.85 m2.
DDVI: 44 mm, SIV: 9 mm, PP: 9 mm, FEVI: 60%.
Ventrículo Derecho: Severamente dilatado en base (diámetro basal 48 mm), aplanamiento sistólico del septo interventricular.
TAPSE: 14 mm (disminuido), Onda s' tricúspidea: 8 cm/s, FACVD: 30%.
Válvula Tricúspide: Insuficiencia tricuspidea moderada, velocidad de IT: 3.8 m/s, Gradiente de IT: 58 mmHg.
Vena Cava Inferior: 24 mm, plétora cavas (colapso <50%).

--- REPORTE ESPERADO ---
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: ROBERTO HERNANDEZ PEREZ
EDAD: 50 ANOS | ASC: 1.85 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: tamaño normal, diámetro AI 34 mm, sin masas o trombos.
• Auricula derecha: significativamente dilatada, área AD 26 cm2, RAVI acorde.
• Ventriculo izquierdo: geometría normal, dimensiones normales con DDVI 44 mm, SIV 9 mm, PP 9 mm, masa indexada 82 gr/m2, GPR 0.41; aplanamiento sistólico del septo interventricular; movilidad global y segmentaria normal; función sistólica con fevi simpson modificado 60%; función diastólica normal.
• Ventriculo derecho: severamente dilatado en su porción basal (diámetro basal 48 mm, medio 36 mm, longitudinal 82 mm); función sistólica longitudinal y global deprimida con TAPSE 14 mm, onda s' tisular tricúspidea 8 cm/s y FACVD 30%.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, sin valvulopatía significativa.
• Valvula tricuspide: dilatación del anillo valvular, insuficiencia tricuspidea moderada, velocidad de IT 3.8 m/s, gradiente de IT 58 mmHg.
• Valvula aortica: trivalva, morfologia normal, sin insuficiencia ni gradiente de salida significativo.
• Valvula pulmonar: aceleración del flujo con muesca mesosistólica, tiempo de aceleración pulmonar corto (TAP 75 ms), insuficiencia pulmonar con gradiente diastólico inicial de 25 mmHg, presión sistólica pulmonar estimada de 64 mmHg.
• Pericardio de aspecto normal. Sin derrame pericárdico. Cava inferior dilatada de 24 mm con colapso menor al 50%.

CONCLUSIONES:
1. Geometría normal.
2. Dimensiones normales del ventrículo izquierdo y dilatación severa de cavidades derechas.
3. Función sistólica de ventrículo izquierdo conservada y disfunción sistólica de ventrículo derecho.
4. Función diastólica normal.
5. Insuficiencia tricúspidea moderada sin otras valvulopatías significativas.
6. Alta probabilidad de hipertensión pulmonar.
7. Sin alteraciones de la movilidad.

DIAGNOSTICO:
Estudio ecocardiográfico compatible con dilatación y disfunción sistólica severa del ventrículo derecho; signos ecocardiográficos de alta probabilidad de hipertensión pulmonar.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""
