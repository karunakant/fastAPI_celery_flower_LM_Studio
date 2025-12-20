conda activate anuveda_ai
& D:/Code/AI/Python/local_llm/.venv/Scripts/Activate.ps1
pip install -r requirements.txt
python services\main.py
python -m fast_api.main
python -m streamlit run ui.fast_API_test
celery -A celery_service.celery_worker.celery_app worker --autoscale=10,3 --loglevel=info -c 4
streamlit run ui\app.py
celery -A celery_service.celery_worker:celery_app worker --loglevel=info -c 4
celery -A celery_service.celery_worker.celery_app flower




flower
celary
redis
logging
config
env
postgres
llm`



fast_api
heealthcheck


notion one platform for all
