from fastapi import FastAPI

app = FastAPI(
    title="Test API",
    description="Just a test",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Run with: uvicorn test_server:app --reload 