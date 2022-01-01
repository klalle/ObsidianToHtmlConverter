import  os
from shutil import copyfile, copyfileobj
import shutil
from pathlib import Path
import pathlib
import sys
import re
import html
from urllib.parse import unquote
import urllib.request
from random import seed,random,randint



if(len(sys.argv)!=2 and len(sys.argv)!=3 and len(sys.argv)!=4):
    print("Wrong number of arguments!\nUsage: python3 exportMdFileToHtml.py <filename.md> <[y/n](optional) y=default => creates a html-export in export vault> <[y/n](optional) y=default => download extrernal images locally>")
    quit()

mainFileToExport = ""
fileToFind = str(sys.argv[1])
for path in Path('.').rglob(fileToFind):
    mainFileToExport=path

exportToHtml = True
downloadImages = True
if len(sys.argv) >= 3:
    if str(sys.argv[2]).upper() == "N":
        print("Exporting: " + str(mainFileToExport) + " to vault")
        exportToHtml = False
    if len(sys.argv) == 4 and str(sys.argv[3]).upper() == "N":
        downloadImages = False
else:
    print("Exporting: " + str(mainFileToExport) + " + creates a html-copy in vault")


if(mainFileToExport == ""):
    print("File not found!\nRun this script from the root of obsidian vault\nUsage: python3 exportMdFileToHtml.py <filename.md> <[y/n](optional) y=default => creates a html-export in export vault>")
    quit()

exportDir = os.path.expanduser('~/export_' + fileToFind.split('/')[-1].replace(".md",""))
print("Path to export vault: " + str(exportDir) + "\n")

if os.path.exists(exportDir) and os.path.isdir(exportDir):
    shutil.rmtree(exportDir)
destFile = os.path.join(exportDir,mainFileToExport)
Path(os.path.dirname(destFile)).mkdir(parents=True, exist_ok=True)
assetPath = os.path.join(exportDir,"downloaded_images","test")
Path(os.path.dirname(assetPath)).mkdir(parents=True, exist_ok=True)
copyfile(mainFileToExport, destFile)
filesAllreadyCopied = [mainFileToExport]


def findRelPath(linkPath, currentFile):
    #Find filepath rel currentFile a la html
    pRoot = Path(".") #root
    pCurr = Path(currentFile)
    pLink = Path(linkPath)
    pCurrRelRoot = str(pCurr.relative_to(pRoot))
    pLinkRelRoot = str(pLink.relative_to(pRoot))
    pLinkRelRootList = pLinkRelRoot.replace("\\","/").split("/")
    for parent in pCurrRelRoot.replace("\\","/").split("/"):
        if(parent == pLinkRelRootList[0]):
            del pLinkRelRootList[0]
        else:
            pLinkRelRootList.insert(0,"..")
    if(len(pLinkRelRootList)>0):
        del pLinkRelRootList[0]
    return '/'.join(pLinkRelRootList)

def copyFileToExport(fileToFind, currentFile, traverse=False):
    linkedFilePath=""
    for path in Path('.').rglob(fileToFind):
        linkedFilePath=path
    if(linkedFilePath != ""):
        destDir = os.path.join(exportDir,linkedFilePath)
        Path(os.path.dirname(destDir)).mkdir(parents=True, exist_ok=True)
        copyfile(linkedFilePath, destDir)
        if(traverse and linkedFilePath not in filesAllreadyCopied): #prevent circle ref
            filesAllreadyCopied.append(linkedFilePath)
            readFilesRecursive(linkedFilePath)
        return findRelPath(linkedFilePath,currentFile)

def findMdFile(line, currentFile):
    pattern = re.compile(r"(?<!!)\[\[([^\]]*)\]\]")
    for (file) in re.findall(pattern, line):
        fileOnly = file.split("#")[0] 
            
        ancor = ""
        if(len(file.split("#"))>1):
            ancor = "#" + file.split("#")[1].replace(" ","_").replace("(","").replace(")","")
        newFile = copyFileToExport(fileOnly + '.md', currentFile, traverse=True) 
        if(exportToHtml):
            if(newFile and len(newFile)>0):
                line = line.replace('[[' + file + ']]','<a href="./' + newFile + ".html" + ancor + '">' + newFile.replace("\\","/").split("/")[-1].replace(".md","") + ancor + '</a>')
            else: ##self ref
                line = line.replace('[[' + file + ']]', '<a href="./' + fileOnly + ".md.html" +  ancor + '">' + fileOnly.replace("\\","/").split("/")[-1].replace(".md","") + ancor + '</a>')
    return line

