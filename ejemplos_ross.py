# Muestras reales y definitivas del Dr. Diego Ross Álvarez con orden estricto en conclusiones

EJEMPLO_NORMAL = """
DATOS DE ENTRADA:
Paciente: ZARATE MEDINA IRVING ARAY, 25 AÑOS, ASC 1.96 m2.

REPORTE ESPERADO:
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
• Valvula tricuspide: morfologia normal, sin válvulopatia, sin gradiente de llenado significativo, velocidad de IT 1.5 m/seg, gradiente 9 mmhg.
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

EJEMPLO_REMODELADO = """
DATOS DE ENTRADA:
Paciente: ALVARO DAMIAN CORREA, 34 AÑOS, ASC 2.1 m2.

REPORTE ESPERADO:
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
• Valvula tricuspide: morfologia normal, sin válvulopatia, sin gradiente de llenado significativo, velocidad de IT 1.4 m/seg, gradiente 8 mmhg.
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

EJEMPLO_FEVI_DEPRIMIDA = """
DATOS DE ENTRADA:
Paciente: HUGO MARTINEZ VALENCIA, 46 AÑOS, ASC 2.12 m2.

REPORTE ESPERADO:
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
• Valvula tricuspide: morfologia normal, sin datos de estenosis, velocidad de IT 2.29 m/s, gradiente sistólico VD-AD 21 mmHg.
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
