Автоматизация CAPTCHA 


1. Установка зависимостей:

```bash

git clone https://github.com/__.git
cd _repo

python -m venv venv
source venv/bin/activate  
venv\Scripts\activate 

pip install -r requirements.txt

cp config/config.yaml. config/config.yaml

python -m database.init_db

uvicorn api.main:app --host 0.0.0.0 --port 8000

docker build -t arkose-captcha-solver .
docker run -d -p 8000:8000 --env-file .env arkose-captcha-solver

pytest tests/