seed(1)
def findImages(line, currentFile):
    antalAssets = 0
    pattern = re.compile(r"!\[\[([^\]]*)\]\]")
    for (asset) in re.findall(pattern, line):
        antalAssets += 1
        img = str(copyFileToExport(asset.split("|")[0], currentFile))
        if(exportToHtml):
            style = 'border-radius: 4px;"'
            if('|' in asset):
                style = style + 'width:' + asset.split('|')[1] + 'px; border-radius: 3px;'
            line = line.replace("![[" + asset + "]]", '<img src="./' + img + '" alt="' + img.replace("\\","/").split("/")[-1] + '" style="' + style + '" >')
    
    pattern = re.compile(r"!\[(.*)\]\((.*)\)")
    for size,imglink in re.findall(pattern,line):
        antalAssets += 1
        if(exportToHtml):
            if("http" not in imglink):
                originallink = imglink
                imglink = str(copyFileToExport(unquote(imglink.replace("\\","/").split("/")[-1]), currentFile))
                
                style = 'border-radius: 4px;"'
                if('|' in imglink):
                    style = style + 'width:' + imglink.split('|')[1] + 'px; border-radius: 3px;'
                line = line.replace("![" + size + "](" + originallink + ")", '<img src="./' + imglink + '" alt="' + imglink.replace("\\","/").split("/")[-1] + '" style="' + style + '" >')
            elif downloadImages:
                imgname = 'utl_download_' + str(randint(0,10000)) + imglink.split("/")[-1]
                destFile = os.path.join(exportDir,"downloaded_images",imgname)
                with urllib.request.urlopen(imglink) as responese:
                    with open(destFile,'wb') as fdest:
                        copyfileobj(responese, fdest)
                
                style = 'border-radius: 4px;"'
                line = line.replace("![" + size + "](" + imglink + ")", '<img src="../downloaded_images/' + imgname + '" style="' + style + '" >')
            else:
                style = 'border-radius: 4px;"'
                line = line.replace("![" + size + "](" + imglink + ")", '<img src="' + imglink + '" style="' + style + '" >')
    
    
    return (line, antalAssets)

def findExternalLinks(line):
    pattern = re.compile(r"\[([^\[]*)\]\(([^\[\s]*)\)")

    for (text, link) in re.findall(pattern, line):
        line = line.replace("[" + text + "](" + link + ")",'<a href="' + link + '" target="_blank">' + text + "</a>")
    return line

def findLinkInText(line):
    pattern = re.compile(r"((?<!(?:\"|\(|\[))https{0,1}.*?)[ \n]") #?=>un-greedy, (?<!...) = negative look behind

    for (link) in re.findall(pattern, line):
        line = line.replace(link,'<a href="' + link.strip() + '" target="_blank">' + link + "</a>")
    
    return line

def findCheckboxes(line):
    pattern = re.compile(r"- \[[\sx]]")
    for (text) in re.findall(pattern, line):
        checked = ""
        if "x" in text:
            checked = "checked"
        line = line.replace(text,'<input type="checkbox"' + checked + "/>")
    return line

def findCodeBlock(line, InCodeBlock):
    if("```" in line):
        if(not InCodeBlock):
            line = '<pre class="codeblock"><code style="tab-size: 4;" class="' + line.split("```")[-1].replace("shell\n","sh").replace('\n',"") + ' codeblock">' + line.replace("```","")
        else:
            line = line.replace("```","") + '</pre></code>'
        InCodeBlock = not InCodeBlock
    return (line, InCodeBlock)

def findCommentBlock(line, InCommentBlock):
    pattern = re.compile(r"(%%.*%%)")
    for (inlineComment) in re.findall(pattern, line):
        line = line.replace(inlineComment,'')

    if "%%" in line:
        InCommentBlock = not InCommentBlock
        line = ''

    return (line, InCommentBlock)

def leftMargin(line):
    margin = 0
    for c in line:
        if(c.startswith('\t')):
            margin = margin + 20
    return margin

