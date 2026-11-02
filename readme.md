# 📍 Kommunale Kita-Bedarfs- & Versorgungsanalyse (§ 80 SGB VIII)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4-green?logo=postgis)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

Automatisierte End-to-End-Geodateninfrastruktur zur kleinräumigen Ermittlung von Kita-Bedarfen und Betreuungsquoten in kommunalen Planungsräumen (Lebensweltlich orientierte Räume / LOR Berlin).

Ersetzt manuelle Tabellen-Verschneidungen und fehleranfällige Excel-Abgleiche durch automatisierte OGC-Pipelines, performante PostGIS-Routinen und interaktive Fach-Dashboards.

---

## 🎯 Fachlicher Hintergrund (Use Case)

Kommunale Träger der öffentlichen Jugendhilfe sind nach **§ 80 SGB VIII** gesetzlich verpflichtet, eine vorausschauende Bedarfs- und Einrichtungsplanung vorzuhalten. In der Verwaltungspraxis führt dies häufig zu Medienbrüchen und erheblichem personellem Aufwand:

* **Amtliche Geometrien:** Lebensweltlich orientierte Räume (LOR-Planungsräume, Bezirksregionen) liegen als OGC-Dienste oder Vektordaten vor.
* **Einrichtungsbestände:** Kindertagesstätten, Trägerstrukturen und Platzkapazitäten werden über amtliche WFS-Dienste (GDI Berlin) oder Tabellen gepflegt.
* **Bevölkerungsdaten:** Alterskohorten (0 bis unter 6 Jahre) stammen aus periodischen Einwohnerregister-Matrizen (EWR).

**Ziel dieser Lösung:** Vollständige Beseitigung manueller Klickarbeit durch automatisierte räumliche Verschneidung (`ST_Contains`), konsistente Datenhaltung in PostGIS und Bereitstellung einer performanten REST-API für Auswertungen und Dashboards.

---

## 🏛 Systemarchitektur

```
┌────────────────────────────────────────────────────────┐
│                   Amtliche Datenquellen                │
│  • GDI Berlin WFS (Kitas & Einrichtungen)              │
│  • Amtliche LOR-Geometrien (Planungsräume EPSG:25833)  │
│  • Open Data Berlin (EWR-Bevölkerungsstatistiken)      │
└───────────────────────────┬────────────────────────────┘
                            │ (Automatisierte ETL-Pipelines)
                            ▼
┌────────────────────────────────────────────────────────┐
│             PostgreSQL 16 + PostGIS 3.4                │
│  • Geometrie-Validierung & Räumliche Indizes (GiST)    │
│  • Räumliche Verschneidung (ST_Contains, ST_Transform) │
│  • Vorberechnete Views für Betreuungsquoten & Defizite │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     FastAPI Backend       │ │    Appsmith Low-Code      │
│ • OpenAPI / Swagger Doku  │ │ • Interaktives Dashboard  │
│ • Performante GeoJSON API │ │ • Filtern nach Bezirk/LOR │
│ • Statistische Metriken   │ │ • Exportfähige Tabellen   │
└───────────────────────────┘ └───────────────────────────┘
```

---

## 🛠 Tech-Stack

* **Storage & Spatial Core:** PostgreSQL 16 + PostGIS 3.4 (Räumliche Indizes via GiST, Topologie-Prüfungen)
* **ETL & Data Processing:** Python 3.12+, GeoPandas, Shapely, SQLAlchemy 2.0, Requests
* **Backend Services:** FastAPI, Pydantic v2, Uvicorn
* **Orchestrierung:** Docker & Docker Compose
* **Frontend / Dashboarding:** Appsmith CE (alternativ QGIS Desktop / WebGIS-Clients)

---

## 📂 Projektstruktur

