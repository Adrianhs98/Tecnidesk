import os
import re

replacements = {
    # Backend
    r"gemini-3.7-flash": r"gemini-3.6-flash",
    r"Copiloto IA Técnico Libre": r"Ohm — Asistente IA Técnico Libre",
    r"Copiloto de taller": r"Ohm (Asistente de taller)",
    r"copiloto IA \(Gemini 3.7 Flash\)": r"Ohm (Gemini 3.6 Flash)",
    r"copiloto técnico experto": r"asistente Ohm, experto",
    r"respuesta del copiloto": r"respuesta de Ohm",
    r"Copiloto IA no disponible": r"Ohm no disponible",
    
    # Frontend AiChatBubble
    r"Copiloto IA Flotante": r"Ohm Flotante",
    r"Cerrar Copiloto IA": r"Cerrar Ohm",
    r"Abrir Copiloto IA": r"Abrir Ohm",
    r'"Copiloto \(\$': r'"Ohm ($',
    r'"Copiloto IA"': r'"Ohm"',
    
    # Frontend AiChatDrawer
    r"Copiloto IA de Taller\*\* \(Gemini 3.7 Flash\)": r"Ohm\*\* (Gemini 3.6 Flash)",
    r"Copiloto IA Técnico": r"Ohm",
    r"Copiloto IA de Taller": r"Ohm",
    r"Copiloto IA": r"Ohm",
    r"> Copiloto": r"> Ohm",
    r"Pregunta al Copiloto técnico": r"Pregúntale a Ohm",
    r"Enviar mensaje al copiloto": r"Enviar mensaje a Ohm",
    
    # Frontend TechnicianDashboard
    r"\[Copiloto IA\]": r"[Ohm]",
}

files_to_edit = [
    "backend/app/routers/diagnostic.py",
    "backend/app/services/correction_service.py",
    "backend/app/services/explanation_service.py",
    "backend/test_gemini.py",
    "frontend/src/features/technician/AiChatBubble.jsx",
    "frontend/src/features/technician/AiChatDrawer.jsx",
    "frontend/src/features/technician/TechnicianDashboard.jsx",
    "frontend/src/features/technician/TechnicianWorkModal.jsx",
    "frontend/src/tests/features/TechnicianPortal.test.jsx",
    "README.md"
]

for file_path in files_to_edit:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        for old, new in replacements.items():
            content = re.sub(old, new, content)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {file_path}")
    else:
        print(f"File not found: {file_path}")
