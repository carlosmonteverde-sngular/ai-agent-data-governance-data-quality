import os
import time
from google.cloud import bigquery
import vertexai
from core.github_client import GitHubClient
from modules.data_quality import DataQualityGenerator
from config.settings import config

# --- CONFIGURACIÓN TÉCNICA ---
PROJECT_ID = config.PROJECT_ID
LOCATION = config.LOCATION
TARGET_DATASET = config.DATASET_ID or "pharmaceutical_drugs" 

def get_context_from_bigquery(project_id: str, location: str, dataset_id: str) -> str:
    """
    Recupera el contexto de los metadatos de las tablas en BigQuery de un dataset específico.
    """
    client = bigquery.Client(project=project_id, location=location)
    context = ""
    
    try:
        print(f"DEBUG: Listando tablas en el dataset '{dataset_id}'...")
        
        try:
             tables = list(client.list_tables(dataset_id))
        except Exception as e:
            print(f"⚠️ Error accediendo al dataset {dataset_id}: {e}")
            return ""

        if not tables:
             print(f"⚠️ No se encontraron tablas en {dataset_id}.")
             return ""

        context += f"\nDataset: {dataset_id}\n"
        
        for table in tables:
            full_table = client.get_table(table)
            context += f"  Table: {full_table.table_id}\n"
            if full_table.description:
                context += f"    Description: {full_table.description}\n"
            
            context += "    Columns:\n"
            for schema_field in full_table.schema:
                desc_str = f" - Description: {schema_field.description}" if schema_field.description else ""
                context += f"      - {schema_field.name} ({schema_field.field_type}){desc_str}\n"

    except Exception as e:
        print(f"⚠️ Error recuperando metadatos de BigQuery: {e}")
        return ""

    return context.strip()

def main():
    print("🚀 Lanzando Agente de Calidad de Datos (Vertex AI + BigQuery Metadata)")

    # Inicialización
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    github_client = GitHubClient()

    # PASO 1: Búsqueda de contexto en BigQuery
    print(f"🔍 Recuperando metadatos de BigQuery para dataset '{TARGET_DATASET}'...")
    contexto_metadatos = get_context_from_bigquery(PROJECT_ID, LOCATION, TARGET_DATASET)

    if not contexto_metadatos:
        print("❌ No se pudo recuperar ningún contexto de metadatos de BigQuery.")
        return

    print(f"✅ Contexto recuperado.")

    # PASO 2: Generar Reglas de Calidad (JSON)
    dq_gen = DataQualityGenerator(model_name=config.MODEL_NAME)
    dq_json = dq_gen.suggest_quality_rules(contexto_metadatos)
    
    if dq_json:
        print("\nSugerencia generada (Reglas DQ):")
        print(dq_json)

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time())
        local_filename = f"{output_dir}/dq_rules_proposal_{timestamp}.json"
        
        with open(local_filename, "w", encoding="utf-8") as f:
            f.write(dq_json)
        
        print(f"\n✅ Propuesta guardada localmente en: {local_filename}")

        # --- STEP 3: GITHUB PR ---
        try:
            # Creando PR con la propuesta de reglas de calidad
            pr_url = github_client.create_proposal_pr(dq_json, "data_quality_rules")
            print(f"\n✅ Proceso completado. PR: {pr_url}")
        except Exception as e:
            print(f"❌ Error GitHub: {e}")

if __name__ == "__main__":
    main()