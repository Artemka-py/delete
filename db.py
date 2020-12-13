import psycopg2
import config
from typing import Dict, List, Tuple

conn = psycopg2.connect(host=config.host, port=config.port, database=config.database, user=config.user,
                        password=config.password)
cur = conn.cursor()
print('Database connection open success')


def insert(table: str, column_values: Dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    cur.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def insert_single_value(table: str, field: str, value):
    cur.execute(
        f"INSERT INTO {table} "
        f"({field}) "
        f"VALUES ({value})"
    )
    conn.commit()


def fetchall(table: str, columns: List[str], where: str) -> List[Tuple]:
    columns_joined = ", ".join(columns)
    cur.execute(f"SELECT {columns_joined} FROM {table} {where}")
    rows = cur.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def fetchall_instructors(table: str, columns: List[str], where: str) -> List[Tuple]:
    columns_joined = ", ".join(columns)
    res = fetchall("orders_order", ["resort_id", "service_id"], "where finish = false and instructor_id IS NULL and "
                                                                "date_time > now()")
    for re in res:
        cur.execute(f"""select telegram_id from instructors_instructor ii
            left join instructors_instructor_resorts iir on ii.id = iir.instructor_id
            left join instructors_instructor_services iis on ii.id = iis.instructor_id
        where ii.approved = true and ii.reg_finish = true and iir.resort_id = {re["resort_id"]} and iis.service_id = {re["service_id"]}""")
    rows = cur.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def delete(table: str, row_id: int) -> None:
    row_id = int(row_id)
    cur.execute(f"delete from {table} where id={row_id}")
    conn.commit()


def get_cursor():
    return cur
