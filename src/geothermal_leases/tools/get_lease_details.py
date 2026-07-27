import httpx

from ._blm import BASE_URL, ts_to_date as _ts_to_date


def register(mcp):

    @mcp.tool()
    async def get_lease_details(case_number: str) -> dict:
        """
        Retrieve details for a BLM geothermal lease by its Case Serial Number.

        Args:
            case_number: The BLM case serial number, e.g. 'NVNV105806473'

        Returns:
            A dict with lease details, or an error message if not found.
        """
        params = {
            "where": f"CSE_NR='{case_number}'",
            "outFields": "*",
            "f": "json",
            "resultRecordCount": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": (
                    f"BLM service returned HTTP {exc.response.status_code} "
                    f"for case number '{case_number}'"
                )
            }
        except httpx.HTTPError as exc:
            return {"error": f"Request to BLM service failed: {exc}"}

        try:
            data = resp.json()
        except ValueError:
            return {"error": "BLM service returned a non-JSON response"}

        # ArcGIS returns HTTP 200 with an "error" object for bad queries
        if "error" in data:
            svc_err = data["error"]
            return {
                "error": (
                    f"BLM service error {svc_err.get('code')}: "
                    f"{svc_err.get('message')}"
                )
            }

        features = data.get("features", [])
        if not features:
            return {"error": f"No lease found for case number '{case_number}'"}

        attrs = features[0]["attributes"]
        geometry = features[0].get("geometry")  # polygon boundary if requested

        return {
            "case_serial_number": attrs.get("CSE_NR"),
            "case_name": attrs.get("CSE_NAME") or None,
            "lease_type": attrs.get("BLM_PROD"),
            "status": attrs.get("CSE_DISP"),
            "state": attrs.get("ADMIN_STATE"),
            "acreage": attrs.get("RCRD_ACRS"),
            "commodity": attrs.get("CMMDTY"),
            "formation": attrs.get("FRMTN"),
            "production_status": attrs.get("PRDCNG"),
            "effective_date": _ts_to_date(attrs.get("EFF_DT")),
            "expiration_date": _ts_to_date(attrs.get("EXP_DT")),
            "sale_date": _ts_to_date(attrs.get("SALE_DT")),
            "data_source": attrs.get("SRC"),
            "last_modified": _ts_to_date(attrs.get("Modified")),
        }