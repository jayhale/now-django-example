# Django running on Zeit Now

## Tutorial


### Install Django

```
$ mkdir now-django-example
$ cd now-django-example
$ pip install Django
$ django-admin startproject now_app .
```

### Add an app

```
$ python manage.py startapp example
```

Add the new app to your application settings (`now_app/settings.py`):
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'example',
]
```

Be sure to also include your new app URLs in your project URLs file (`now_app/urls.py`):
```python
# now_app/urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('', include('example.urls')),
]
```


#### Create the first view

Add the code below (a simple view that returns the current time) to `example/views.py`:
```python
# example/views.py
from datetime import datetime

from django.http import HttpResponse


def index(request):
    now = datetime.now()
    html = f'''
    <html>
        <body>
            <h1>Hello from Zeit Now!</h1>
            <p>The current time is { now }.</p>
        </body>
    </html>
    '''
    return HttpResponse(html)
```


#### Add the first URL

Add the code below to a new file `example/urls.py`:
```python
# example/urls.py
from django.urls import path

from example.views import index


urlpatterns = [
    path('', index),
]
```


### Test your progress

Start a test server and navigate to `localhost:8000`, you should see the index view you just
created:
```
$ python manage.py runserver
```

### Get ready for Now

#### Add the Now configuration file

Create a new file `index.py` to act as your application entrypoint for Now. The file should import
the WSGI application you want to use and make it available as `application`:
```python
# index.py
from now_app.wsgi import application
```

Create a new file `now.json` and add the code below to it:
```json
{
    "version": 2,
    "name": "python-wsgi-example",
    "builds": [{
        "src": "index.py",
        "use": "@ardent-labs/now-python-wsgi",
        "config": { "maxLambdaSize": "15mb" }
    }]
}
```
This configuration sets up a few things:
1. `"src": "index.py"` tells Now that `index.py` is the only application entrypoint to build
2. `"use": "@ardent-labs/now-python-wsgi"` tells Now to use the `now-python-wsgi` builder (you can
   read more about the builder at https://github.com/ardent-co/now-python-wsgi)
3. `"config": { "maxLambdaSize": "15mb" }` ups the limit on the size of the code blob passed to
   lambda (Django is pretty beefy)

Add django to requirements.txt
```
# requirements.txt
django==2.1.7
```


#### Update your Django settings

First, update allowed hosts in `settings.py` to include `now.sh`:
```python
# settings.py
ALLOWED_HOSTS = ['.now.sh']
```

Second, get rid of your database configuration since many of the libraries django may attempt to
load are not available on lambda (and will create an error when python can't find the missing
module):
```python
# settings.py
DATABASES = {}
```


### Deploy

With now installed you can deploy your new application:
```
$ now
> Deploying now-django-example under jayhale
...
> Success! Deployment ready [57s]
```

Check your results by visiting https://zeit.co/dashboard/project/now-django-example

## Ready to add a database? Try Postgres.

### Configure Django Settings

Configure `now_app/settings.py` to accept database connection strings using `dj_database_url`

```
# now_app/settings.py

import dj_database_url

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}

```

While in `now_app/settings.py`, add `whitenoise`.  WhiteNoiseMiddleware enables Django to serve 
its own static files. Without whitenoise, Django Admin won't import necessary CSS, and we will use 
the Django admin to test whether or not our database connection is working.

```
# now_app/settings.py

MIDDLEWARE = [
    ... other stuff ...,
    'whitenoise.middleware.WhiteNoiseMiddleware',
]
```

Add both `whitenoise` and `dj_database_url` to requirements.txt

At this point, requirements.txt file should include:

```
# requirements.txt

