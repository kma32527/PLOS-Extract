from os import listdir
from os.path import isfile, join
import xml.etree.ElementTree as ET
import re

##------------------------------------------------------------------
## Gets plos data from a folder
## getplosdata(path) gets ALL valid articles from the file path
## getplosdata(path, n) gets the first n articles from the file path
def getplosdata(path, *args):
    allfiles = [''.join([path, f]) for f in listdir(path) if isfile(join(path, f))]
    if len(args)>0 and isinstance(args[0], int):
        allfiles=allfiles[:args[0]]
    articles=list()
    cleanarticles=list()
    for filename in allfiles:
        tree=ET.parse(filename)
        title, cleantitle=getcleantitle(tree)
        abstract, cleanabstract=getcleanabstract(tree)
        body, cleanbody=getcleanbody(tree)
        articles.append({'title' : title, 'abstract' : abstract, 'body' : body})
        cleanarticles.append({'title' : cleantitle, 'abstract': cleanabstract, 'body': cleanbody})
    return articles, cleanarticles
##----------------------------------------------------------------------------
##Removes formatting while maintaining readability
##Contractions have the apostrophe removed
def unformat(paper):
    if paper=='_none_':
        return paper
    paper=re.sub('b\'|b"', ' ', paper)
    paper=re.sub('n\'|n"', '', paper)
    paper=re.sub('\\\\t', ' ', paper)
    paper=re.sub('\\\\n', ' ', paper)
    paper=re.sub('\[[^\]\[]*\]', '', str(paper))
    paper=re.sub('<sub>', '_', paper)
    paper=re.sub('</sub>', '', paper)
    paper=re.sub('\\\\(\w){1,}', ' ', paper)
    paper=re.sub('\s{1,}', ' ', paper)
    paper=re.sub('<[^<>]*>', ' ', paper)
    paper=re.sub('\\\\', '', paper)
    paper=re.sub('\'', '', paper)
    paper=re.sub(' +', ' ', paper)
    paper=re.sub(' \. ', '. ', paper)
    paper=paper.strip()
    if len(paper)==0:
        paper='_none_'
    return paper

##Strips special characters from text and converts to lower case
def cleantext(paper):
    if paper=='_none_':
        return paper
    paper=unformat(paper)
    paper=re.sub('[(~%)\-/,=:;+``#:.]', ' ', paper)
    paper=re.sub(' +', ' ', paper)     
    paper=paper.lower().strip()          
    if len(paper)==0:
        paper='_none_'
    return paper
    
##Compiles all glossaries in a folder into a single glossary
##Note: Should look more closely at how repeat abbreviations are handled
def megaglossary(all_files):
    fullglossary={}
    for filepath in all_files:
        tree=ET.parse(filepath)
        glossary=getglossary(tree)
        for abbr in glossary:
            if not abbr in fullglossary:
                fullglossary[abbr]=glossary[abbr]
    return fullglossary

##Replaces abbreviations with the corresponding definition found in the glossary
def translatepaper(text, glossary):
    text=cleantext(text)
    tokens=nltk.word_tokenize(text)
    for i in range(len(tokens)-1, 0, -1):
        if tokens[i] in glossary:
            tokens[i]=glossary[tokens[i]]
    return re.sub('\s{1,}',' ', ' '.join(tokens))

##Returns the glossary of the article
def getglossary(tree):
    root=tree.getroot()
    terms=root.findall("./back/glossary/def-list/")
    glossary={}
    for term in terms:
        raw_entry=str(ET.tostring(term, encoding='utf-8', method='xml'))
        try:
            abbr=cleantext(re.search('<term>.*</term>', raw_entry).group())
            definition=cleantext(re.search("<def>.*</def>", raw_entry).group())
            abbr=re.sub(' ','', abbr)
            glossary[abbr.lower()]=definition
        except:
            print('yikes')
    return glossary

##Returns the title of the article
def extracttitle(tree):
    root=tree.getroot()
    title=str(ET.tostring(root.findall("./front//article-title")[0], encoding='utf-8', method='xml'))
    try:
        alt_title= str(ET.tostring(root.findall("./front//alt-title")[0], encoding='utf-8', method='xml'))
    except:
        alt_title=''
    return unformat(title), unformat(alt_title)

def gettitle(tree):
    title, alt_title=extracttitle(tree)
    if not alt_title=='_none_':
        title=title+ ' (' + unformat(alt_title) + ')'
    return title

##Finds abstract in the file
def extractabstract(tree):
    root=tree.getroot()
    abstracts=root.findall(".//abstract")
    abstract='';
    synopsis='';
    for section in abstracts:
        text=str(ET.tostring(section, encoding='utf-8', method='xml'))
        if 'abstract-type' in section.attrib:
            synopsis=text
        else:
            abstract=text
    abstract=re.sub('<title>.*</title>', '', " ".join([abstract, synopsis]))
    return abstract

##Returns the unformatted abstract from the article
def getabstract(tree):
    abstract=extractabstract(tree)
    abstract=unformat(abstract)
    return abstract

##Returns the unformatted body of the article
def extractbody(tree):
    root=tree.getroot()
    sections=root.findall("./body/")
    body=''
    for section in sections:
        paper=ET.tostring(section, encoding="utf-8", method="xml")
        body= body + ' ' + str(paper)
    return body

##Returns the unformatted body of the article
def getbody(tree):
    body=extractbody(tree)
    body=re.sub('<title>Introduction</title>|<title>Results</title>|<title>Discussion</title>', '', body)
    body=re.sub('<label>.*</label>', ' ', body)
    return unformat(body.strip())
    
##---------------------------------------------------
#Returns both the unformatted text and cleaned text
def unformatandclean(paper):
    paper=unformat(paper)
    if paper=='_none_':
        return '_none_', '_none_'
    cleanpaper=re.sub('[)~%(\-/,=:;+``#:.]', ' ', paper)
    cleanpaper=re.sub(' +', ' ', cleanpaper)
    cleanpaper=cleanpaper.lower().strip()
    return paper, cleanpaper

def getcleantitle(tree):
    title=gettitle(tree)
    return title, cleantext(title)

def getcleanabstract(tree):
    abstract=extractabstract(tree)
    abstract, cleanabstract=unformatandclean(abstract)
    return abstract, cleanabstract

def getcleanbody(tree):
    body=extractbody(tree)
    body=re.sub('<title>Introduction</title>|<title>Results</title>|<title>Discussion</title>', '', body)
    body=re.sub('<label>.*</label>', ' ', body)
    return unformatandclean(body)


##Tests---------------------------------------

#articles, cleanarticles=getplosdata('./someofplos/pcbi/', 50)
#print('Title:')
#print(articles[12]['title'])
#print('----------------------')
#print('Cleaned title: ')
#print(cleanarticles[12]['title'])
#print('----------------------')
#print('Abstract:')
#print(articles[12]['abstract'])
#print('Cleaned abstract: ')
#print(cleanarticles[12]['abstract'])


