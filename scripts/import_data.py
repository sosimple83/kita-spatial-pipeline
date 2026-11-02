import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# Umgebungsvariablen laden
BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER", "gis_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "streng_geheim_aendern")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "kitaplanung")

DEFAULT_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

DATA_DIR = BASE_DIR / "data"
KITALISTE_PATH = DATA_DIR / "kitaliste-nov-2025.xlsx"
EWR_PATH = DATA_DIR / "EWR_L21_202512E_Matrix.csv"

def main():
    print("🚀 Starte Import der amtlichen Daten...")
    engine = create_engine(DB_URI)

    # --- TEIL 1: KITALISTE (Stand November 2025) ---
    target_excel = KITALISTE_PATH if KITALISTE_PATH.exists() else Path("kitaliste-nov-2025.xlsx")
    if target_excel.exists():
        print(f"📥 Verarbeite {target_excel}...")
        df_kitas = pd.read_excel(target_excel)
        print("Spalten in Kitaliste:", df_kitas.columns.tolist())
    else:
        print(f"⚠️ Hinweis: {target_excel} nicht gefunden. Schritt übersprungen.")

    # --- TEIL 2: BEVÖLKERUNGSMATRIX (Stand 31.12.2025) ---
    target_ewr = EWR_PATH if EWR_PATH.exists() else Path("EWR_L21_202512E_Matrix.csv")
    if target_ewr.exists():
        print(f"📥 Verarbeite {target_ewr}...")
        df_ewr = pd.read_csv(target_ewr, sep=';', encoding='utf-8', low_memory=False)
        print("Spalten in EWR-Matrix:", df_ewr.columns.tolist()[:15])
    else:
        print(f"⚠️ Hinweis: {target_ewr} nicht gefunden. Schritt übersprungen.")

    print("✅ Daten-Skript bereit für die Ausführung gegen PostGIS.")

if __name__ == "__main__":
    main()