dj-database-url==0.5.0
Django==2.1.7
Werkzeug >=0.14,<1
whitenoise
```
### Add a pre-compiled Django Postgres adapter: psycopg2

Django needs an adapter like `psycopg2` to connect to Postgres. 

Only certain libraries are available in the lambda environment, and `psycopg2` is not 
one of them... so simply adding `psycopg2` to `requirements.txt` will not work.

Instead, bundle a pre-compiled `psycopg2` with your project at root level, where Django can import 
as needed.  `psycopg2` must be compiled for the correct python version and environment.

Fortunately, [@jkehler](https://github.com/jkehler) has done the work for us in this repo:
[https://github.com/jkehler/awslambda-psycopg2](https://github.com/jkehler/awslambda-psycopg2)

Download package `awslambda-psychopg2` as a zip file, and copy this subfolder into your 
project's root directory:

`awslambda-psychopg2-master/with_ssl_support/psychopg2-3.6`

Rename folder `psychopg2-3.6` to `psychopg2`

Project directory should look like this:
```
/now-django-example
    /example
    /now_app
    /psycopg2 # this one you just added.
    index.py
    manage.py
    now.json
    README.md
    requirements.txt
```

### Create a database server

One easy way to get up and running fast is to use a Digital Ocean Database Cluster. 

 - Log in at digitalocean.com
 - Select the green 'Create' button in the top right > Databases
 - Follow instructions to create a PostgreSQL 10 server

Feel free to skip the "getting started" section. 

On the Connection Details panel, select dropdown "Connection String" and Copy. 

Your connection string should look something like this:

```
postgres://doadmin:<YOUR-PASSWORD>@<YOUR-DATABASE-SERVER>.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```


_Definitely don't use this default connection string in prod. For prod, create database users with specific permissions.  We only use this connection string because it is easy for a tutorial / proof-of-concept_. 

### Seed the database server with a user

Lambda environments are immutable, and you cannot run environment commands like `python manage.py ...`

One way to seed the database is to run Django commands locally, _before_ deploying to Now (though  connecting to the same database server).

In your environment, set environment variable DATABASE_URL to the database connection string from Digital Ocean. 

```console
user:~/now-django-example $ export DATABASE_URL=postgres://doadmin:<YOUR-PASSWORD>@<YOUR-DATABASE-SERVER>.db.ondigitalocean.com:25060/defaultdb?sslmode=require

user:~/now-django-example $ echo $DATABASE_URL
postgres://doadmin:<YOUR-PASSWORD>@<YOUR-DATABASE-SERVER>.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

Ensure your local environment has  installed requirements.txt 
```console
user:~/now-django-example $ python3 -m pip install -r requirements.txt
```

Then use manage.py to create a superuser:
```console
user:~/now-django-example $ python3 manage.py createsuperuser
```

Follow Django's instructions to create the super user. 

Run the server and try logging in to make sure the database is seeded correctly. 

```console
user:~/now-django-example $ python3 manage.py runserver
```
Navigate to: https://localhost:8000/admin and log in using the super user you created above. 

Your database is seeded. Stop the server using CTRL+C and proceed with Now deployment. 

### Modify now.json environment variables and routes. 

`dj_database_url` will look for an environment variable named `DATABASE_URL`.

Your `DATABASE_URL`, however, contains sensitive information, so we will use a [now secret](https://zeit.co/docs/v1/features/env-and-secrets).

```console
user:~/now-django-example $ now secret add db-url postgres://doadmin:<YOUR-PASSWORD>@<YOUR-DATABASE-SERVER>.db.ondigitalocean.com:25060/defaultdb?sslmode=require
> Success! Secret db-url added (pejowei) [466ms]
```

Add environment variable to `now.json`

```json
{
    "env":{
        "DATABASE_URL":"@db-url"
    }
}
```

While editing `now.json`, this is a good time to update routes. 

We want all requests and responses to be routed through the index.py handler file, so your Django
application needs to be routed like a single-page app.

Add the following to `now.json` to send all requests to your Django wsgi application via index.py:

```json
{
    "routes" : [{
        "src" : "/(.*)", "dest":"/"
    }],
}
```

### Deploy

You can now redeploy (pun intended) your new application:
```
$ now
> Deploying now-django-example under pejowei
...
> Success! Deployment ready [57s]
```

Check your results by visiting https://zeit.co/dashboard/project/now-django-example

You will know if everything worked if you can log into Django admin and add a user.

Django admin will be available at https://YOUR-DEPLOYMENT.now.sh/admin

Good luck!
