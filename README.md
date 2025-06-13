
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

python manage.py runserver 0.0.0.0:8000

gunicorn --bind 0.0.0.0:8000 your_project_name.wsgi:application
sudo systemctl daemon-reload
sudo systemctl restart gunicorn