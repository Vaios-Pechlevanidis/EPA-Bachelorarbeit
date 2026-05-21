from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database.supabase_client import get_supabase_client
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from routes.topics import router as topics_router
from routes.upload import router as upload_router
from routes.companies import router as companies_router
from routes.analytics import router as analytics_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    try:
        get_supabase_client()
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {str(e)}")
    
    yield
    
    # Shutdown (if needed, add cleanup code here)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://epa-bachelorprojekt.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics_router)
app.include_router(upload_router)
app.include_router(companies_router)
app.include_router(analytics_router)


@app.get("/api/hello")
def hello():
    return {"message": "Hallo von FastAPI"}


@app.get("/api/test-connection")
async def test_connection():
    """Test Supabase connection and verify tables exist."""
    from config import get_settings
    
    try:
        # First check if configuration is loaded
        settings = get_settings()
        supabase = get_supabase_client()
        
        # Test connection by querying the candidates table
        candidates_test = supabase.table("candidates").select("id").limit(1).execute()
        
        # Test connection by querying the employee table
        employee_test = supabase.table("employee").select("id").limit(1).execute()
        
        # Test connection by querying the companies table
        companies_test = supabase.table("companies").select("id").limit(1).execute()
        
        return {
            "status": "success",
            "message": "Supabase connection successful",
            "tables": {
                "candidates": {
                    "exists": True,
                    "accessible": True,
                    "row_count": len(candidates_test.data) if candidates_test.data else 0
                },
                "employee": {
                    "exists": True,
                    "accessible": True,
                    "row_count": len(employee_test.data) if employee_test.data else 0
                },
                "companies": {
                    "exists": True,
                    "accessible": True,
                    "row_count": len(companies_test.data) if companies_test.data else 0
                }
            },
            "connection": {
                "url_configured": bool(settings.supabase_url),
                "key_configured": bool(settings.supabase_key)
            }
        }
    except ValueError as e:
        # Configuration error
        return {
            "status": "error",
            "message": "Configuration error",
            "error": str(e),
            "troubleshooting": [
                "Check that SUPABASE_URL and SUPABASE_KEY are set in .env file",
                "Verify the .env file is in the backend directory",
                "Ensure there are no typos in the environment variable names"
            ]
        }
    except Exception as e:
        error_message = str(e)
        # Check if it's a table not found error
        if "relation" in error_message.lower() or "does not exist" in error_message.lower() or "not found" in error_message.lower():
            return {
                "status": "partial",
                "message": "Supabase connection works, but tables may not exist yet",
                "error": error_message,
                }
        return {
            "status": "error",
            "message": "Failed to connect to Supabase",
            "error": error_message,
            "troubleshooting": [
                "Check that SUPABASE_URL and SUPABASE_KEY are correct in .env file",
                "Verify your Supabase project is active",
                "Ensure your Supabase API key has the correct permissions"
            ]
        }


# Example CRUD endpoints - adapt table name and schema to your needs
# These examples use a generic "items" table

@app.get("/api/items")
async def get_items() -> List[Dict[str, Any]]:
    """Get all items from the database."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("items").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching items: {str(e)}")


@app.get("/api/items/{item_id}")
async def get_item(item_id: int) -> Dict[str, Any]:
    """Get a specific item by ID."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("items").select("*").eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching item: {str(e)}")


@app.post("/api/items")
async def create_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new item."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("items").insert(item).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create item")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@app.put("/api/items/{item_id}")
async def update_item(item_id: int, item: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing item."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("items").update(item).eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int) -> Dict[str, str]:
    """Delete an item by ID."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("items").delete().eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")
