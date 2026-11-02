from pydantic import BaseModel
from typing import List, Optional

class LorPlanungsraumResponse(BaseModel):
    plr_id: str
    plr_name: str
    bezirk_name: str
    kinder_0_bis_6: int
    plaetze_ist: int

    class Config:
        from_attributes = True

class BezirkVersorgungResponse(BaseModel):
    bezirk_name: str
    gesamt_kinder_0_6: int
    gesamt_plaetze_ist: int
    versorgungsquote_prozent: Optional[float] = None
    planungsraeume: List[LorPlanungsraumResponse]

class GrenzraumAnalyseItem(BaseModel):
    plr_id: str
    plr_name: str
    bezirk_name: str
    schnitt_flaeche_qm: float
    anteil_prozent: float
    kinder_zuzug: int
    plaetze_ist: int
    auslastung_neu: Optional[float] = None