import configparser
import datetime
import logging
import os
import sys

import requests
from bs4 import BeautifulSoup
from bs4 import Comment
from jinja2 import Environment, FileSystemLoader, Template


# Check and create logs directorycd pro
if not os.path.exists('logs'):
    os.mkdir('logs')

logging.basicConfig(filename='logs/issue_alerts.info.txt', level=logging.INFO)
logger = logging.getLogger(__name__)

# Format ISO date
dateiso = datetime.datetime.now().strftime('%Y%m%d')

# Config
config = configparser.ConfigParser()
config._interpolation = configparser.ExtendedInterpolation()
config.read('config.ini')

# Invalid Sections
invalid_sec = config['invalid_sec']['sections'].encode('latin-1').decode('utf-8').split(', ')
invalid_sec = invalid_sec + [s.upper() for s in invalid_sec]

# Domain
domain = 'https://www.scielo.br'

# Set Language EN from WebSite in new Session
try:
    print('Starting a website session...')
    s = requests.Session()
    s.get("https://www.scielo.br/set_locale/en/")
except Exception as e:
    print(e)
    sys.exit()
    

def leave(e=None):
    if e:
        print(e)
    i = input("\nPress a key to exit... ")
    if i != '':
        sys.exit()


def getdocs(urli, articles):
    # Get Issue page
    # urli = "https://www.scielo.br/j/ean/i/2021.v25n1/"
    # urla = "https://www.scielo.br/j/pg/a/HrVWp3P85qGksXDqQM9ZdSx/?lang=de"

    # Issue
    if urli and urli != None:
        
        r = s.get(urli, cookies=s.cookies)
        soup = BeautifulSoup(r.content, "html.parser")
        docs = soup.find_all("td", {"class":"pt-4"})
        
        print('Total documents: %s\n' % (len(docs)))

        return docs
    
    # Articles
    if articles and articles != None:
        
        docsa = []
        lurli = None

        for urla in articles:
            # get issue page
            pidv3 = urla.split('/')[6]
            r = s.get(urla, cookies=s.cookies)
            soup = BeautifulSoup(r.content, "html.parser")
            tc = soup.find_all("a", {"class":"btn mb-0"})[0]['href']
            urli = domain + tc
            
            # access Table of contents of the article
            if urli != lurli:
                r = s.get(urli, cookies=s.cookies)
                soup = BeautifulSoup(r.content, "html.parser")
                docsi = soup.find_all("td", {"class":"pt-4"})
                
            # insert 1 doc in docs list
            for doc in docsi:
                for link in doc.find_all("a", {"class":"text-uppercase"}):
                    if pidv3 in link.attrs['href']:
                        docsa.append(doc)
                        break
            
            # preserves urli
            lurli = urli
        
        if docsa:
            print('Total documents: %s\n' % (len(docsa)))
            
            return docsa


def json2html(htmlout, config, urli=None, articles=None):

    # Write the HTML file
    with open(htmlout, encoding='utf-8', mode='w') as f:
        # Start HTML output
        f.write(u'<html>\n<body>\n')

        # JINJA
        jinja_env = Environment(loader=FileSystemLoader('template'))
        template = jinja_env.get_template('body.html')

        # First section only
        previous_sec = None
        section = None

        # Get a list of docs from Issue or a Article
        docs = getdocs(urli, articles)

        for doc in docs:

            # SECTION
            try:
                # previous_sec = doc.find("span", {"class":"badge"}).text
                section = doc.find("span", {"class":"badge"}).text.upper()
            except:
                # previous_sec = "ORIGINAL ARTICLE"
                section = "ORIGINAL ARTICLE"

            if section:
                if section != previous_sec and section.upper() not in invalid_sec:
                    print('\n' + section)
                    tsec = Template("<p><strong>{{ section }}</strong></p>\n\n")
                    outsec = tsec.render(section=section)
                    f.write(outsec)
                    previous_sec = section
                      
                if section.upper() not in invalid_sec:
                    # Title
                    title_html = None
                    title = None

                    # Scraping HTML
                    title_html = doc.find("strong", {"class":"d-block mt-2"})
                    title_html.attrs.clear()
                    title = title_html.text
                    
                    # PID v2
                    # comments = doc.find_all(string=lambda text: isinstance(text, Comment))
                    # pid = [c.split(':')[1].strip() for c in comments if 'PID' in c][0]
                    
                    # show PID v2 title to user
                    # if title_html:
                    #     title = title_html.text
                    #     print(pid, title.strip()[0:60])

                    # Authors
                    authors = []
                    authors = [au.text for au in doc.find_all("a", {"class":"me-2"})]

                    # Link text in english
                    link_text = {
                            'en': ('text in English', 'English'),
                            'pt': ('text in Portuguese', 'Portuguese'),
                            'es': ('text in Spanish', 'Spanish'),
                            'fr': ('text in French', 'French'),
                            'it': ('text in Italian', 'Italian'),
                            'de': ('text in German', 'German'),
                            'ru': ('text in Russian', 'Russian'),
                            }
                    
                    # ALL Links
                    all_links = [link.attrs['href'] for link in doc.find_all("a", {"class":"text-uppercase"})]

                    # PID v3
                    for a in all_links:
                        if 'format=pdf' in a:
                            pidv3 = a.split('/')[4]
                            break
                    
                    # show PID v3 title to user   
                    print(pidv3, title.strip()[0:60])
                    
                    # Text Links
                    ltxt = []
                    for a in all_links:
                        if 'abstract' not in a and 'format=pdf' not in a:
                            l = a[-2:]
                            utxt = '%s%s' % (domain, a)
                            # print(utxt)
                            ltxt.append((link_text[l][0], link_text[l][1], utxt))
                    
                    # PDF Links
                    lpdf = []
                    for a in all_links:
                        if 'format=pdf' in a:
                            l = a[-2:]
                            updf = '%s%s%s' % (domain, a[:-2], l)
                            # print(updf)
                            lpdf.append((link_text[l][1], updf))

                    # Render HTML
                    output = template.render(
                        title=title_html, authors=authors, lpdf=lpdf, ltxt=ltxt)
                    
                    f.write(output)

        # Terminate HTML output
        f.write(u'</body>\n</html>')
        f.close()


def main():
    
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

    # ISSUE or ARTICLE List
    with open(config['paths']['issuelistname']) as f:
        urllist = [line.strip() for line in f]
    f.close()

    issues = []
    for url in urllist:
        if url.split('/')[5] == 'i':
            issues.append(url)

    articles = []
    for url in urllist:
        if url.split('/')[5] == 'a':
            articles.append(url)

    if issues:
        for url in issues:
            issue = url.split('/')[4]+'_'+url.split('/')[6]
            htmlout = ('%s/%s_%s.html' % (htmlfolder, htmlfilename, issue))
            print('\nfolder/htmlfile: %s\n' % htmlout)
            
            # Build HTML object
            print(url)
            json2html(htmlout=htmlout, config=config, urli=url, articles=None)

    if articles:
        # for url in articles:
        acron = articles[0].split('/')[4]
        htmlout = ('%s/%s_%s_articles.html' % (htmlfolder, htmlfilename, acron))
        print('\nfolder/htmlfile: %s\n' % htmlout)
        
        # Build HTML object
        json2html(htmlout=htmlout, config=config, urli=None, articles=articles)

    # End of operations
    leave()

if __name__ == "__main__":
    main()
