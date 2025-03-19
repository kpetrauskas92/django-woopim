from celery import shared_task
from .utils import scrape_retail_vista

@shared_task
def run_scraper():
    """Celery task to run the Retail Vista scraper daily."""
    scrape_retail_vista()