from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from service.database import get_db
from service.schemas import BezirkVersorgungResponse, LorPlanungsraumResponse
import os

router = APIRouter(tags=["kitas"])

@router.get("/api/v1/versorgung/bezirk/{bezirk_name}", response_model=BezirkVersorgungResponse)
def get_versorgung_bezirk(bezirk_name: str, db: Session = Depends(get_db)):
    agg_sql = text("""
        SELECT 
            bezirk_name,
            SUM(kinder_0_bis_6) AS gesamt_kinder_0_6,
            SUM(plaetze_ist) AS gesamt_plaetze_ist,
            ROUND((SUM(plaetze_ist)::numeric / NULLIF(SUM(kinder_0_bis_6), 0)) * 100, 2) AS versorgungsquote_prozent
        FROM lor_planungsraeume
        WHERE bezirk_name = :bezirk
        GROUP BY bezirk_name;
    """)
    agg = db.execute(agg_sql, {"bezirk": bezirk_name}).fetchone()
    if not agg:
        raise HTTPException(status_code=404, detail="Bezirk nicht gefunden")

    pl_sql = text("""
        SELECT plr_id, plr_name, bezirk_name, kinder_0_bis_6, plaetze_ist
        FROM lor_planungsraeume
        WHERE bezirk_name = :bezirk
    """)
    pl_rows = db.execute(pl_sql, {"bezirk": bezirk_name}).fetchall()

    return BezirkVersorgungResponse(
        bezirk_name=agg.bezirk_name,
        gesamt_kinder_0_6=int(agg.gesamt_kinder_0_6 or 0),
        gesamt_plaetze_ist=int(agg.gesamt_plaetze_ist or 0),
        versorgungsquote_prozent=float(agg.versorgungsquote_prozent) if agg.versorgungsquote_prozent is not None else None,
        planungsraeume=[LorPlanungsraumResponse.model_validate(r) for r in pl_rows]
    )

@router.get("/api/kitas")
def get_kitas(bezirk: str = None, db: Session = Depends(get_db)):
    try:
        if not bezirk or bezirk == "ALL":
            return []
            
        query = text("""
            SELECT k.name, k.traeger, k.plaetze, 
                   ST_Y(ST_Transform(k.geom, 4326)) AS latitude, 
                   ST_X(ST_Transform(k.geom, 4326)) AS longitude 
            FROM kitas k
            JOIN lor_planungsraeume l ON ST_Contains(l.geom, k.geom)
            WHERE l.bezirk_name = :bezirk;
        """)
        result = db.execute(query, {"bezirk": bezirk})
        data = [dict(row._mapping) for row in result]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/planungsraeume")
def get_planungsraeume(db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::json,
                        'properties', json_build_object(
                            'plr_id', plr_id,
                            'plr_name', plr_name,
                            'bezirk_name', bezirk_name,
                            'kinder_0_bis_6', kinder_0_bis_6,
                            'plaetze_ist', plaetze_ist,
                            'versorgungsquote', ROUND((plaetze_ist::numeric / NULLIF(kinder_0_bis_6, 0)) * 100, 1)
                        )
                    )
                ), '[]'::json)
            )::text as geojson
            FROM lor_planungsraeume;
        """)
        geojson_str = db.execute(query).scalar()
        if not geojson_str:
            return {"type": "FeatureCollection", "features": []}

        return Response(content=geojson_str.encode("utf-8"), media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/bezirke")
def get_bezirke(db: Session = Depends(get_db)):
    try:
        query = text("SELECT DISTINCT bezirk_name FROM lor_planungsraeume WHERE bezirk_name IS NOT NULL ORDER BY bezirk_name;")
        result = db.execute(query).scalars().all()
        return [{"label": b, "value": b} for b in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))