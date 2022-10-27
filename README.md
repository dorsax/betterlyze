# betterplace_fetch
Fetches data from the betterplace.org API and will render charts which can then be used e.g. on a Website to display informations about a project.

# installation

> This project requires python 3.9 or later!

Create a python virtual environment and activate it:
```
python -m venv 'venv'
source venv/bin/activate 
```
All requirements are in the standard `requirements.txt`. Installing them inside your virtual environment is easy: 

```powershell
python -m pip install -r requirements.txt
```

For database support like mysql (which is shipped with this project), you have to install the corresponding packages to your OS before installing the needed packages for django to successfully connect to your database.

``` 
cp betterlyze/betterlyze/template-settings.py betterlyze/betterlyze/settings.py
```

Edit the following settings:
- DEBUG = FALSE
- ALLOWED_HOSTS (insert the FQDN where the app should be published)
- DATABASES
- TIME_ZONE
- LANGUAGE_CODE

Then apply migrations:
```
python betterlyze/manage.py migrate
```

check, if the server would run:
```
python betterlyze/manage.py runserver
```
# cron

In order to achieve regular fetching of new donations, add the following cronjob to your crontab. Please adjust the placeholders as needed:

```cron
*/5 * * * * username /path/to/project/venv/bin/python /path/to/project/betterlyze/manage.py runcrons 
```