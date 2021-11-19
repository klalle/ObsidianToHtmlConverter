import  os
from shutil import copyfile
import shutil
from pathlib import Path
import pathlib
import sys
import re

if(len(sys.argv)!=2 and len(sys.argv)!=3):
    print("Wrong number of arguments!\nUsage: python3 exportMdFileToHtml.py <filename.md> <[y/n](optional) y=default => creates a html-export in export vault>")
    quit()

mainFileToExport = ""
fileToFind = str(sys.argv[1])
for path in Path('.').rglob(fileToFind):
    mainFileToExport=path

exportToHtml = True
if(len(sys.argv) == 3 and str(sys.argv[2]).upper() == "N"):
    print("Exporting: " + str(mainFileToExport) + " to vault")
    exportToHtml = False
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

copyfile(mainFileToExport, destFile)
filesAllreadyCopied = [mainFileToExport]
if(exportToHtml):
    with open(os.path.join(exportDir,"index.html"), 'w') as outputfile:
        outputfile.write('<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta http-equiv="Refresh" content="0; url=\'./' + str(mainFileToExport) + '.html\'" />\n\t</head>\n</html>')

def findRelPath(linkPath, currentFile):
    #Hittar sökvägen relativt currentFile a la html
    pRoot = Path(".") #root
    pCurr = Path(currentFile)
    pLink = Path(linkPath)
    pCurrRelRoot = str(pCurr.relative_to(pRoot))
    pLinkRelRoot = str(pLink.relative_to(pRoot))
    pLinkRelRootList = pLinkRelRoot.split("/")
    for parent in pCurrRelRoot.split("/"):
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
        if(traverse and linkedFilePath not in filesAllreadyCopied): #förhindra cirkelreferens => oändlig loop
            filesAllreadyCopied.append(linkedFilePath)
            readFilesRecursive(linkedFilePath)
        return findRelPath(linkedFilePath,currentFile)

def findMdFile(line, currentFile, convertHtml=True):
    pattern = re.compile(r"(?<!!)\[\[([^\]]*)\]\]")
    for (file) in re.findall(pattern, line):
        file = file.split("#")[0] #om länk till överskrift
        #print("fil: " + file)
        newFile = copyFileToExport(file + '.md', currentFile, traverse=True) 
        if(convertHtml):
            if(len(newFile)>0):
                line = line.replace('[[' + file + ']]','<a href="./' + newFile + ".html" + '">' + newFile.split("/")[-1].replace(".md","") + '</a>')
            else: ##referar till sig själv
                line = line.replace('[[' + file + ']]', '<a href="./' + file + ".md.html" + '">' + file.split("/")[-1].replace(".md","") + '</a>')
    return line

def findImages(line, currentFile, convertHtml=True):
    antalAssets = 0
    pattern = re.compile(r"!\[\[([^\]]*)\]\]")
    for (asset) in re.findall(pattern, line):
        antalAssets += 1
        img = str(copyFileToExport(asset.split("|")[0], currentFile))
        if(convertHtml):
            style = 'border-radius: 4px;"'
            if('|' in asset):
                style = style + 'width:' + asset.split('|')[1] + 'px; border-radius: 3px;'
            line = line.replace("![[" + asset + "]]", '<img src="./' + img + '" alt="' + img.split("/")[-1] + '" style="' + style + '" >')
    return (line, antalAssets)

def findExternalLinks(line):
    pattern = re.compile(r"\[([^\[]*)\]\(([^\[\s]*)\)")

    for (text, link) in re.findall(pattern, line):
        line = line.replace("[" + text + "](" + link + ")",'<a href="' + link + '" target=”_blank”>' + text + "</a>")
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
            line = '<div class="codeblock"><xmp style="tab-size: 4;">' + line
        else:
            line = line + '</xmp></div>'
        InCodeBlock = not InCodeBlock
    return (line, InCodeBlock)

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
    pattern = re.compile(r"^([\t]*)[\- ]*([#]{1,})(.*)")
    
    for (tab, heading, text) in re.findall(pattern, line):
        line = '<h' + str(len(heading)) + ' style="margin-left:' + str(len(tab) * 20) + 'px;">' + text + '</h' + str(len(heading)) + '>\n'
    return line

def insertParagraphs(line):
    line = line.replace("\n","")
    if('<h' not in line and '</xmp>' not in line):
        line = "<p>" + line + "</p>"
    return line + "\n"

def readFilesRecursive(path):
    with open(path,"r") as readfile:
        data = readfile.readlines()

    antalAssets = 0
    
    if(exportToHtml):
        with open(os.path.join(exportDir,str(path) + ".html"), 'w') as outputfile:
            outputfile.write("<!DOCTYPE html>\n")
            outputfile.write("<html>\n")
            outputfile.write("<head>\n")
            outputfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
            outputfile.write("<style>\n")
            outputfile.write("\timg { max-width:900px; }\n")
            outputfile.write("\t.codeblock { \n\tbackground: #B0B0B0; padding:1px 10px 0px 10px; border-radius: 5px; overflow-x:auto; \n\t}\n")
            outputfile.write("\tcode {\n font-family: monospace; font-size: inherit; color: #202020; \n\t}\n")
            outputfile.write("</style>\n")
            outputfile.write("</head>\n")
            outputfile.write('<body style="background: #F0F0F0;">\n')
            outputfile.write('<div style="width:1000px; margin: 0 auto; padding:20px; text-align:left; background-color: #DCDCDC; border-radius: 5px;">\n')
            InCodeBlock = False
            for line in data:
                (line, InCodeBlock) = findCodeBlock(line, InCodeBlock)
                if(not InCodeBlock):
                    line = findMdFile(line, currentFile=path)
                    (line, a) = findImages(line, currentFile=path)
                    antalAssets += a
                    line = findExternalLinks(line)
                    line = findCheckboxes(line)
                    line = findBolds(line)
                    line = findHeadings(line)
                    line = findListItems(line)
                    line = insertParagraphs(line)
                outputfile.write(line)
            outputfile.write("</html>\n")
            outputfile.write("</body>\n")
    else:
        for line in data:
            findMdFile(line, currentFile=path, convertHtml=False)
            (line, a) = findImages(line, currentFile=path, convertHtml=False)
            antalAssets += a
    
    print("Exported: " + str(path) + (" (" + str(antalAssets) + " images)" if antalAssets>0 else ''))

readFilesRecursive(mainFileToExport)
print("Done!\n\nPath to export: " + str(exportDir) + ("/index.html" if exportToHtml else '' ))