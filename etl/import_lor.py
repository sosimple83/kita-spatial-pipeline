import os
import csv
import psycopg2

def run_import(csv_path: str = None):
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "kitaplanung")
    db_user = os.getenv("POSTGRES_USER", "gis_admin")
    db_pass = os.getenv("POSTGRES_PASSWORD", "geosecret2026")
    
    conn = psycopg2.connect(f"dbname={db_name} user={db_user} password={db_pass} host={db_host} port={db_port}")
    cur = conn.cursor()

    cur.execute("""
        UPDATE lor_planungsraeume
        SET 
            bezirk_name = CASE 
                WHEN LEFT(plr_id, 2) = '01' THEN 'Mitte'
                WHEN LEFT(plr_id, 2) = '02' THEN 'Friedrichshain-Kreuzberg'
                ELSE 'Berlin' 
            END,
            plr_name = COALESCE(plr_name, 'LOR ' || plr_id)
        WHERE bezirk_name IS NULL OR bezirk_name = '';
    """)

    if csv_path and os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    UPDATE lor_planungsraeume
                    SET kinder_0_bis_6 = %s,
                        plaetze_ist = %s
                    WHERE plr_id = %s;
                """, (int(row["kinder_0_6"]), int(row["plaetze_ist"]), row["plr_id"]))
        print(f"CSV-Demografie aus {csv_path} eingepflegt.")
    else:
        cur.execute("""
            UPDATE lor_planungsraeume
            SET kinder_0_bis_6 = 150,
                plaetze_ist = 120
            WHERE bezirk_name = 'Mitte' AND (kinder_0_bis_6 = 0 OR kinder_0_bis_6 IS NULL);
        """)
        print("Mitte-Basiswerte (150 Kinder / 120 Plätze = 80%) gesetzt.")

    conn.commit()
    cur.close()
    conn.close()
    print("ETL-Durchlauf erfolgreich abgeschlossen.")

if __name__ == "__main__":
    run_import()