def findListItems(line):
    pattern = re.compile(r"^([\t]*)[\- ](.*)")
    
    for (tab, text) in re.findall(pattern, line):
        line = '<ul style="margin-left:' + str(len(tab) * 20) + 'px;"><li>' + text.strip() + '</li></ul>\n'
    return line


def findBolds(line):
    pattern = re.compile(r"\*\*([^\*]*)\*\*")
    for (text) in re.findall(pattern, line):
        line = line.replace("**" + text + "**", '<b>' + text + '</b>')
    return line

def findHeadings(line):
    pattern = re.compile(r"^([\t]*)[\- ]*([#]{1,}) ([^<]{1,})")
    linkHeading = re.compile(r"^([\t]*)[\- ]*([#]{1,}) (<a href.*>([^\/]*)<\/a>)(.*)")
    
    for (tab, heading, link, text, aftertext) in re.findall(linkHeading, line):
        line = '<h' + str(len(heading)) + ' style="margin-left:' + str(len(tab) * 20) + 'px;" id="' + (
            (text + aftertext).strip().replace(" ","_").replace("(","").replace(")","").replace("#","_") + '">' 
            + link + aftertext + '</h' + str(len(heading)) + '>\n')

    for (tab, heading, text) in re.findall(pattern, line):
        line = '<h' + str(len(heading)) + ' style="margin-left:' + str(len(tab) * 20) + 'px;" id="' + text.strip().replace(" ","_").replace("(","").replace(")","")  + '">' + text + '</h' + str(len(heading)) + '>\n'
    return line




def findInlineCodeBlocks(line):
    pattern = re.compile(r"`([^`]*)`")
    for (text) in re.findall(pattern, line):
        line = line.replace('`' + text + '`', '<code class="inlineCoed">' + html.escape(text) + '</code>')
    return line

def findInlineCodeBlockswrongly(line):
    pattern = re.compile(r"```([^`]*)```")
    for (text) in re.findall(pattern, line):
        line = line.replace('```' + text + '```', '<code class="inlineCoed">' + html.escape(text) + '</code>')
    return line
def insertParagraphs(line):
    line = line.replace("\n","")
    if('<h' not in line and '</pre></code>' not in line):
        line = "<p>" + line + "</p>"
    return line + "\n"

def findLines(line):
    if  '---' in line:
        line = "<hr>"
    return line + "\n"


def readFilesRecursive(path):
    with open(path,"r",encoding='utf-8') as readfile:
        data = readfile.readlines()

    antalAssets = 0
    
    if(exportToHtml):
        with open(os.path.join(exportDir,str(path) + ".html"), 'w', encoding='utf-8') as outputfile:
            outputfile.write("<!DOCTYPE html>\n")
            outputfile.write("<html>\n")
            outputfile.write("<head>\n")
            outputfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
            
            #code-highlighting with highlight.js:
            outputfile.write('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/styles/default.min.css">\n')
            outputfile.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/highlight.min.js"></script>\n')
            outputfile.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/languages/go.min.js"></script>\n')
            outputfile.write('<script>hljs.initHighlightingOnLoad();</script>\n')
            
            outputfile.write("<style>\n")
            outputfile.write("\timg { max-width:900px; }\n")
            outputfile.write("\t.codeblock { \n\tbackground: #B0B0B0; padding:1px 10px 0px 10px; border-radius: 5px; overflow-x:auto; \n\t}\n")
            outputfile.write("\tcode {\n font-family: monospace; font-size: inherit; color: #202020; \n\t}\n")
            outputfile.write("\t.inlineCoed {\n font-family: monospace; font-size: inherit; color: #202020; \n\t}\n")
            outputfile.write("</style>\n")
            outputfile.write("</head>\n")
            
            outputfile.write('<body style="background: #F0F0F0;">\n')
            outputfile.write('<div style="margin: 0 auto; width:1380px;  position: relative;" >\n')
            
            outputfile.write('<div style="width:1000px; padding:20px; margin:0px; z-index: 5; text-align:left; background-color: #DCDCDC; border-radius: 5px; position:absolute; top:0; left:340px;">\n')
            InCodeBlock = False
            InComment = False
            for line in data:
                if(not InCodeBlock):
                    line = findInlineCodeBlockswrongly(line)

                (line, InCodeBlock) = findCodeBlock(line, InCodeBlock)
                
                if(not InCodeBlock):
                    if InComment:
                        (line, InComment) = findCommentBlock(line, InComment)
                        line=''
                    else:
                        (line, InComment) = findCommentBlock(line, InComment)
                        if(InComment):
                            continue
                        line = findLines(line)
                        line = findMdFile(line, currentFile=path)
                        (line, a) = findImages(line, currentFile=path)
                        antalAssets += a
                        line = findInlineCodeBlocks(line)
                        line = findLinkInText(line)
                        line = findExternalLinks(line)
                        line = findCheckboxes(line)
                        line = findBolds(line)
                        line = findHeadings(line)
                        line = findListItems(line)
                        line = insertParagraphs(line)
                        
                    
                elif("<code" not in line):
                    line = html.escape(line)
                outputfile.write(line)
            outputfile.write("</div>\n")
            b = str(findRelPath(".",path))
            outputfile.write('<div style="width:345px; padding-top: 20px;; position:absolute; top:0; left:0; overflow:auto;">\n')
            outputfile.write('\t<iframe src="' + str(findRelPath(".",path))[:-1] + 'treeview.html" width="340px" frameBorder="0" height="900px"></iframe>\n')
            outputfile.write("</div>\n")

            outputfile.write("</div>\n")
            outputfile.write("</body>\n")
            outputfile.write("</html>\n")

    else:
        for line in data:
            findMdFile(line, currentFile=path)
            (line, a) = findImages(line, currentFile=path)
            antalAssets += a
    
    print("Exported: " + str(path) + (" (" + str(antalAssets) + " images)" if antalAssets>0 else ''))

