# python-tg-chatbot
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