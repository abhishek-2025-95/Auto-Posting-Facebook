"""
The Extractor: Web scraping module for news articles.
Extracts title and main text content from news URLs.
"""

from newspaper import Article
import logging

logger = logging.getLogger(__name__)


def extract_news_content(url):
    """
    Extract news article content from a URL.
    
    Args:
        url (str): The URL of the news article
        
    Returns:
        dict: Dictionary containing 'title' and 'text' keys, or None if extraction fails
    """
    try:
        logger.info(f"Extracting content from: {url}")
        article = Article(url)
        article.download()
        article.parse()
        
        if not article.title or not article.text:
            logger.warning("Article missing title or text content")
            return None
            
        result = {
            "title": article.title.strip(),
            "text": article.text.strip()
        }
        
        logger.info(f"Successfully extracted article: {result['title'][:50]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {e}")
        return None

