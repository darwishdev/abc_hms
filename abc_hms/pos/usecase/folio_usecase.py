
import json
from typing import List
import frappe
from frappe import _
from abc_hms.dto.pos_folio_dto import FolioInsertRequest , FolioItem, FolioListFilteredRequest, FolioMergeRequest, FolioUpsertRequest,  FolioWindowUpsertRequest
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from abc_hms.pos.repo.folio_repo import FolioRepo

class FolioUsecase:
    def __init__(self):
        self.repo = FolioRepo()


    def folio_insert(
        self,
        payload :FolioInsertRequest,
    ):
        try:
            return self.repo.folio_insert(payload)
        except frappe.ValidationError as e:
            raise e

        except Exception as e:
            raise e
    def folio_upsert(
        self,
        payload :FolioUpsertRequest,
    ):
        try:
            return self.repo.folio_upsert(payload.get("doc") , payload.get("commit"))
        except frappe.ValidationError as e:
            raise e

        except Exception as e:
            raise e


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

    def folio_merge(self, req: FolioMergeRequest):
        try:
            return self.repo.folio_merge(req["source_folio"],req["destination_folio"] ,req["destination_window"])
        except Exception as e:
            raise e

