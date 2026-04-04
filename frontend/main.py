from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.get("/features", response_class=HTMLResponse)
async def features():
    return FileResponse("static/features.html")

@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works():
    return FileResponse("static/how-it-works.html")

@app.get("/pricing", response_class=HTMLResponse)
async def pricing():
    return FileResponse("static/pricing.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/about", response_class=HTMLResponse)
async def about():
    return FileResponse("static/about.html")

@app.get("/contact", response_class=HTMLResponse)
async def contact():
    return FileResponse("static/contact.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
