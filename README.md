# betterplace_fetch
Fetches data from the betterplace.org API and will render charts which can then be used e.g. on a Website to display informations about a project.

# installation

All requirements are in the standard `requirements.txt`. Installing them is easy: 

```powershell
python -m pip install -r requirements.txt
```

# cron

In order to achieve regular fetching of new donations, add the following cronjob to your crontab. Please adjust the placeholders as needed:

```cron
*/5 * * * * username /path/to/project/venv/bin/python /path/to/project/betterlyze/manage.py runcrons 
```