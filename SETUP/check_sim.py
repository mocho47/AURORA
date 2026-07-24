from pathlib import Path

triggers_simulado = ['SIMULADO', 'PENDIENTE = True', 'Template response',
                     'def solution():\n    pass', '$XXX', 'PLACEHOLDER']
triggers_real = ['AsyncGroq', 'groq.chat.completions.create', 'motor_origen']

for f in sorted(Path('MOTORES').glob('motor_*.py')):
    content = open(f, encoding='utf-8').read()
    simulado = [t for t in triggers_simulado if t in content]
    reales   = [t for t in triggers_real if t in content]
    tiene_singleton = 'motor = Motor' in content
    estado = 'REAL' if (reales and not simulado and tiene_singleton) else 'REVISAR'
    print(f"{estado}  {f.name}")
    if simulado:
        print(f"       FALSO: {simulado}")
