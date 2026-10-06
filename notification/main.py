from contextlib import asynccontextmanager
from fastapi import FastAPI
from py_eureka_client import eureka_client
import uvicorn
import os

# Fix SSL issue
os.environ.pop('SSL_CERT_FILE', None)

# Lire le port depuis la variable d'environnement ou utiliser 8084 par défaut
# (doit être le même que celui passé à uvicorn --port)
PORT = int(os.getenv("PORT", 8084))
BASE_URL = f"http://localhost:{PORT}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enregistrement dans Eureka au démarrage
    await eureka_client.init_async(
        eureka_server="http://localhost:8761/eureka",
        app_name="NOTIFICATION",
        instance_port=PORT,
        instance_host="localhost",
        instance_ip="127.0.0.1",
        home_page_url=f"{BASE_URL}/",
        health_check_url=f"{BASE_URL}/health",
        status_page_url=f"{BASE_URL}/health",
    )
    print(f"Eureka registration complete - NOTIFICATION registered on port {PORT}")
    yield
    # Désenregistrement à l'arrêt
    print("Stopping Notification microservice...")
    await eureka_client.stop_async()
    print("Eureka unregistration complete")


app = FastAPI(title="Notification Microservice", lifespan=lifespan)


@app.get("/api/notifications/hello")
def hello():
    return {"message": "Hello from Notification Microservice"}


@app.get("/health")
def health():
    return {"service": "NOTIFICATION", "status": "UP", "port": PORT}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
