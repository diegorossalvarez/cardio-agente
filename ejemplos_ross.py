# Pares de entrenamiento contextual (Few-Shot Learning) con el estilo real, seco y directo del Dr. Diego Ross Álvarez

EJEMPLO_NORMAL = """
DATOS DE ENTRADA:
Paciente: Usvaldo Javier Rivero Aguirre, 35 años, ASC 2.0 m2.
VTI, diámetros y flujos normales. Fevi 60%.

REPORTE ESPERADO:
DR. ROSS ALVAREZ CARDIOLOGIA
Reporte ecocardiograma transtoracico

PACIENTE: USVALDO JAVIER RIVERO AGUIRRE
EDAD: 35 ANOS | ASC: 2.0 m²

Se realizo ecocardiograma transtoracico en reposo, buena ventana, ritmo sinusal.

• Auricula izquierda: levemente dilatada, LAVI 39 mL/m2, diámetro AI 28 mm.
• Auricula derecha: tamaño normal, RAVI 28 mL/m2.
• Ventriculo izquierdo: masa indexada 152 gr/m2, GPR 0.54, movilidad global y segmentaria normal, no dilatado, DDVI 48 mm, SIV 13 mm, PP 12 mm, DSVI 32 mm, VTD 146 ml, VTS 58 ml, fevi simpson modificado 60%, función diastolica normal, onda E 89 cm/s, onda A 62 cm/s, E/A 1.4, TDA 130 ms, E tisular lateral 12 cm/s, E tisular medial 12 cm/s.
• Ventriculo derecho: levemente dilatado, diámetros 41x28x94 mm, función sistólica global y longitudinal normal, Tapse 30 mm, onda s tisular tricúspidea 12.8 cm/s, CAFVD 50%.
• Valvula mitral: aparato valvular y subvalvular de morfologia normal, AVM por THP 5.0 cm2, sin gradiente significativo de llenado, sin insuficiencia.
• Valvula tricuspide: morfologia normal, sin valvulopatia, sin gradiente de llenado significativo, velocidad de IT 2 m/s, gradiente 16 mmHg.
• Valvula aortica: sin insuficiencia, sin gradiente de salida significativo. AVAo por continuidad 3.7 cm2, diámetros de la raíz aórtica normal.
• Valvula pulmonar: TSVD prox distal 23 mm, prox 31 mm, TAP 150 ms, sin insuficiencia ni gradiente de salida significativo, presión sistólica pulmonar estimada 20 mmHg.
• Pericardio de aspecto normal. Sin masas o trombos. Cava 18 mm, colapso mas del 50%.

CONCLUSIONES:
1. Función sistólica de ambos ventrículos normal.
2. Función diastólica normal.
3. Sin valvulopatías.
4. Baja probabilidad de hipertensión pulmonar.
5. Hipertrofia miocárdica inducida por ejercicio.

DIAGNOSTICO:
Estudio ecocardiográfico con hipertrofia miocárdica adaptativa; función sistólica y diastólica conservadas.

DR ROSS ALVAREZ DIEGO
Cardiologo clinico | cedula 12883155 | avalado por la UNAM
Electrofisiologo egresado CMN 20 de noviembre
AV tormenta # 20, cp 24090 | 9812438407
"""
