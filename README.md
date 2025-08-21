# Global Exchange WebApp

## Requisitos

- Python 3.12.3
- Django 5.2
- PostgreSQL (con usuario y base de datos creados)

Para correr servidor localmente:

En la terminal VSCode, hacer el siguiente comando:

`python manage.py runserver`

y en el navegador web ir a la pagina:

`localhost:8000`


Proyecto creado con ayuda de estos tutoriales:

https://code.visualstudio.com/docs/python/tutorial-django

https://docs.djangoproject.com/en/5.2/intro/tutorial01/

https://docs.djangoproject.com/en/5.2/topics/install/#installing-official-release


---

## Configuración del proyecto

### 1. Clonar el repositorio

```bash
git clone <your-repo-url>
cd <your-project>
```
<img width="642" height="194" alt="image" src="https://github.com/user-attachments/assets/f3dc801b-c89a-4592-89de-d28501811c07" />


### 2. Crear y activar el entorno virtual

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```
>Nota: Si da error relacionado con externally-managed-environment, asegúrate de estar dentro del virtual environment (venv).
<img width="1097" height="681" alt="image" src="https://github.com/user-attachments/assets/367faf1e-61c5-4484-af8e-bd2924d9d46f" />

### 4. Configurar variables de entorno

Copiar el archivo de ejemplo .env.example a .env:

```bash
cp .env.example .env
```
>Completar las credenciales de la base de datos (DB_NAME, DB_USER, DB_PASSWORD, etc.).
>El archivo .env debe estar en la raíz del proyecto, junto a manage.py.
<img width="795" height="575" alt="image" src="https://github.com/user-attachments/assets/74da7ace-b616-4ae2-8acb-79947aa4c2a2" />
<img width="647" height="528" alt="image" src="https://github.com/user-attachments/assets/a84e1ba6-5a76-44e9-a426-497ab3bb1a96" />


### 5. Configuración de PostgreSQL

Asegurarse de que el usuario y la base de datos existan:
```bash
sudo -i -u postgres
createuser myuser -P
createdb mydb -O myuser
```
>Si ocurre error de permiso denegado al migrar, revisar que el usuario tenga privilegios sobre el schema public.

### 6. Migraciones de la base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```
<img width="655" height="443" alt="image" src="https://github.com/user-attachments/assets/3e43c711-e275-4176-9bb5-7955749fc68c" />



### 7. Levantar el servidor local

```bash
python manage.py runserver
```

## 8. Sincronizar cambios con el remoto (GitHub)
<img width="852" height="323" alt="image" src="https://github.com/user-attachments/assets/1a2edd61-d1a2-4c94-a81c-7048a88d07ee" />


## Consejos para evitar problemas
Ramas: Mantener main solo con releases estables. Todos los cambios van a desarrollo.
Entorno virtual: Siempre activarlo antes de instalar paquetes o correr el servidor.
Variables de entorno: Revisar que .env esté correctamente configurado antes de migrar.
Pull remoto: Hacer git pull origin desarrollo antes de empezar a trabajar para evitar conflictos.
