import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from datetime import datetime
import numpy as np
import os

class Bot1:
    def __init__(self, csv_file_path):
        """
        Initialize Bot 1 with the path to the CSV file
        
        :param csv_file_path: Full path to the CSV file containing news data
        """
        self.csv_file_path = csv_file_path
        
        # Validate file exists
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
    def get_article_links(self, num_clusters=10):
        """
        Returns links to top articles from each cluster
        
        :param num_clusters: Number of clusters to create
        :return: List of recommended article links
        """
        try:
            # Read and preprocess data
            df = pd.read_csv(self.csv_file_path)
            df['DateTime'] = pd.to_datetime(df['DateTime'])
            
            # Create combined text for clustering
            df['combined_text'] = (
                df['category'] + ' ' + 
                df['subcategory'] + ' ' + 
                df['headline'] + ' ' + 
                df['Entire_News']
            )
            
            # Vectorize text
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            vectors = vectorizer.fit_transform(df['combined_text'])
            
            # Perform clustering
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            df['cluster'] = kmeans.fit_predict(vectors)
            
            # Calculate scores
            current_time = datetime.now()
            df['time_diff'] = df['DateTime'].apply(lambda x: (current_time - x).total_seconds() / (24 * 3600))
            df['time_score'] = df['time_diff'].apply(lambda x: -np.exp(-0.1 * x))  # Negative weight for time
            df['final_score'] = (0.4 * df['time_score']) + (0.6 * df['Mean_Time'])  # Positive weight for ratings
            
            # Get top article links from each cluster
            recommended_links = []
            for cluster in range(num_clusters):
                cluster_articles = df[df['cluster'] == cluster]
                
                # Skip if no articles in cluster
                if cluster_articles.empty:
                    continue
                
                try:
                    top_article = cluster_articles.loc[cluster_articles['final_score'].idxmax()]
                    recommended_links.append({
                        'cluster': cluster + 1,
                        'category': top_article['category'],
                        'headline': top_article['headline'],
                        'link': top_article['News_Link']
                    })
                except Exception as e:
                    print(f"Error processing cluster {cluster}: {e}")
            
            return recommended_links
        
        except Exception as e:
            print(f"Error in get_article_links: {e}")
            return []

    def get_results(self):
        """
        Wrapper method to get results for API integration
        
        :return: List of recommended articles
        """
        try:
            # Try to get article links with default 10 clusters
            return self.get_article_links()
        except Exception as e:
            print(f"Bot 1 error: {e}")
            return [
                {
                    "error": "Could not retrieve article recommendations",
                    "details": str(e)
                }
            ]

# Example usage for debugging
def main():
    try:
        # Adjust the path to your CSV file
        csv_file_path = "Processes_data.csv"
        bot1 = Bot1(csv_file_path)
        
        recommended_links = bot1.get_article_links()
        
        print("\nRecommended Article Links:")
        print("-" * 50)
        for article in recommended_links:
            print(f"\nCluster {article['cluster']} ({article['category']})")
            print(f"Headline: {article['headline']}")
            print(f"Link: {article['link']}")
    
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()