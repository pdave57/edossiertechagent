from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Dict, Any
import json
import logging

from app.tools.go_backend import go_backend_client

logger = logging.getLogger(__name__)


class HealthCheckTool(BaseTool):
    name: str = "health_check"
    description: str = "Check the health status of the e-Dossier Go backend API"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.health_check())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.health_check()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class LoginTool(BaseTool):
    name: str = "login"
    description: str = "Authenticate with the e-Dossier backend using email and password"
    
    class InputSchema(BaseModel):
        email: str = Field(description="User email address")
        password: str = Field(description="User password")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(self, email: str, password: str) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.login(email, password))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, email: str, password: str) -> str:
        try:
            result = await go_backend_client.login(email, password)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class ListStatesTool(BaseTool):
    name: str = "list_states"
    description: str = "List all states in the e-Dossier system"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.list_states())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.list_states()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class ListSchoolsTool(BaseTool):
    name: str = "list_schools"
    description: str = "List schools with optional filters for state, zone, or LGA"
    
    class InputSchema(BaseModel):
        state_id: Optional[str] = Field(default=None, description="Filter by state ID")
        zone_id: Optional[str] = Field(default=None, description="Filter by zone ID")
        lga_id: Optional[str] = Field(default=None, description="Filter by LGA ID")
        page: int = Field(default=1, description="Page number")
        limit: int = Field(default=20, description="Results per page")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(
        self,
        state_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        lga_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        import asyncio
        try:
            result = asyncio.run(
                go_backend_client.list_schools(state_id, zone_id, lga_id, page, limit)
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self,
        state_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        lga_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        try:
            result = await go_backend_client.list_schools(state_id, zone_id, lga_id, page, limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetSchoolTool(BaseTool):
    name: str = "get_school"
    description: str = "Get detailed information about a specific school"
    
    class InputSchema(BaseModel):
        school_id: str = Field(description="School ID")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(self, school_id: str) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_school(school_id))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, school_id: str) -> str:
        try:
            result = await go_backend_client.get_school(school_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class ListPersonnelTool(BaseTool):
    name: str = "list_personnel"
    description: str = "List personnel (staff) with optional filters"
    
    class InputSchema(BaseModel):
        school_id: Optional[str] = Field(default=None, description="Filter by school ID")
        state_id: Optional[str] = Field(default=None, description="Filter by state ID")
        page: int = Field(default=1, description="Page number")
        limit: int = Field(default=20, description="Results per page")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        import asyncio
        try:
            result = asyncio.run(
                go_backend_client.list_personnel(school_id, state_id, page, limit)
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        try:
            result = await go_backend_client.list_personnel(school_id, state_id, page, limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class ListStudentsTool(BaseTool):
    name: str = "list_students"
    description: str = "List students with optional filters"
    
    class InputSchema(BaseModel):
        school_id: Optional[str] = Field(default=None, description="Filter by school ID")
        state_id: Optional[str] = Field(default=None, description="Filter by state ID")
        page: int = Field(default=1, description="Page number")
        limit: int = Field(default=20, description="Results per page")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        import asyncio
        try:
            result = asyncio.run(
                go_backend_client.list_students(school_id, state_id, page, limit)
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self,
        school_id: Optional[str] = None,
        state_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        try:
            result = await go_backend_client.list_students(school_id, state_id, page, limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetStudentTool(BaseTool):
    name: str = "get_student"
    description: str = "Get detailed information about a specific student"
    
    class InputSchema(BaseModel):
        student_id: str = Field(description="Student ID")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(self, student_id: str) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_student(student_id))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, student_id: str) -> str:
        try:
            result = await go_backend_client.get_student(student_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetEnrollmentsTool(BaseTool):
    name: str = "get_enrollments"
    description: str = "Get student enrollments with optional filters"
    
    class InputSchema(BaseModel):
        student_id: Optional[str] = Field(default=None, description="Filter by student ID")
        school_id: Optional[str] = Field(default=None, description="Filter by school ID")
        session_id: Optional[str] = Field(default=None, description="Filter by session ID")
        page: int = Field(default=1, description="Page number")
        limit: int = Field(default=20, description="Results per page")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(
        self,
        student_id: Optional[str] = None,
        school_id: Optional[str] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        import asyncio
        try:
            result = asyncio.run(
                go_backend_client.get_enrollments(student_id, school_id, session_id, page, limit)
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self,
        student_id: Optional[str] = None,
        school_id: Optional[str] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> str:
        try:
            result = await go_backend_client.get_enrollments(
                student_id, school_id, session_id, page, limit
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetSessionsTool(BaseTool):
    name: str = "get_sessions"
    description: str = "List academic sessions"
    
    class InputSchema(BaseModel):
        school_id: Optional[str] = Field(default=None, description="Filter by school ID")
        page: int = Field(default=1, description="Page number")
        limit: int = Field(default=20, description="Results per page")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(self, school_id: Optional[str] = None, page: int = 1, limit: int = 20) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_sessions(school_id, page, limit))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self, school_id: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> str:
        try:
            result = await go_backend_client.get_sessions(school_id, page, limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetRecommendationsTool(BaseTool):
    name: str = "get_recommendations"
    description: str = "Get ML-powered facility shortage recommendations for schools"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_recommendations())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.get_recommendations()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetDashboardStatsTool(BaseTool):
    name: str = "get_dashboard_stats"
    description: str = "Get dashboard statistics for the e-Dossier system"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_dashboard_stats())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.get_dashboard_stats()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetZonalSummaryTool(BaseTool):
    name: str = "get_zonal_summary"
    description: str = "Get zonal summary report"
    
    class InputSchema(BaseModel):
        school_id: Optional[str] = Field(default=None, description="Filter by school ID")
    
    args_schema: Type[BaseModel] = InputSchema
    
    def _run(self, school_id: Optional[str] = None) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_zonal_summary(school_id))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, school_id: Optional[str] = None) -> str:
        try:
            result = await go_backend_client.get_zonal_summary(school_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetGenderDistributionTool(BaseTool):
    name: str = "get_gender_distribution"
    description: str = "Get gender distribution statistics"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_gender_distribution())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.get_gender_distribution()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


class GetOSCDataTool(BaseTool):
    name: str = "get_osc_data"
    description: str = "Get Out-of-School Children (OSC) data"
    
    def _run(self) -> str:
        import asyncio
        try:
            result = asyncio.run(go_backend_client.get_osc_data())
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self) -> str:
        try:
            result = await go_backend_client.get_osc_data()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"


GO_BACKEND_TOOLS = [
    HealthCheckTool(),
    LoginTool(),
    ListStatesTool(),
    ListSchoolsTool(),
    GetSchoolTool(),
    ListPersonnelTool(),
    ListStudentsTool(),
    GetStudentTool(),
    GetEnrollmentsTool(),
    GetSessionsTool(),
    GetRecommendationsTool(),
    GetDashboardStatsTool(),
    GetZonalSummaryTool(),
    GetGenderDistributionTool(),
    GetOSCDataTool(),
]