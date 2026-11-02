import os
from pathlib import Path
from dotenv import load_dotenv
import geopandas as gpd
from sqlalchemy import create_engine

# Umgebungsvariablen laden
BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER", "gis_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "streng_geheim_aendern")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "kitaplanung")

DEFAULT_DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

WFS_URL = "WFS:https://gdi.berlin.de/services/wfs/kita?service=WFS&version=1.1.0&request=GetCapabilities"
LAYER_NAME = "kita:kita"
GEOJSON_PATH = BASE_DIR / "data" / "kitas.geojson"


def main():
    print("🚀 Hole amtlichen WFS-Stream (GDI Berlin)...")
    gdf = gpd.read_file(WFS_URL, layer=LAYER_NAME)
    print(f"📦 Geladen: {len(gdf)} Features.")

    # 1. CRS erzwingen (EPSG:25833 UTM 33N)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:25833")
    elif gdf.crs.to_epsg() != 25833:
        gdf = gdf.to_crs("EPSG:25833")

    # 2. Schema-Mapping & Geometrie-Standardisierung
    clean_gdf = (
        gdf.rename(
            columns={'e_name': 'name', 't_name': 'traeger', 'e_platz': 'plaetze'}
        )
        .rename_geometry('geom')
    )

    cols = ['name', 'traeger', 'plaetze', 'geom']
    clean_gdf = clean_gdf[[c for c in cols if c in clean_gdf.columns]]

    # 3. Sicherheits-Backup als GeoJSON (ignoriert in .gitignore)
    GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_gdf.to_file(GEOJSON_PATH, driver="GeoJSON")
    print(f"💾 Lokal gedumpt: {GEOJSON_PATH}")

    # 4. Bulk-Insert PostGIS
    print("🐘 Schreibe nach PostgreSQL/PostGIS (kitaplanung)...")
    engine = create_engine(DB_URL)
    clean_gdf.to_postgis('kitas', engine, if_exists='replace', index=False)
    print(f"✅ Stark. [{len(clean_gdf)}] Kitas persistent in DB.")


if __name__ == "__main__":
    main()