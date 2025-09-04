#!/usr/bin/env python3
import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set in environment variables")
        print("Please set your OpenAI API key in the .env file")
    
    if not os.getenv("SECRET_KEY"):
        print("Warning: SECRET_KEY not set in environment variables")
        print("Please set a secret key in the .env file")
    
    print("Starting HireMatch AI...")
    print("API documentation will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