readFilesRecursive(mainFileToExport)
if(exportToHtml):
    with open(os.path.join(exportDir,"index.html"), 'w') as outputfile:
        outputfile.write('<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta http-equiv="Refresh" content="0; url=\'./' + str(mainFileToExport) + '.html\'" />\n\t</head>\n</html>')
    
    with open(os.path.join(exportDir,"treeview.html"), 'w') as outputfile:
        outputfile.write("<!DOCTYPE html>\n")
        outputfile.write("<html>\n")
        outputfile.write("<head>\n")
        outputfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
        
        outputfile.write("<head>\n")
        outputfile.write('<base target="_parent">\n')
        outputfile.write("<style>\n")
        outputfile.write('ul{ padding-left: 5px; margin-left: 15px; list-style-type: "- "; }\n')
        outputfile.write(".folderClass {list-style-type: disc;}\n")
        outputfile.write("</style>\n")
        outputfile.write("</head>\n")
        
        outputfile.write('<body style="background: #F0F0F0; ">\n')
        filesAllreadyCopied.sort()
        outputfile.write("<ul>")
        for f in str(filesAllreadyCopied[0]).replace("\\","/").split("/"):
            if('.md' in f):
                outputfile.write('<li>' + '<a href="./' + str(filesAllreadyCopied[0]) + ".html" + '">' + str(f).replace(".md","") + '</a>' + '</li>\n')
            else:
                outputfile.write('<li class="folderClass">' + str(f) + "</li>")
                outputfile.write("<ul>")
        lastFilePath = str(filesAllreadyCopied[0]).replace("\\","/").split("/")
        first = True
        for currFile in filesAllreadyCopied:
            if(not first):
                for currFolder in str(currFile).replace("\\","/").split("/"):
                    if(len(lastFilePath) > 0 and currFolder == lastFilePath[0]):
                        del lastFilePath[0]
                    else:
                        for addedSublist in lastFilePath[:-1]: #close previous lists
                            outputfile.write("</ul>\n")
                        lastFilePath = ""
                        if('.md' in currFolder):
                            outputfile.write('<li>' + '<a href="./' + str(currFile) + ".html" + '">' + str(currFolder).replace(".md","") + '</a>' + '</li>\n')
                        else:
                            outputfile.write('<li class="folderClass">' + str(currFolder) + "</li>\n")
                            outputfile.write("<ul>\n")
                lastFilePath = str(currFile).replace("\\","/").split("/")
            first = False

        for i in str(filesAllreadyCopied[-1]).replace("\\","/").split("/"):
            outputfile.write("</ul>")
       
        outputfile.write("</body>\n")
        outputfile.write("</html>\n")
print("Done!\n\nPath to export: " + str(exportDir) + ("/index.html" if exportToHtml else '' ))
