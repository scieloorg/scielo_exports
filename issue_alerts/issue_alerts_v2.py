# coding: utf-8
import configparser
import datetime
import json
import logging
import os
import sys

import requests
from bs4 import BeautifulSoup
from bs4 import Comment
from jinja2 import Environment, FileSystemLoader, Template
from xylose.scielodocument import Article, Issue


# Check and create logs directorycd pro
if not os.path.exists('logs'):
    os.mkdir('logs')

logging.basicConfig(filename='logs/issue_alerts.info.txt', level=logging.INFO)
logger = logging.getLogger(__name__)


def leave():
    i = None
    i = input("\nPress a key to exit... ")
    if i != None:
        sys.exit()


def getpidlist(urli):
    r = requests.get(urli)
    soup = BeautifulSoup(r.content, "html.parser")
    pidscomm = soup.find_all(string=lambda text: isinstance(text, Comment) and 'PID:' in text)
    pidlist = [pid.strip(' PID: ') for pid in pidscomm]
    print('Total de documentos no fasciculo: %s' % (len(pidlist)))
    return pidlist


# def json2html(htmlout, config, issue):
def json2html(htmlout, config, urli):

    issue_pids = getpidlist(urli)
    issue = issue_pids[0][1:18]

    # Write the html file
    with open(htmlout, encoding='utf-8', mode='w') as f:

        # Start HTML output
        f.write(u'<html>\n<body>\n')

        # Request Issue
        # http://articlemeta.scielo.org/api/v1/issue/?code=0104-070720190001
        uissue = config['articlemeta']['host'] + \
            '/api/v1/issue/?code=%s&collection=scl' % issue
        logger.info(uissue)
        print(uissue)

        xissue = None
        while xissue is None:
            try:
                rissue = requests.get(uissue)
                xissue = Issue(rissue.json())
            except requests.exceptions.Timeout:
                logger.info('error: %s' % e)
                print("Timeout - Try again")
                logger.info("Timeout - Try again")
                leave()
            except requests.exceptions.RequestException as e:
                logger.info('error: %s' % e)
                print("Request Error - Check your connection and try again")
                logger.info(
                    "Request Error - Check your connection and try again")
                leave()
            except json.decoder.JSONDecodeError as e:
                logger.info('error: %s' % e)
                print("Request Error - Try again")
                logger.info("Request Error - Try again")
                leave()

        # Invalid Sections
        notsec = ['Errata', 'Erratum', 'Presentation', 'Apresentação']
        # Valid Codes list
        seccode_list = []

        if xissue.sections != None:
            for sec in list(xissue.sections.items()):
                # print(sec)
                if 'Errata' in sec[1].values() or 'Erratum' in sec[1].values():
                    pass
                else:
                    seccode_list.append(sec[0])

        # JINJA
        jinja_env = Environment(loader=FileSystemLoader('template'))
        template = jinja_env.get_template('body.html')

        previous_sec = None
        for pid in issue_pids:
            logger.info(pid)
            # Request Article
            uart = config['articlemeta']['host'] + \
                "/api/v1/article/?code=%s&collection=scl" % pid
            xart = None
            while xart is None:
                try:
                    rart = requests.get(uart)
                    xart = Article(rart.json())
                except requests.exceptions.Timeout:
                    logger.info('error: %s' % e)
                    print("Timeout - Try again")
                    logger.info("Timeout - Try again")
                    leave()
                except requests.exceptions.RequestException as e:
                    logger.info('error: %s' % e)
                    print("Request Error - Check your connection and try again")
                    logger.info(
                        "Request Error - Check your connection and try again")
                    leave()
                except json.decoder.JSONDecodeError as e:
                    logger.info('error: %s' % e)
                    print("Request Error - Try again")
                    logger.info("Request Error - Try again")
                    leave()

            # Language priority to HTML
            lang_priority = ['en', 'pt', 'es']

            if xart.section_code and xart.section_code in seccode_list:
                # Sets the language of the template
                for l in lang_priority:
                    if l in xart.languages():
                        lang = l
                        break

                # First section only
                if 'en' in xissue.sections[xart.section_code].keys():
                    section = xissue.sections[xart.section_code]['en'].upper()
                    if previous_sec != section:
                        print(section)
                        tsec = Template("<p><strong>{{ section }}</strong></p>\n\n")
                        outsec = tsec.render(section=section)
                        f.write(outsec)
                        previous_sec = section
                else:
                    if lang in xissue.sections[xart.section_code].keys():
                        section = section = xissue.sections[xart.section_code][lang].upper()
                        print(section)
                        tsec = Template("<p><strong>{{ section }}</strong></p>\n\n")
                        outsec = tsec.render(section=section)
                        f.write(outsec)
                        previous_sec = section

                # Article metadata
                try:
                    print(pid, xart.original_title()[0:60])
                except Exception as e:
                    print('Error: %s' % e)
                    leave()

                # Title
                title_html = None
                title = None

                ## HTML title
                try:
                    r = requests.get("https://www.scielo.br/scielo.php?script=sci_arttext&pid="+pid+"&tlng=en")
                    soup = BeautifulSoup(r.content, 'html.parser')
                    arttitle = soup.find("h1", {"class":"article-title"})
                    arttitle.attrs.clear()
                    arttitle.find_all('span')[0].replaceWithChildren()
                    arttitle.find_all('span')[0].replaceWithChildren()
                    arttitle.find_all('a')[0].replaceWithChildren()
                    arttitle.name = 'strong'
                    if arttitle:
                        title_html = arttitle
                except requests.exceptions.Timeout:
                    logger.info('error: %s' % e)
                    print("Timeout - Try again")
                    logger.info("Timeout - Try again")
                    leave()



                ## HTML title or original_title
                if title_html:
                    title = title_html
                elif xart.original_language() == lang:
                    title = xart.original_title()
                elif lang in xart.translated_titles().keys():
                    title = xart.translated_titles()[lang]
                else:
                    title = xart.original_title()

                # Authors
                authors = [au['surname']+', '+au['given_names']
                           for au in xart.authors]

                # Label traductions
                labelst = {
                    'en': {
                        'en': ('abstract in English', 'text in English', 'English'),
                        'pt': ('abstract in Portuguese', 'text in Portugues', 'Portuguese'),
                        'es': ('abstract in Spanish', 'text in Spanish', 'Spanish')},
                    'pt': {
                        'en': ('resumo em Inglês', 'texto em Inglês', 'Inglês'),
                        'pt': ('resumo em Português', 'texto em Português', 'Português'),
                        'es': ('resumo em Espanhol', 'texto em Espanhol', 'Espanhol')},
                    'es': {
                        'en': ('resumen en Inglés', 'texto en Inglés', 'Inglés'),
                        'pt': ('resumen en Portugués', 'texto en Portugués', 'Portugués'),
                        'es': ('resumen en Español', 'texto en Español', 'Español')}
                }

                # Text Links
                ltxt = None
                if xart.fulltexts() != None:
                    ltxt = []
                    if 'html' in xart.fulltexts().keys():
                        for l in xart.languages():
                            if l in xart.fulltexts()['html']:
                                utxt = xart.fulltexts()['html'][l]
                                ltxt.append(
                                    (labelst[lang][l][1],
                                     labelst[lang][l][2],
                                     utxt))

                # PDF Links
                lpdf = None
                print(xart.fulltexts())
                if xart.fulltexts() != None:
                    lpdf = []
                    if 'pdf' in xart.fulltexts().keys():
                        for l in xart.languages():
                            updf = xart.fulltexts()['pdf'][l]
                            lpdf.append((labelst[lang][l][2], updf))
                        print(lpdf)

                # Render HTML
                output = template.render(
                    title=title, authors=authors, lpdf=lpdf, ltxt=ltxt)
                f.write(output)

        # Terminate HTML output
        f.write(u'</body>\n</html>')


