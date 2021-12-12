import requests
import bs4
import pdf2image
import os
import glob
import json
import platform

if platform.system() == 'Windows':
    import win32com.client #pywin32

class Circolari:

    def __init__(self, archiveDir=None):
        self.__pageTemplate__ = 'https://www.itispaleocapa.edu.it/circolari/page/'

        if archiveDir is not None:
            self.__archiveDir__ = archiveDir

            if not os.path.exists(archiveDir):
                os.mkdir(archiveDir)

            if os.path.exists(archiveDir + '/archive.json'):
                with open(archiveDir + '/archive.json') as file:
                    self.__archive__ = json.load(file)

            else:
                self.__archive__ = {'dir': archiveDir}

        else:
            self.__archiveDir__ = None
            self.__archive__ = None

    def __saveArchive__(self):
        with open(self.__archiveDir__ + '/archive.json', 'w') as file:
            file.write(json.dumps(self.__archive__, indent=4, sort_keys=True))

    def getPages(self, no, _range=True):
        circolariList = list()
        no = int(no)

        if no < 1:
            return []
        

        if _range:
            pList = range(no)

        else:
            pList = [no-1]

        for i in pList:
            x = requests.get(self.__pageTemplate__ + str(i + 1)).text
            soup = bs4.BeautifulSoup(x, 'html.parser')
            tags = soup.find_all(class_='post-box-archive')

            for circolare in tags:
                aTag = circolare.find_all('a')[1]
                cURL = aTag['href']
                cNo = [value for value in [i for o in [value.replace('/', '').split(' ') for value in aTag.text.lower().replace('bis', '').replace('ter', '').replace('-', '').split('.')] for i in o] if value.isnumeric()][0]
                
                while True:
                    if cNo.startswith('0'):
                        cNo = cNo[1:]

                    else:
                        break

                if 'bis' in aTag.text.lower():
                    cNo = cNo + ' bis'

                elif 'ter' in aTag.text.lower():
                    cNo = cNo + ' ter'

                cDate = circolare.find_all(class_='hdate')[0].text
                dMAE = circolare.find(class_='members-access-error')
                
                if dMAE:
                    cRestricted = True
                    cTitle = dMAE.text

                else:
                    cRestricted = False
                    cTitle = circolare.find('p').text

                circolariList.append(self.Circolare(cNo, cTitle, cDate, cURL, cRestricted, self.__archiveDir__, self.__archive__))

        if self.__archive__ is not None:
            for value in circolariList:
                if value.number not in self.__archive__:
                    self.__archive__[value.number] = {
                        'name': value.name,
                        'date': value.date,
                        'url': value.url,
                        'restricted': value.restricted
                    }

            self.__saveArchive__()

        return circolariList

    def get(self, no, _timeout=5):
        no = str(no)
        noN = int(no.split(' ')[0])

        if self.__archive__ is not None:
            if no in self.__archive__:
                return self.Circolare(no, self.__archive__[no]['name'], self.__archive__[no]['date'], self.__archive__[no]['url'], self.__archive__[no]['restricted'], self.__archiveDir__, self.__archive__)

        if noN < 1:
            return 'Inesistente'

        cList = self.getPages(1, _range=False)
        cNos = [value.number for value in cList]

        if no in cNos:
            return [value for value in cList if value.number == no][0]

        iterations = 0
        page = 1

        while True:
            cNoN = [int(value.split(' ')[0]) for value in cNos]
            last = cNoN[0]
            first = cNoN[-1]

            if first < noN and last > first:
                return 'Inesistente'

            if noN > last:
                return 'Inesistente'

            page = page + int((last - noN) / 10)

            if str(noN) + ' bis' in cNos and not str(noN) in cNos:
                page = page + 1
            
            cList = self.getPages(page, _range=False)
            cNos = [value.number for value in cList]

            if no in cNos:
                return [value for value in cList if value.number == no][0]

            iterations = iterations + 1

            if iterations == _timeout:
                return 'Timeout'

    def getFrom(self, startCircN, includeFirst=False):
        startCircN = str(startCircN)
        i = 1
        pageList = []

        while True:
            page = self.getPages(i, _range=False)
            cNos = [value.number for value in page]
            maxC = int([value for value in cNos if value.isnumeric()][0])

            if i == 1 and maxC < int(startCircN.split(' ')[0]) and includeFirst or i == 1 and maxC <= int(startCircN.split(' ')[0]) and not includeFirst:
                return []

            if startCircN in cNos:

                if includeFirst:
                    page = page[:cNos.index(startCircN) + 1]

                else:
                    page = page[:cNos.index(startCircN)]

                pageList.append(page)
                break

            pageList.append(page)
            i = i + 1

        return [i for o in pageList for i in o]

    class Circolare:

        def __init__(self, number, name, date, url, restricted, archiveDir, archive):
            self.number = number
            self.name = name
            self.date = date
            self.url = url
            self.restricted = restricted
            self.__archiveDir__ = archiveDir
            self.__archive__ = archive
            self.__downloadInfo__ = None

        def __saveArchive__(self):
            with open(self.__archiveDir__ + '/archive.json', 'w') as file:
                file.write(json.dumps(self.__archive__, indent=4, sort_keys=True))

        def __convertToPng__(self, infile, outfile, poppler=None):
            tmpFilesList = []
            
            if poppler:
                pages = pdf2image.convert_from_path(infile, poppler_path=poppler)

            else:
                pages = pdf2image.convert_from_path(infile)

            for page in range(len(pages)):
                pages[page].save(outfile + '-' + str(page+1) + '.png', 'PNG')
                tmpFilesList.append(outfile + '-' + str(page+1) + '.png')

            return tmpFilesList

        def download(self, path=None, pngConvert=False, docConvert=False, keepDoc=False, poppler=None):
            fileList = {}
                
            if self.__archive__ is not None:
                path = self.__archive__['dir']
                dirpath = path + '/' + self.number + '/'

                try:
                    if self.__archive__[self.number]['attachments'] is None:
                        return {}

                except:
                    pass

                try:
                    for num, filename in enumerate(self.__archive__[self.number]['attachments']):
                        tmpFilename = self.__archive__[self.number]['attachments'][filename]['filename']
                        tmpExtension = tmpFilename.split('.')[-1]

                        if not os.path.exists(self.__archive__[self.number]['attachments'][filename]['filename']) or (tmpExtension == 'pdf' and pngConvert and not glob.glob(dirpath + tmpFilename.split('-')[1].split('.')[0] + '-*.png')) or (tmpExtension in ['doc', 'docx'] and docConvert and not glob.glob(dirpath + self.number + '-*.pdf')):
                            raise 'error'

                except:
                    pass

                else:
                    if not pngConvert and not docConvert:
                        return self.__archive__[self.number]['attachments']

                    try:
                        if any(not os.path.exists(i) for o in [self.__archive__[self.number]['attachments'][f]['files'] for f in self.__archive__[self.number]['attachments']] for i in o):
                            raise 'error'

                    except:
                        pass

                    else:
                        return self.__archive__[self.number]['attachments']

            dirpath = path + '/' + self.number + '/'
            dPage = requests.get(self.url).text
            soup = bs4.BeautifulSoup(dPage, 'html.parser')
            word = None

            if docConvert:
                word = win32com.client.Dispatch('Word.Application')
                word.visible = 0
            
            for num, value in enumerate(soup.find_all(class_='post-attachment')):
                tmpFilesArray = {}

                if not glob.glob(dirpath + self.number + '-' + str(num+1) + '.*') or self.__archive__ is None:
                    pdfPage = requests.get(value.find('a')['href'])
                    pdfFile = pdfPage.content
                    cExtension = pdfPage.url.split('.')[-1]
                    
                    if not os.path.isdir(path + '/' + self.number):
                        os.mkdir(path + '/' + self.number)

                    file = open(dirpath + self.number + '-' + str(num+1) + '.' + cExtension, 'wb')
                    file.write(pdfFile)
                    file.close()
                    tmpFilesArray['name'] = value.find('a').text
                    tmpFilesArray['filename'] = dirpath + self.number + '-' + str(num+1) + '.' + cExtension

                else:
                    tmpFilesArray['name'] = self.__archive__[self.number]['attachments'][str(num+1)]['name']
                    tmpFilesArray['filename'] = self.__archive__[self.number]['attachments'][str(num+1)]['filename']
                    cExtension = tmpFilesArray['filename'].split('.')[-1]
                    tmpFilesArray['files'] = glob.glob(dirpath + str(num+1) + '-*.png')

                    if not tmpFilesArray['files']:
                        del tmpFilesArray['files']

                if pngConvert and cExtension == 'pdf' and not glob.glob(dirpath + str(num+1) + '-*.png'):
                    tmpFilesArray['files'] = self.__convertToPng__(tmpFilesArray['filename'], dirpath + str(num+1), poppler=poppler)
                
                elif docConvert and cExtension in ['doc', 'docx'] and not os.path.exists(dirpath + self.number + '-' + str(num+1) + '.pdf'):
                    wb = word.Documents.Open(os.path.abspath(tmpFilesArray['filename']))
                    wb.SaveAs2(os.path.abspath(tmpFilesArray['filename'].replace('.' + cExtension, '') + '.pdf'), FileFormat=17)
                    wb.Close()

                    if not keepDoc:
                        os.remove(tmpFilesArray['filename'])

                    tmpFilesArray['filename'] = tmpFilesArray['filename'].replace('.' + cExtension, '') + '.pdf' 

                    if pngConvert and not glob.glob(dirpath + str(num+1) + '-*.png'):                   
                        tmpFilesArray['files'] = self.__convertToPng__(tmpFilesArray['filename'], dirpath + str(num+1) , poppler=poppler)

                fileList[str(num+1)] = tmpFilesArray
            
            if word is not None:
                word.Quit()
            
            if not fileList:
                fileList = None

            if self.__archive__ is not None:
                try:
                    self.__archive__[self.number]

                except:
                    self.__archive__[self.number] = {
                        'name': self.name,
                        'date': self.date,
                        'url': self.url,
                        'restricted': self.restricted
                    }

                if not 'attachments' in self.__archive__[self.number] or (not 'files' in self.__archive__[self.number]['attachments'] and pngConvert) or docConvert:
                    self.__archive__[self.number]['attachments'] = fileList

                self.__saveArchive__()

            self.__downloadInfo__ = fileList
            return fileList

        def delete(self, archive=True, files=True):

            if files:

                try:
                    if self.__downloadInfo__ is None:
                        self.__downloadInfo__ = self.__archive__[self.number]['attachments']

                except:
                    pass

                if self.__downloadInfo__ is not None:

                    dirpath = os.path.dirname(self.__downloadInfo__['1']['filename'])

                    if os.path.exists(dirpath):
                            
                        for file in glob.glob(dirpath + '/*'):
                            os.remove(file)
                                
                        os.rmdir(dirpath)

                        if self.__archive__ is not None:
                            del self.__archive__[self.number]['attachments']

                self.__downloadInfo__ = None
                
                try:
                    del self.__archive__[self.number]['attachments']

                except:
                    pass

            if archive and self.__archive__ is not None:
                del self.__archive__[self.number]

            if self.__archive__ is not None:
                self.__saveArchive__()
