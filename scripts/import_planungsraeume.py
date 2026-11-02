import os
from pathlib import Path
from dotenv import load_dotenv
import geopandas as gpd
from shapely.geometry import MultiPolygon
from sqlalchemy import create_engine

# Umgebungsvariablen laden (.env aus Root)
BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER", "gis_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "streng_geheim_aendern")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "kitaplanung")

DEFAULT_DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

FILE_PATH = BASE_DIR / "data" / "Planungsraum.json"
TABLE_NAME = "berlin_planungsraeume"


def main():
    print(f"🚀 Lese Planungsräume aus: {FILE_PATH}...")
    if not FILE_PATH.exists():
        # Fallback falls direkt im Ordner
        alt_path = Path(__file__).resolve().parent / "Planungsraum.json"
        if alt_path.exists():
            target_path = alt_path
        else:
            raise FileNotFoundError(f"Datei nicht gefunden: {FILE_PATH} oder {alt_path}")
    else:
        target_path = FILE_PATH

    gdf = gpd.read_file(target_path)
    print(f"📦 Geladen: {len(gdf)} Features.")

    # 1. Spalten-Mapping & LOR-Systematik ableiten
    if "SCHLUESSEL" in gdf.columns:
        gdf.rename(columns={"SCHLUESSEL": "plr_id"}, inplace=True)

    gdf["bezirk_code"] = gdf["plr_id"].astype(str).str[:2]
    gdf["bzr_code"] = gdf["plr_id"].astype(str).str[:4]

    # 2. Geometrie standardisieren: Alles sauber auf MultiPolygon zwingen
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: MultiPolygon([g]) if g is not None and g.geom_type == "Polygon" else g
    )
    gdf = gdf.set_geometry("geometry").rename_geometry("geom")

    # 3. CRS-Handling & Transformation nach UTM Zone 33N
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    if gdf.crs.to_epsg() != 25833:
        gdf = gdf.to_crs(epsg=25833)

    # 4. Spalten selektieren
    cols = ["plr_id", "bezirk_code", "bzr_code", "geom"]
    clean_gdf = gdf[[c for c in cols if c in gdf.columns]]

    # 5. Bulk-Insert nach PostGIS
    print(f"🐘 Schreibe {len(clean_gdf)} Planungsräume nach PostGIS ({TABLE_NAME})...")
    engine = create_engine(DB_URL)
    
    clean_gdf.to_postgis(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False
    )
    print(f"✅ Stark. Tabelle '{TABLE_NAME}' erfolgreich in DB geschrieben.")


if __name__ == "__main__":
    main()