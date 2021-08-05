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
    i = input("\nPress a key to exit... ")
    if i != '':
        sys.exit()


def getpidcode(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        # get PIDs
        pidscomm = soup.find_all(string=lambda text: isinstance(text, Comment) and 'PID:' in text)
        pids = [pid.strip(' PID: ') for pid in pidscomm]
        # get Codes (new PID) and Prefix
        if url.split('/')[5] == 'a':
            # is article
            codes = [url.split('/a/')[1].split('/')[0]]
            prefix = [url.split('/a/')[0] for p in range(len(pids))]
        else:
            # is issue
            arts = soup.find_all("li", attrs={"data-date":True})
            codes = [art.find_all('a')[-1].attrs['href'].split('/')[4] for art in arts]
            prefix = [url.split('/i/')[0] for p in range(len(pids))]

        # zip Prefix, Codes and PIDs
        pidscodelist = list(zip(prefix, codes, pids))

        return pidscodelist

    except Exception as e:
        print(e)
        leave()


def json2html(htmlout, config, urli=None, articles=None):

    if urli:
        pid_code_list = getpidcode(urli)

    if articles:
        for urla in articles:
            pid_code_list = [getpidcode(urla)[0] for urla in articles]

    print('Total documents: %s\n' % (len(pid_code_list)))

    # Write the html file
    with open(htmlout, encoding='utf-8', mode='w') as f:

        # Start HTML output
        f.write(u'<html>\n<body>\n')

        issue_pid = pid_code_list[0][2][1:18]
        # Request Issue
        # http://articlemeta.scielo.org/api/v1/issue/?code=0104-070720190001
        uissue = config['articlemeta']['host']+'/api/v1/issue/?code=%s' % issue_pid
        logger.info(uissue)

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
                if 'Errata' not in sec[1].values() or 'Erratum' not in sec[1].values():
                    seccode_list.append(sec[0])

        # JINJA
        jinja_env = Environment(loader=FileSystemLoader('template'))
        template = jinja_env.get_template('body.html')

        previous_sec = None
        for prefix, code, pid in pid_code_list:
            # logger.info(pid, code)
            # Request Article
            uart = config['articlemeta']['host']+"/api/v1/article/?code=%s" % pid
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

            if xart.section_code and xart.section_code in seccode_list:
                # Language priority to HTML
                lang_priority = ['en', 'pt', 'es']
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
                authors = []
                if xart.authors:
                    authors = [au['surname']+', '+au['given_names'] for au in xart.authors]

                # Link text in english
                link_text = {
                        'en': ('text in English', 'English'),
                        'pt': ('text in Portugues', 'Portuguese'),
                        'es': ('text in Spanish', 'Spanish')
                }

                # Links to full text (URL)
                ltxt = None
                if xart.fulltexts() != None:
                    ltxt = []
                    if 'html' in xart.fulltexts().keys():
                        for l in xart.languages():
                            if l in xart.fulltexts()['html']:
                                utxt = '%s/a/%s/?lang=%s' % (prefix, code, l)
                                ltxt.append(
                                    (link_text[l][0],
                                     link_text[l][1],
                                     utxt))

                # PDF Links
                lpdf = None
                if xart.fulltexts() != None:
                    lpdf = []
                    if 'pdf' in xart.fulltexts().keys():
                        for l in xart.languages():
                            updf = '%s/a/%s/?format=pdf&lang=%s' % (prefix, code, l)
                            lpdf.append((link_text[l][1], updf))

                # Render HTML
                output = template.render(
                    title=title, authors=authors, lpdf=lpdf, ltxt=ltxt)
                f.write(output)

        # Terminate HTML output
        f.write(u'</body>\n</html>')


def main():
    # Format ISO date
    dateiso = datetime.datetime.now().strftime('%Y%m%d')

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

    # Check and create html folder output
    if not os.path.exists(htmlfolder):
        os.mkdir(htmlfolder)

    # ISSUE or Article List
    with open(config['paths']['issuelistname']) as f:
        urllist = [line.strip() for line in f]
    f.close()

    articles = []
    for url in urllist:
        if url.split('/')[5] == 'a':
            articles.append(url)

    issues = []
    for url in urllist:
        if url.split('/')[5] == 'i':
            issues.append(url)

    if issues:
        for urli in issues:
            issue = urli.split('/')[4]+'_'+urli.split('/')[6]
            htmlout = ('%s/%s_%s.html' % (htmlfolder, htmlfilename, issue))
            logger.info('issue: %s' % issue)
            print('\nfolder/htmlfile: %s\n' % htmlout)
            # Build HTML object
            json2html(htmlout=htmlout, config=config, urli=urli, articles=None)

    if articles:
        htmlout = ('%s/%s_%s.html' % (htmlfolder, htmlfilename, '_articles'))
        print('\nfolder/htmlfile: %s\n' % htmlout)
        # Build HTML object
        json2html(htmlout=htmlout, config=config, urli=None, articles=articles)

    # End of operations
    leave()

if __name__ == "__main__":
    main()
