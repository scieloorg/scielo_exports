# Issue Alerts

Produces HTML for issue alert service.

## For Windows Users (Windows10-64bits)
### How to use
- Download the .zip package [here](https://github.com/scieloorg/scielo_exports/raw/master/issue_alerts/dist/issue_alerts.zip)
- Rename the config.ini.template file to config.ini
- Configure the parameters
- Add one or more Issue or Article URL in the issue_list.txt
- Run issue_alerts.bat

## For Developer (for the maintenance of the code)
### Requirements
- beautifulsoup4==4.13.3
- Jinja2==3.1.5
- requests==2.32.2
- xylose==1.35.11
- PyInstaller==6.10.0  (to compile for Windows)

### Python version supported
- Python 3.4 through 3.13.0
