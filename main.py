from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
import aio_pika
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RabbitMQ Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "alerts"

# FastAPI app
app = FastAPI()

# Status Dictionary
status = {"running": False, "message": ""}

# Message model for RabbitMQ
class Message(BaseModel):
    type: str
    message: str

# RabbitMQ Connection Function
async def send_to_rabbitmq(message: str):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=message.encode()),
                routing_key=QUEUE_NAME
            )
        print("[INFO] Sent message to RabbitMQ:", message)
    except Exception as e:
        print(f"[ERROR] RabbitMQ send failed: {e}")

# Background Scan Task
async def run_scan():
    """Simulates the start of a security scan by sending alerts to RabbitMQ"""
    global status
    status["running"] = True
    status["message"] = "Scan started..."
    
    try:
        # Simulate scan running
        await asyncio.sleep(3)  # Simulate some processing time
        await send_to_rabbitmq("Scan completed: No attack detected")
        status["message"] = "Scan completed successfully"
    
    except Exception as e:
        status["message"] = f"Scan failed: {str(e)}"
    
    finally:
        status["running"] = False

# Endpoint: Trigger Scan
@app.post("/start-scan")
async def start_scan(background_tasks: BackgroundTasks):
    """Start the cyber attack scan"""
    if status["running"]:
        raise HTTPException(status_code=400, detail="Scan already in progress")
    
    background_tasks.add_task(run_scan)
    return {"message": "Scan started successfully!"}

# Endpoint: Get Scan Status
@app.get("/status")
async def get_status():
    """Check the status of the current scan"""
    return status

# Endpoint: RabbitMQ Alert (For Testing)
@app.post("/send-alert")
async def send_alert(message: Message):
    """Send a test alert to RabbitMQ"""
    try:
        await send_to_rabbitmq(f"[ALERT] {message.type}: {message.message}")
        return {"message": "Alert sent successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
