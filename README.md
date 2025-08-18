

python 3.12.3

django 5.2

Para correr servidor localmente:

En la terminal VSCode, hacer el siguiente comando:

`python manage.py runserver`

y en el navegador web ir a la pagina:

`localhost:8000`


Proyecto creado con ayuda de estos tutoriales:

https://code.visualstudio.com/docs/python/tutorial-django

https://docs.djangoproject.com/en/5.2/intro/tutorial01/

https://docs.djangoproject.com/en/5.2/topics/install/#installing-official-release


Para poder clonar:

1- Instalar extensiones de python y django en vscode

2- correr

```
sudo apt install python3-pip
sudo apt install postgresql postgresql-contrib
```

en la terminal



3- crear una carpeta en la cual estara alojado el proyecto y el entorno virtual

4- correr estos comandos en esa carpeta:

```
sudo apt-get install python3-venv    # si es necesario

python3 -m venv .venv

source .venv/bin/activate
```


5- esto creara y activara el entorno virtual, sabremos que estamos dentro del entorno virtual cuando al inicio
de la linea de comandos diga (.venv)

6- dentro del entorno virtual, abrir vscode con el siguiente comando:

`code .`

6- presionar ctrl+shift+P en vscode, y seleccionar "Python: Select Interpereter"
de la lista que se presenta, seleccionar el entorno virtual que empieza con "./.venv" o ".\.venv"

7- ctrl+shift+P, buscar el comando "Terminal:Create New Terminal"
esto automaticamente activa el entorno virtual, se hara esto cada vez que se quiera trabajar en el

8- actualizar pip en el entorno virtual:

`python -m pip install --upgrade pip`

9- instalar django y el driver de postgresql para python en el entorno virtual:

`python -m pip install django`

`pip install psycopg2-binary`

10- ahora el entorno esta listo para correr django, se procede a clonar el repositorio dentro de este entorno virtual ya creado
nota que para poder clonar el repositorio, se debe tener git instalado y haber iniciado sesion de github en VSCode

  - Entrar a Source Control (Ctrl+Shift+G)
    
  - Clone Repository

  - Clone from Github

