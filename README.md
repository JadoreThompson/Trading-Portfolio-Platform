## **Description**

This project is a full-stack Python web application built with Django, leveraging multithreading and asynchronous programming to build a highly responsive and efficient engine. It integrates a custom [sentiment analysis model](https://github.com/JadoreThompson/CryptoSentimentAnalysis), which processes market data to provide real-time insights, transported through a REST API. This functionality is crucial for traders and investors seeking to make data-driven decisions based on sentiment in the cryptocurrency market.

**Key Highlights:**

- **Async & Multithreading:** Implemented asynchronous processes for high-performance, non-blocking requests, ensuring fast responses in a data-heavy environment.
- **Custom Sentiment Analysis Model:** Integrated a custom-trained NLP model to analyze real-time crypto news and social media sentiment, providing actionable insights for users.
- **API Integration:** Fetched data from external services like NewsAPI and CryptoCompare to enrich the analysis with up-to-date financial news and crypto market data.
- **Redis for Task Scheduling:** Used Redis for managing background tasks, such as sending weekly PDF summaries and real-time notifications for order creation/close.

Throughout the application, I maintained a clean structure with clear separation of concerns, ensuring maintainability and scalability.

## Prerequisites

- **Redis**: Utilised for managing Celery task queues and periodic tasks like email notifications and scheduled summaries.
    
    ```bash
    docker run --name redis-container -p 6379:6379 -d redis
    
    ```
    
- **GCloud OAuth**: Since Google discontinued app passwords, OAuth credentials were used to programmatically send emails.
    - [Google Cloud ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- **API Keys**:
    - [NewsAPI](https://newsapi.org/docs)
    - [CryptoCompare Data API](https://developers.cryptocompare.com/documentation/data-api/introduction)
    
    ```bash
    # Environment variables
    DB_HOST=localhost
    DB_USER=postgres
    DB_PORT=5432
    DB_PASSWORD=password
    DB_NAME=db_name
    
    CC_DATA_API_KEY=<api_key>
    NEWS_API_KEY=<api_key>
    
    SENDER_EMAIL=your_gmail
    GOOGLE_CLOUD_PROJECT=your_cloud_project
    
    ```
    

## **Installation**

```bash
# Clone the repository
git clone <https://github.com/JadoreThompson/Trading-Portfolio-Platform/>

# Install the requirements
pip install -r requirements.txt

# Run Django server
python manage.py runserver

# Start Celery worker
celery -A toolbox worker --pool=solo -l INFO

# Start Celery Beat (for scheduling tasks)
celery -A toolbox beat -l INFO --scheduler django_celery_beat.schedulers.DatabaseScheduler

```

## **Contact**

If you’re interested in collaborating or have any opportunities, feel free to contact me at [jadorethompson6@gmail.com](mailto:jadorethompson6@gmail.com) or connect with me on [LinkedIn](https://www.linkedin.com/in/jadore-t-49379a295/).In the future I’m looking to build a list and phrases that indicate sentiment in an attempt to aid the model then combined with the CIMAWA model mentioned in the FBert paper. If you've cloned  the repo fell free to contact me too I'd like to communicate with people who find my work interesting
