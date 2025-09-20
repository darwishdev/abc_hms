from typing import List
from abc_hms.dto.property_reservation_date_dto import ReservationDate
from utils.sql_utils import run_sql

class ReservationDateRepo:
    def reservation_date_sync(
            self,
            name: str,
            commit: bool
    )-> List[ReservationDate]:
        try:
            def procedure_call(cur , conn):
                cur.execute(
                    """
                    CALL reservation_date_sync(%s)
                    """,
                    (name)
                )

                if commit:
                    conn.commit()
                result : List[ReservationDate] = cur.fetchall()
                return result
            return run_sql(procedure_call)
        except Exception as e:
            raise e
