from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.auth import route
app = FastAPI()

app.include_router(route.router)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["https://localhost:4200"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)
@app.get("/")
def home():
	return "Home"

