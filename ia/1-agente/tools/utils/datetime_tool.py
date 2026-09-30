from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Optional

BOGOTA_TZ = ZoneInfo("America/Bogota")
import logging
import traceback
import time
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

class GetCurrentDatetimeTool:

    _tool_data: dict
    _tenant_id: Optional[str] = None
    _version: Optional[str] = None

    def __init__(self, tenant_id: str, version: str):
        start_time = time.time()
        try:
            self._tenant_id = tenant_id
            self._version = version
        except Exception as e:
            logger.error(
                "Error during initialization of GetCurrentDatetimeTool: %s", str(e)
            )
        finally:
            end_time = time.time()

    async def get_current_datetime(self):
        """
        Obtiene la fecha y hora actual.

        Returns:
            str: Fecha y hora actual en formato yyyy-MM-dd HH:mm:ss.
        """
        start_time = time.time()
        try:
            now = datetime.now(tz=BOGOTA_TZ)
            return now.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(
                "GetCurrentDatetimeTool - Error Getting current datetime - Error: %s",
                str(e),
            )
        finally:
            end_time = time.time()

    def _get_params_class(self):
        try:
            logger.info("Defining parameters class for GetCurrentDatetimeTool.")
            # Esta tool no tiene parámetros, así que creamos una clase vacía
            class DatetimeParams:
                pass

        except Exception as e:
            logger.error(
                "Error defining parameters class for GetCurrentDatetimeTool. An error occurred: %s",
                str(e),
            )
            logger.debug("Exception details: %s", traceback.format_exc())

        return DatetimeParams

    def get_structured_tool(self, tool_name: str, tool_data: dict) -> StructuredTool:
        start_time = time.time()
        try:
            self._tool_data = tool_data
            params_class = self._get_params_class()

            async def validate_and_instantiate(**kwargs):
                return await self.get_current_datetime()

            create_tool = StructuredTool(
                name=tool_name,
                coroutine=validate_and_instantiate,
                args_schema=params_class,
                description=self._tool_data.get("description", ""),
            )
            return create_tool
        except Exception as e:
            logger.error(
                "Error in structured tool with name: %s - An error occurred: %s",
                tool_name,
                str(e),
            )
            return None
        finally:
            end_time = time.time()

    @staticmethod
    def get_tool():
        async def wrapper(**kwargs) -> Any:
            now = datetime.now(tz=BOGOTA_TZ)
            return now.strftime("%Y-%m-%d %H:%M:%S")

        return StructuredTool.from_function(
            name="get_current_datetime",
            description="Devuelve la fecha y hora actual en formato yyyy-MM-dd HH:mm:ss.",
            coroutine=wrapper,
        )