def main():
    # Format ISO date
    dateiso = datetime.datetime.now().strftime('%Y%m%d')
    print(dateiso)

    # Config
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read('config.ini')

    # Folder and file names
    if config['paths']['issuelistname'] == '':
        print('issuelistname = empty.\nEnter a name for the issue list in config.ini.')
        leave()

    htmlfilename = config['paths']['htmlfilename']

    htmlfolder = config['paths']['htmlfoldername']

    if config['paths']['prefix'] == 'yes':
        if config['paths']['htmlfilename'] == '':
            htmlfilename = dateiso
        else:
            htmlfilename = ('%s_%s' % (dateiso, htmlfilename))

    if config['paths']['prefix'] == 'no':
        if config['paths']['htmlfilename'] == '':
            print('htmlfilename = empty.\nEnter a name in config.ini.')
            leave()

    if config['paths']['prefix'] == '':
        if config['paths']['htmlfilename'] == '':
            print('htmlfilename = empty.\nEnter a name in config.ini.')
            leave()

    # ISSUE List
    with open(config['paths']['issuelistname']) as f:
        issuelist = [line.strip() for line in f]
        print(issuelist)
    f.close()

    # for issue in issuelist:
    for urli in issuelist:
        issue = urli.split('/')[4]+urli.split('/')[6]
        logger.info('issue: %s' % issue)
        print('\nissue: %s' % issue)
        htmlout = ('%s/%s_%s.html' % (htmlfolder, htmlfilename, issue))


        print('\nfolder/htmlfile: %s\n' % htmlout)

        # Check and create html folder output
        if not os.path.exists(htmlfolder):
            os.mkdir(htmlfolder)

        # Build HTML object
        # json2html(htmlout=htmlout, config=config, issue=issue)
        json2html(htmlout=htmlout, config=config, urli=urli)

    # End of operations
    leave()


if __name__ == "__main__":
    main()