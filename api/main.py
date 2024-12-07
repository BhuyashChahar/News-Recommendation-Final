# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Optional
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
from sklearn.cluster import KMeans
from datasketch import MinHashLSHForest, MinHash
from datetime import datetime
import numpy as np
import logging
import re
from pydantic import BaseModel

# Data Models
class ArticleRecommendation(BaseModel):
    article_id: Optional[int] = None
    cluster: Optional[int] = None
    category: str
    headline: str
    link: str
    score: Optional[float] = None

class Bot1Response(BaseModel):
    recommendations: List[ArticleRecommendation]
    message: str

class Bot2Response(BaseModel):
    recommendations: List[ArticleRecommendation]
    message: str

# Initialize FastAPI app with CORS
app = FastAPI(title="News Recommendation API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
bot1_recommendations = None
recommendation_bot = None

class NewsRecommendationBot:
    # [Previous NewsRecommendationBot implementation remains the same]
    # Copy the entire NewsRecommendationBot class from the previous response here

@app.on_event("startup")
async def startup_event():
    """Initialize both bots and load data on startup"""
    global bot1_recommendations, recommendation_bot
    try:
        logger.info("Starting up the application...")
        
        # Check if data files exist
        try:
            pd.read_csv('UserProfileData.csv')
            pd.read_csv('Processes_data.csv')
        except FileNotFoundError as e:
            logger.error(f"Data files not found: {e}")
            raise HTTPException(
                status_code=500,
                detail="Required data files not found. Please ensure UserProfileData.csv and Processes_data.csv are present."
            )

        # Initialize Bot 2
        recommendation_bot = NewsRecommendationBot(
            user_data_path='UserProfileData.csv',
            process_data_path='Processes_data.csv'
        )
        
        # Initialize Bot 1 recommendations
        processes_df = pd.read_csv('Processes_data.csv')
        bot1_recommendations = get_article_links(processes_df)
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

def get_article_links(df: pd.DataFrame, num_clusters: int = 10) -> List[dict]:
    # [Previous get_article_links implementation remains the same]
    # Copy the entire get_article_links function from the previous response here

@app.get("/", response_model=Bot1Response)
async def home():
    """Home endpoint returning Bot 1 recommendations"""
    try:
        if bot1_recommendations is None:
            raise HTTPException(status_code=503, detail="Service not yet initialized")
        return {
            "recommendations": bot1_recommendations,
            "message": "Successfully retrieved top articles from each cluster"
        }
    except Exception as e:
        logger.error(f"Error in home endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/{user_id}", response_model=Bot2Response)
async def get_recommendation(user_id: int):
    """Endpoint for Bot 2 personalized recommendations"""
    try:
        if recommendation_bot is None:
            raise HTTPException(status_code=503, detail="Service not yet initialized")
        recommendations = recommendation_bot.get_recommendations(user_id)
        return {
            "recommendations": recommendations,
            "message": f"Successfully retrieved personalized recommendations for user {user_id}"
        }
    except ValueError as e:
        logger.error(f"Value error in recommendations: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "bot1_status": "initialized" if bot1_recommendations else "not initialized",
        "bot2_status": "initialized" if recommendation_bot else "not initialized"
    }

if __name__ == "__main__":
    try:
        logger.info("Starting server...")
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise