import httpx
from typing import Any
from app.config import settings

def create_ezrentout_client() -> httpx.Client:
    return httpx.Client(
        base_url=settings.ez_rentout_base_url,
        timeout=20.0,
        headers={
            "Authorization": f"Bearer {settings.ez_rentout_token}",
            "Accept": "application/json",
            },
        )

class EzRentOutEndpoint:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def get_rented_out_assets_page(self, page: int = 1) -> dict[str, Any]:
        response = self.client.get(
            "/assets/filter.api",
            params={"status": "checked_out", "page": page},
        )
        response.raise_for_status()
        return response.json()

    def get_all_rented_out_assets(self) -> list[dict]:
        first_page = self.get_rented_out_assets_page(1)

        total_pages = first_page["total_pages"]
        all_assets = first_page["assets"]

        for page in range(2, total_pages + 1):
            data = self.get_rented_out_assets_page(page)
            all_assets.extend(data["assets"])

        return all_assets

    def get_asset_history_page(self, asset_id: str, page: int = 1) -> dict[str, Any]:
        response = self.client.get(
            f"assets/{asset_id}/history_paginate.api",
            params={"page": page},
        )
        response.raise_for_status()
        return response.json()

    def get_custom_fields_info(self) -> dict[str, list]:
        response = self.client.get("/assets/custom_attributes.api")
        response.raise_for_status()
        return response.json()

    def get_custom_field_history(self, asset_id: str, attribute_id: str) -> dict[str, list]:
        response = self.client.get(
            f"/assets/{asset_id}/custom_attribute_history.api",
            params={"custom_attribute_id": attribute_id},
        )
        response.raise_for_status()
        return response.json()

    def export_custom_report(self):
        response = self.client.post(
            "/reports/custom_report.api",
            data="report_id=707267"
        )
        response.raise_for_status()
        return response.json()

    def list_background_jobs(self):
        response = self.client.get(
            "/background_jobs.api"
        )
        response.raise_for_status()
        return response.json()

    def get_backgroud_job_details(self, job_id):
        response = self.client.get(
            f"/background_jobs/{job_id}.api"
        )
        return response.json()
