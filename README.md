En Django, tenemos el proyecto (en este caso, web_project)
y la app (webapp)
A menos que el alcance de nuestro trabajo practico suba mucho, creo que solo necesitaremos una app para todo

python 3.12.3

django 5.2

Para correr servidor localmente:

En la terminal VSCode, hacer el siguiente comando:

`python manage.py runserver`

y en el navegador web ir a la pagina:

`localhost:8000`

En caso que diga "This port is already in use" simplemente matar el proceso

`sudo lsof -i:<port_number>`

Reemplazar <port_number> por el puerto en uso (por defecto, usamos 8000)

Usar el PID dado para matar le proceso

`sudo kill <PID>`

Cuando se hacen cambios (ej anhadir clases a model.py) se debe hacer migraciones (actualizar la base de datos)

```
python manage.py makemigrations
python manage.py migrate
```


Proyecto creado con ayuda de estos tutoriales:

https://code.visualstudio.com/docs/python/tutorial-django

https://docs.djangoproject.com/en/5.2/intro/tutorial01/

https://docs.djangoproject.com/en/5.2/topics/install/#installing-official-release


Clone the repo:

```
git clone <your-repo-url>
cd <your-project>
```
Create virtual environment and activate:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Copy .env.example to .env and fill in database credentials.

Ensure PostgreSQL user and database exist:

```
sudo -i -u postgres
createuser myuser -P
createdb mydb -O myuser
```

Run migrations:

```
python manage.py migrate
```

Start server:

```
python manage.py runserver
```
