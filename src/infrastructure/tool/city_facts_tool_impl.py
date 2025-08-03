from typing import Any
import httpx
import asyncio
import json
from langchain_core.tools import tool
from ...domain.agent.tool_interface import ToolInterface, ToolResult

async def fetch_city_info_from_wikipedia(city: str) -> dict:
    """Get city information from English Wikipedia API"""
    search_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{search_url}/{city}")
        response.raise_for_status()
        return response.json()

@tool
def get_city_facts(city: str) -> str:
    """Get basic information about a specified city.
    
    Args:
        city: Name of the city in English (single word, e.g., 'Paris', 'Tokyo', 'London')
        
    Returns:
        City information JSON string from Wikipedia API
    """
    try:
        # Get information from Wikipedia API
        city_data = asyncio.run(fetch_city_info_from_wikipedia(city))
        return json.dumps(city_data, ensure_ascii=False, indent=2)
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"City '{city}' not found in Wikipedia. Please use English city name in single word (e.g., 'Paris', 'Tokyo', 'London')."
        else:
            return f"Failed to fetch city information (HTTP Error: {e.response.status_code})"
    except Exception as e:
        return f"Error occurred while fetching city information: {str(e)}"

class CityFactsToolImpl(ToolInterface):
    """City information tool implementation"""
    
    @property
    def name(self) -> str:
        return "CityFactsTool"
    
    @property
    def description(self) -> str:
        return "Get basic information about a specified city from Wikipedia. Please use English city name in single word (e.g., 'Paris', 'Tokyo', 'London')."
    
    def get_langchain_tool(self) -> Any:
        return get_city_facts
    
    def execute(self, city: str, **kwargs) -> ToolResult:
        """Get city information and return result object"""
        try:
            # Get information from Wikipedia API
            city_data = asyncio.run(fetch_city_info_from_wikipedia(city))
            
            return ToolResult(
                success=True,
                data=json.dumps(city_data, ensure_ascii=False, indent=2)
            )
            
        except httpx.HTTPStatusError as e:
            error_type = "retryable" if e.response.status_code in [500, 502, 503, 504] else "non-retryable"
            
            if e.response.status_code == 404:
                error_msg = f"City '{city}' not found in Wikipedia. Please use English city name in single word (e.g., 'Paris', 'Tokyo', 'London')."
                error_type = "retryable"  # City name issues are fixable
            else:
                error_msg = f"Failed to fetch city information (HTTP Error: {e.response.status_code})"
            
            return ToolResult(
                success=False,
                error_message=error_msg,
                error_type=error_type
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error_message=f"Error occurred while fetching city information: {str(e)}",
                error_type="retryable"
            )