FROM python:3.12.5
WORKDIR /app
COPY . /app
ENV DB_HOST=localhost
ENV DB_USER=postgres
ENV DB_PORT=5432
ENV DB_PASSWORD=Jadore10@
ENV DB_NAME=trading_platform
ENV CC_DATA_API_KEY=35d08de31c349dd8081ec1f8b4523d3402b08d78e04bac0218ff7af88cfffb63
ENV NEWS_API_KEY=ab349f20a31241bd9bb9416b9fcb8366
ENV SENDER_EMAIL=wifimemesyt@gmail.com
ENV GOOGLE_CLOUD_PROJECT=django-trading
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ['python', 'manage.py', 'runserver']
