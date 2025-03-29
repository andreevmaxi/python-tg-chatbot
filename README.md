# python-tg-chatbot
telegram bot username: @latoken_hackaton_korobkom_bot  
tg bot that was created for hackaton at Latoken
  
  
in order to run bot you will need to create file .env in tg_bot folder with structure like:  
TELEGRAM_TOKEN=<YOUR_TG_BOT_TOKEN>  
OPENAI_KEY=<GPT_KEY>  
POSTGRES_PASSWORD=<YOUR_PASSWORD_FOR_DB>  
LOCAL_DB_URL=postgresql://latoken:${POSTGRES_PASSWORD}@localhost:5438/latoken_bot  
DOCKER_DB_URL=postgresql://latoken:${POSTGRES_PASSWORD}@postgres:5432/latoken_bot  
afterwards if you want to run telegram bot in docker container,  
than just use in this folder via cmd command "docker compose up -d"  
And also you need to create volume named postgres_data with command:  
"docker volume create postgres_data"



In order to locally run you need to install chromium  
sudo apt-get install -y wget gnupg && \   
sudo wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
sudo echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
sudo apt-get install -y \
google-chrome-stable \
fonts-liberation \
libglib2.0-0 \
libnss3 \
libx11-6 \
xvfb \
libgconf-2-4 \
libxtst6