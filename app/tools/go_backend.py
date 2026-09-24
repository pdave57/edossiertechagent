import httpx
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoBackendClient:
    def __init__(self):
        self.base_url = settings.GO_BACKEND_URL
        self.timeout = settings.GO_BACKEND_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self._auth_token: Optional[str] = None
    
    def set_auth_token(self, token: str):
        self._auth_token = token
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers
    
    async def close(self):
        await self.client.aclose()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = await self.client.request(
                method, url, headers=headers, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        result = await self._request("POST", "/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        if "access_token" in result:
            self.set_auth_token(result["access_token"])
        return result
    
    async def get_me(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/auth/me")
    
    async def list_states(self) -> List[Dict[str, Any]]:
        return await self._request("GET", "/api/v1/states")
    
    async def get_state(self, state_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/states/{state_id}")
    
    async def list_zones(self, state_id: str) -> List[Dict[str, Any]]:
        return await self._request("GET", f"/api/v1/states/{state_id}/zones")
    
    async def list_lgas(self, state_id: str, zone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if zone_id:
            params["zone_id"] = zone_id
        return await self._request("GET", f"/api/v1/states/{state_id}/lgas", params=params)
    
    async def list_schools(
        self,
        state_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        lga_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if state_id:
            params["state_id"] = state_id
        if zone_id:
            params["zone_id"] = zone_id
        if lga_id:
            params["lga_id"] = lga_id
        return await self._request("GET", "/api/v1/schools", params=params)
    
    async def get_school(self, school_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/schools/{school_id}")
    
    async def list_personnel(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if school_id:
            params["school_id"] = school_id
        if state_id:
            params["state_id"] = state_id
        return await self._request("GET", "/api/v1/personnel", params=params)
    
    async def get_personnel(self, personnel_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/personnel/{personnel_id}")
    
    async def list_students(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if school_id:
            params["school_id"] = school_id
        if state_id:
            params["state_id"] = state_id
        return await self._request("GET", "/api/v1/students", params=params)
    
    async def get_student(self, student_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/students/{student_id}")
    
    async def get_enrollments(
        self,
        student_id: Optional[str] = None,
        school_id: Optional[str] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if student_id:
            params["student_id"] = student_id
        if school_id:
            params["school_id"] = school_id
        if session_id:
            params["session_id"] = session_id
        return await self._request("GET", "/api/v1/enrollments", params=params)
    
    async def get_sessions(
        self,
        school_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if school_id:
            params["school_id"] = school_id
        return await self._request("GET", "/api/v1/sessions", params=params)
    
    async def get_terms(
        self,
        session_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        return await self._request("GET", f"/api/v1/sessions/{session_id}/terms", params=params)
    
    async def get_results(
        self,
        student_id: Optional[str] = None,
        school_id: Optional[str] = None,
        session_id: Optional[str] = None,
        term_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if student_id:
            params["student_id"] = student_id
        if school_id:
            params["school_id"] = school_id
        if session_id:
            params["session_id"] = session_id
        if term_id:
            params["term_id"] = term_id
        return await self._request("GET", "/api/v1/results", params=params)
    
    async def get_report_cards(
        self,
        sub_level_id: str,
        session_id: str,
        term_id: str
    ) -> Dict[str, Any]:
        return await self._request("POST", "/api/v1/results/report-cards/generate", json={
            "sub_level_id": sub_level_id,
            "session_id": session_id,
            "term_id": term_id
        })
    
    async def get_recommendations(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/recommendations")
    
    async def get_zonal_summary(self, school_id: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if school_id:
            params["school_id"] = school_id
        return await self._request("GET", "/api/v1/reports/zonal/summary", params=params)
    
    async def get_gender_distribution(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/reports/gender/total")
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/reports/dashboard/stats")
    
    async def get_osc_data(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/reports/osc")
    
    async def get_attendance(
        self,
        school_id: Optional[str] = None,
        student_id: Optional[str] = None,
        personnel_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}
        if school_id:
            params["school_id"] = school_id
        if student_id:
            params["student_id"] = student_id
        if personnel_id:
            params["personnel_id"] = personnel_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return await self._request("GET", "/api/v1/attendance", params=params)


go_backend_client = GoBackendClient()