import pika
import json
import os
import logging
from langchain.chat_models import ChatGroq
from langchain.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)

# RabbitMQ Config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

# Groq LLM Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

llm = ChatGroq(temperature=0.7, model_name=GROQ_MODEL, api_key=GROQ_API_KEY)

def callback(ch, method, properties, body):
    alert = json.loads(body)
    logging.info(f"Received alert: {alert}")

    prompt = f"Security Alert: {alert['type']}. Provide mitigation steps."
    response = llm.invoke(prompt)
    
    logging.info(f"LLM Response: {response}")

def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
    )
    
    channel = connection.channel()
    channel.queue_declare(queue="alerts")

    channel.basic_consume(queue="alerts", on_message_callback=callback, auto_ack=True)
    logging.info("Listening for alerts...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
