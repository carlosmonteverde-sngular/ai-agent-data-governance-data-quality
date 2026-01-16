from typing import Optional
from vertexai.generative_models import GenerativeModel

class DataQualityGenerator:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Generador de Reglas de Calidad (Data Quality) para Dataplex
        """
        self.model = GenerativeModel(model_name)

    def _build_prompt(self, technical_context: str) -> str:
        return f"""
        Eres un Data Quality Engineer experto en Google Cloud Dataplex.
        
        TU TAREA:
        Analiza los siguientes METADATOS TÉCNICOS de BigQuery y sugiere un conjunto de REGLAS DE CALIDAD DE DATOS (Data Quality Rules) para Dataplex AutoDQ.
        
        CONTEXTO TÉCNICO (Tablas y Columnas):
        -------------------------------------
        {technical_context}
        -------------------------------------

        REQUISITOS:
        1. Sugiere reglas coherentes con el tipo de dato y nombre de columna.
           - IDs -> Uniqueness, Not Null
           - Fechas -> Validity (no futuras, formato)
           - Emails/Códigos -> Regex patterns (escapa backslashes correctamente para JSON)
           - Categorías -> SqlAssertion o Set check
        2. Asigna una 'dimension' correcta (COMPLETENESS, ACCURACY, CONSISTENCY, VALIDITY, UNIQUENESS).
        3. Genera una descripción para cada regla.
        
        SALIDA ESPERADA (JSON ÚNICAMENTE):
        Una lista de reglas bajo la clave "rules", incluyendo la tabla a la que aplican.
        
        {{
            "rules": [
                {{
                    "table": "table_name",
                    "column": "patient_id",
                    "dimension": "UNIQUENESS",
                    "type": "UNIQUENESS",
                    "description": "Patient ID must be unique"
                }},
                {{
                    "table": "table_name",
                    "column": "email",
                    "dimension": "VALIDITY",
                    "type": "REGEX",
                    "description": "Email must be valid format",
                    "parameters": {{ "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" }}
                }}
            ]
        }}
        
        REGLAS:
        - Responde SOLO EL JSON VÁLIDO.
        """

    def suggest_quality_rules(self, technical_context: str) -> Optional[str]:
        """
        Genera reglas de calidad basadas en el contexto técnico proporcionado.
        """
        prompt = self._build_prompt(technical_context)
        print("🧠 Gemini analizando reglas de calidad...")
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                return response.text.replace("```json", "").replace("```", "").strip()
        except Exception as e:
            print(f"❌ Error generando reglas de calidad: {e}")
        
        return None
