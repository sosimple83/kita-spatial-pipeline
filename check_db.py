from service.database import engine
with engine.connect() as conn:
    res = conn.exec_driver_sql("SELECT table_name, column_name FROM information_schema.columns WHERE table_name IN ('berlin_planungsraeume', 'kitas')").fetchall()
    for r in res: print(r)
