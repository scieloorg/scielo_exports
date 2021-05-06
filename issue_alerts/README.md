# Issue Alerts

Produces HTML for issue alert service.

## For Windows Users (Windows10-64bits)
### How to use
- Download the .zip package [here](https://github.com/scieloorg/scielo_exports/raw/master/issue_alerts/dist/issue_alerts.zip)
- Rename the config.ini.template file to config.ini
- Configure the parameters
- Add one or more Issue IDs in the issue_list.txt
- Run issue_alerts.bat

## For Developer (for the maintenance of the code)
### Requirements
- elasticsearch==7.9.1
- Jinja2==2.11.3
- requests==2.24.0
- xylose==1.35.4
- PyInstaller==4.0 (to compile for Windows)
### Python version supported
- Python 3.4 through 3.7.