```text
├── .env.example              # Vorlage für Umgebungsvariablen
├── .gitignore                # Ausschluss von Rohdaten, Dumps & Credentials
├── docker-compose.yml        # Multi-Container-Setup (PostGIS, FastAPI, Appsmith)
├── README.md                 # Projektdokumentation
├── requirements.txt          # Python-Abhängigkeiten
├── 01_schema.sql             # Datenbankschema & Tabellendefinitionen
├── check_db.py               # Diagnoseskript für Datenbankverbindung
├── data/                     # Lokaler Rohdaten-Speicher (via .gitignore ignoriert)
│   ├── Planungsraum.json
│   ├── kitas.geojson
│   ├── kitaliste-nov-2025.xlsx
│   └── EWR_L21_202512E_Matrix.csv
├── scripts/                  # ETL- & Migrations-Pipelines
│   ├── import_planungsraeume.py
│   ├── import_wfs_kitas.py
│   └── import_data.py
└── service/                  # FastAPI Microservice
    ├── Dockerfile
    ├── main.py
    └── database.py
```

---

## 🚀 Quickstart & Lokales Setup

### 1. Repository klonen & Konfiguration anlegen

```bash
git clone https://github.com/sosimple83/kita-spatial-pipeline.git
cd kita-spatial-pipeline

# Konfigurationsdatei aus Vorlage erzeugen
cp .env.example .env
```

Passe bei Bedarf die Verbindungsparameter in der `.env` an:

```dotenv
POSTGRES_DB=kitaplanung
POSTGRES_USER=gis_admin
POSTGRES_PASSWORD=streng_geheim_aendern
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
API_PORT=8000
APPSMITH_PORT=8080
```

### 2. Container-Infrastruktur starten

```bash
docker compose up -d --build
```

Dienste sind erreichbar unter:
* **FastAPI Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Appsmith UI:** [http://localhost:8080](http://localhost:8080)
* **PostgreSQL / PostGIS:** `localhost:5433` (User: `gis_admin`, DB: `kitaplanung`)

### 3. Geodaten & amtliche Register laden

Führe die ETL-Skripte lokal aus (oder binde sie in periodische Cron-/Orchestrierungs-Jobs ein):

```bash
# Virtuelle Python-Umgebung einrichten
python3 -m venv .venv
source .venv/bin/activate  # Unter Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. LOR-Planungsräume transformieren (EPSG:25833) & nach PostGIS laden
python scripts/import_planungsraeume.py

# 2. Amtlichen WFS der Kita-Standorte (GDI Berlin) synchronisieren
python scripts/import_wfs_kitas.py

# 3. Kitaliste & EWR-Bevölkerungsmatrix verarbeiten
python scripts/import_data.py
```

---

## 📊 API-Spezifikation (Auszug)

| Methode | Endpunkt | Beschreibung |
| :--- | :--- | :--- |
| `GET` | `/api/v1/planungsraeume` | Liefert Planungsräume als GeoJSON FeatureCollection inkl. aggregierter Platzzahlen. |
| `GET` | `/api/v1/kitas` | Liefert Kita-Standorte (filterbar nach LOR-Schlüssel `plr_id` oder Bezirk). |
| `GET` | `/api/v1/stats/versorgung` | Berechnet Versorgungsquoten (Plätze vs. Altersgruppe 0 bis <6 Jahre) pro Planungsraum. |
| `GET` | `/health` | Status-Prüfung für Container-Monitoring und Orchestrierung. |

---

## 🔒 IT-Sicherheit & Datenschutz

* **Keine Speicherung personenbezogener Daten:** Die Plattform verarbeitet ausschließlich aggregierte statistische Daten auf Planungsraumebene (LOR).
* **OGC- & BSI-Konformität:** Standardisierte Schnittstellen (OGC API Features / WFS), offene Vektorformate und containerisierte Isolation.
* **Kein Vendor-Lock-in:** 100 % quelloffener Stack (FOSSGIS) nach den Grundsätzen von *Public Money, Public Code*.

---

## 👤 Kontakt & Engineering

**Philip Emmanuel Tobey**  
*GIS Solution Architect & Python Developer*  
*Spezialisiert auf Geodaten-Pipelines, PostGIS-Architektur und kommunale Fachverfahren.*

* **Website:** [qgis-profi.de](https://qgis-profi.de) / [tobeygis.de](https://tobeygis.de)
* **LinkedIn:** [linkedin.com/in/philip-emmanuel-tobey](https://www.linkedin.com/in/philip-emmanuel-tobey/)
* **GitHub:** [@sosimple83](https://github.com/sosimple83)
* **E-Mail:** info@tobeygis.de
