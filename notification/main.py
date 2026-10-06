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

APP_INFO = {
    "name": "notification",
    "description": "Microservice d'envoi des notifications",
    "version": "1.0.0",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enregistrement dans Eureka au démarrage
    await eureka_client.init_async(
        eureka_server="http://localhost:8761/eureka",
        app_name="NOTIFICATION",
        instance_port=PORT,
        instance_host="localhost",
        instance_ip="127.0.0.1",
        # Même format que les services Spring : localhost:<service>:<port>
        instance_id=f"localhost:notification:{PORT}",
        home_page_url=f"{BASE_URL}/",
        health_check_url=f"{BASE_URL}/actuator/health",
        status_page_url=f"{BASE_URL}/actuator/info",
    )
    print(f"Eureka registration complete - NOTIFICATION registered on port {PORT}")
    yield
    # Désenregistrement à l'arrêt
    print("Stopping Notification microservice...")
    await eureka_client.stop_async()
    print("Eureka unregistration complete")


app = FastAPI(title="Notification Microservice", version=APP_INFO["version"], lifespan=lifespan)


@app.get("/api/notifications/hello")
def hello():
    return {"message": "Hello from Notification Microservice"}


# Endpoints au format Spring Boot Actuator, déclarés à Eureka (status_page_url / health_check_url)
@app.get("/actuator/info")
def actuator_info():
    return {"app": APP_INFO}


@app.get("/actuator/health")
def actuator_health():
    return {"status": "UP"}


@app.get("/health")
def health():
    return {"service": "NOTIFICATION", "status": "UP", "port": PORT}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
