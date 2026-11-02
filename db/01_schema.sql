CREATE EXTENSION IF NOT EXISTS postgis;

-- LOR-Planungsräume (Stand ab 2021)
CREATE TABLE IF NOT EXISTS lor_planungsraeume (
    plr_id VARCHAR(8) PRIMARY KEY,      -- 8-stelliger LOR-Schlüssel
    plr_name VARCHAR(100) NOT NULL,
    bezirk_name VARCHAR(50) NOT NULL,
    kinder_0_bis_6 INT DEFAULT 0,
    plaetze_ist INT DEFAULT 0,
    geom GEOMETRY(MultiPolygon, 25833)  -- Metrisch in ETRS89 / UTM 33N
);

CREATE INDEX IF NOT EXISTS idx_lor_geom ON lor_planungsraeume USING GIST (geom);

-- Funktion zur dynamischen Grenzraum-Analyse
-- Input: lon/lat in EPSG:4326 (aus Web-UI), Wohneinheiten, Pufferdistanz in Metern
CREATE OR REPLACE FUNCTION fn_analyse_grenzraum(
    p_lon DOUBLE PRECISION,
    p_lat DOUBLE PRECISION,
    p_we INT,
    p_buffer_meter DOUBLE PRECISION DEFAULT 1000.0
)
RETURNS TABLE (
    plr_id VARCHAR(8),
    plr_name VARCHAR(100),
    bezirk_name VARCHAR(50),
    schnitt_flaeche_qm DOUBLE PRECISION,
    anteil_prozent NUMERIC(5,2),
    kinder_zuzug INT,
    plaetze_ist INT,
    auslastung_neu NUMERIC(5,2)
) AS $$
DECLARE
    v_pt_25833 GEOMETRY;
    v_buffer_geom GEOMETRY;
    v_kinder_gesamt INT;
    v_summe_schnittflaeche DOUBLE PRECISION;
BEGIN
    -- 1. Transformation von Web-Koordinaten (4326) in amtliches Metrik-System (25833)
    v_pt_25833 := ST_Transform(ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326), 25833);
    v_buffer_geom := ST_Buffer(v_pt_25833, p_buffer_meter);
    
    -- Bedarfsfaktor: 15 Kinder je 100 Wohneinheiten
    v_kinder_gesamt := ROUND(p_we * 0.15);

    -- 2. Gesamte Überschneidungsfläche berechnen (zur 100-%-Normierung)
    SELECT COALESCE(SUM(ST_Area(ST_Intersection(l.geom, v_buffer_geom))), 0)
    INTO v_summe_schnittflaeche
    FROM lor_planungsraeume l
    WHERE ST_Intersects(l.geom, v_buffer_geom);

    IF v_summe_schnittflaeche = 0 THEN
        RETURN;
    END IF;

    -- 3. Rückgabe mit exakter 100-%-Aufteilung und Plausibilisierung
    RETURN QUERY
    WITH schnitte AS (
        SELECT 
            l.plr_id,
            l.plr_name,
            l.bezirk_name,
            l.plaetze_ist,
            l.kinder_0_bis_6,
            ST_Area(ST_Intersection(l.geom, v_buffer_geom)) AS flaeche_qm
        FROM lor_planungsraeume l
        WHERE ST_Intersects(l.geom, v_buffer_geom)
    )
    SELECT 
        s.plr_id,
        s.plr_name,
        s.bezirk_name,
        s.flaeche_qm,
        ROUND(((s.flaeche_qm / v_summe_schnittflaeche) * 100)::numeric, 2) AS anteil_prozent,
        ROUND((v_kinder_gesamt * (s.flaeche_qm / v_summe_schnittflaeche)))::int AS kinder_zuzug,
        s.plaetze_ist,
        ROUND((((s.kinder_0_bis_6 + (v_kinder_gesamt * (s.flaeche_qm / v_summe_schnittflaeche))) / NULLIF(s.plaetze_ist, 0)) * 100)::numeric, 2) AS auslastung_neu
    FROM schnitte s
    ORDER BY s.flaeche_qm DESC;
END;
$$ LANGUAGE plpgsql;