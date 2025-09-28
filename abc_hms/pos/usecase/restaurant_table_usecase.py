
import json
from typing import List
import frappe
from frappe import _
from abc_hms.dto.pos_folio_dto import FolioItem, FolioListFilteredRequest, FolioUpsertRequest,  FolioWindowUpsertRequest
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from abc_hms.pos.repo.folio_repo import FolioRepo
from abc_hms.pos.repo.restaurant_table_repo import RestaurantTableRepo

class RestaurantTableUsecase:
    def __init__(self):
        self.repo = RestaurantTableRepo()

    def table_list(
        self,
        property :str,
    ):
        result = self.repo.table_list(property)
        for item in result:
            if item['tables']:
                item['tables'] = json.loads(item['tables'])
        return result


    def folio_find(self, folio: str):
        try:
            folio_data =  self.repo.folio_find(folio)
            if folio_data['windows']:
                folio_data['windows'] = json.loads(folio_data['windows'])
            return folio_data
        except json.JSONDecodeError as e:
            raise Exception(f"Error Decoding Response Body : {str(e)}")
        except Exception as e:
            raise e
    def folio_list_filtered(self, req: FolioListFilteredRequest) -> List[FolioItem]:
        try:
            return self.repo.folio_list_filtered(
                pos_profile=req['pos_profile'],
                docstatus=str(req['docstatus']) if req.get('docstatus') is not None else None,
                reservation=req.get('reservation'),
                guest=req.get('guest'),
                room=req.get('room'),
                arrival_from=req.get('arrival_from'),
                arrival_to=req.get('arrival_to'),
                departure_from=req.get('departure_from'),
                departure_to=req.get('departure_to')
            )
        except Exception as e:
            raise e
    def folio_window_upsert(self, req: FolioWindowUpsertRequest):
        try:
            return self.repo.folio_window_upsert(req["doc"], commit=req["commit"])
        except Exception as e:
            raise e
