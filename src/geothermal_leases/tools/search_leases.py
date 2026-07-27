import httpx

from ._blm import BASE_URL, ts_to_date as _ts_to_date, to_arcgis_timestamp

# Fields requested for each result (lighter payload than "*")
_SUMMARY_FIELDS = "CSE_NR,CSE_NAME,CSE_DISP,ADMIN_STATE,RCRD_ACRS,EFF_DT,EXP_DT"

# Cap on records returned per search
_MAX_RECORDS = 50


def register(mcp):

    @mcp.tool()
    async def search_leases(
        state: str | None = None,
        status: str | None = None,
        effective_date_from: str | None = None,
        effective_date_to: str | None = None,
        expiration_date_from: str | None = None,
        expiration_date_to: str | None = None,
    ) -> dict:
        """
        Search BLM geothermal leases, optionally filtering by state, status,
        and effective-/expiration-date ranges.

        All parameters are optional. If none is provided, all leases are
        returned (capped at 50 records).

        Args:
            state: Two-letter admin state code, e.g. 'NV' (matches ADMIN_STATE).
            status: Case disposition/status, e.g. 'Authorized' (matches CSE_DISP).
            effective_date_from: Inclusive lower bound on effective date,
                as an ISO date string 'YYYY-MM-DD' (matches EFF_DT).
            effective_date_to: Inclusive upper bound on effective date,
                as an ISO date string 'YYYY-MM-DD' (matches EFF_DT).
            expiration_date_from: Inclusive lower bound on expiration date,
                as an ISO date string 'YYYY-MM-DD' (matches EXP_DT).
            expiration_date_to: Inclusive upper bound on expiration date,
                as an ISO date string 'YYYY-MM-DD' (matches EXP_DT).

        Returns:
            A dict of the form:
            {"count": <int>, "leases": [ {lease summary}, ... ]}
            or an error message if the request fails.
        """
        clauses: list[str] = []
        if state:
            clauses.append(f"ADMIN_STATE='{state.upper()}'")
        if status:
            clauses.append(f"CSE_DISP='{status}'")
        try:
            if effective_date_from:
                clauses.append(f"EFF_DT >= {to_arcgis_timestamp(effective_date_from)}")
            if effective_date_to:
                clauses.append(f"EFF_DT <= {to_arcgis_timestamp(effective_date_to)}")
            if expiration_date_from:
                clauses.append(f"EXP_DT >= {to_arcgis_timestamp(expiration_date_from)}")
            if expiration_date_to:
                clauses.append(f"EXP_DT <= {to_arcgis_timestamp(expiration_date_to)}")
        except ValueError:
            return {
                "error": (
                    "date filters must be ISO dates in 'YYYY-MM-DD' format"
                )
            }
        where = " AND ".join(clauses) if clauses else "1=1"

        params = {
            "where": where,
            "outFields": _SUMMARY_FIELDS,
            "f": "json",
            "returnGeometry": "false",
            "resultRecordCount": _MAX_RECORDS,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": (
                    f"BLM service returned HTTP {exc.response.status_code} "
                    f"for search (state={state!r}, status={status!r})"
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
        leases = [
            {
                "case_serial_number": a.get("CSE_NR"),
                "case_name": a.get("CSE_NAME") or None,
                "status": a.get("CSE_DISP"),
                "state": a.get("ADMIN_STATE"),
                "acreage": a.get("RCRD_ACRS"),
                "effective_date": _ts_to_date(a.get("EFF_DT")),
                "expiration_date": _ts_to_date(a.get("EXP_DT")),
            }
            for f in features
            for a in [f.get("attributes", {})]
        ]

        return {"count": len(leases), "leases": leases}
