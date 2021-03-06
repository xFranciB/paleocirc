import aiohttp
import asyncio
import bs4
import pdf2image
import os
import json

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

    async def __aenter__(self):
        self.__session__ = aiohttp.ClientSession()
        return self

    async def __aexit__(self, type, value, traceback):
        await self.__session__.close()

    def __saveArchive__(self):
        with open(self.__archiveDir__ + '/archive.json', 'w') as file:
            file.write(json.dumps(self.__archive__, indent=4, sort_keys=True))

    async def getPages(self, no, _range=True):
        circolariList = list()
        no = int(no)

        if no < 1:
            return []
        

        if _range:
            pList = range(no)

        else:
            pList = [no-1]

        for i in pList:
            async with self.__session__.get(self.__pageTemplate__ + str(i + 1)) as response:
                x = await response.text()

            soup = bs4.BeautifulSoup(x, 'html.parser')
            tags = soup.find_all(class_='post-box-archive')

            for circolare in tags:
                aTag = circolare.find_all('a')[1]
                cURL = aTag['href']
                cNo = [value for value in [i for o in [value.replace('/', '').split(' ') for value in aTag.text.lower().replace('bis', '').split('.')] for i in o] if value.isnumeric()][0]
                
                while True:
                    if cNo.startswith('0'):
                        cNo = cNo[1:]

                    else:
                        break

                if 'bis' in aTag.text.lower():
                    cNo = cNo + ' bis'
                
                cDate = circolare.find_all(class_='hdate')[0].text
                dMAE = circolare.find(class_='members-access-error')
                
                if dMAE:
                    cRestricted = True
                    cTitle = dMAE.text

                else:
                    cRestricted = False
                    cTitle = circolare.find('p').text

                circolariList.append(self.Circolare(cNo, cTitle, cDate, cURL, cRestricted, self.__session__, self.__archiveDir__, self.__archive__))

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

    async def get(self, no, _timeout=5):
        no = str(no)
        noN = int(no.split(' ')[0])

        if self.__archive__ is not None:
            if no in self.__archive__:
                return self.Circolare(no, self.__archive__[no]['name'], self.__archive__[no]['date'], self.__archive__[no]['url'], self.__archive__[no]['restricted'], self.__session__, self.__archiveDir__, self.__archive__)

        if noN < 1:
            return 'Inesistente'

        cList = await self.getPages(1, _range=False)
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
            
            cList = await self.getPages(page, _range=False)
            cNos = [value.number for value in cList]

            if no in cNos:
                return [value for value in cList if value.number == no][0]

            iterations = iterations + 1

            if iterations == _timeout:
                return 'Timeout'

    async def getFrom(self, startCircN, includeFirst=False):
        startCircN = str(startCircN)
        i = 1
        pageList = []

        while True:
            page = await self.getPages(i, _range=False)
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

        def __init__(self, number, name, date, url, restricted, session, archiveDir, archive):
            self.number = number
            self.name = name
            self.date = date
            self.url = url
            self.restricted = restricted
            self.__session__ = session
            self.__archiveDir__ = archiveDir
            self.__archive__ = archive
            self.__downloadInfo__ = None

        def __saveArchive__(self):
            with open(self.__archiveDir__ + '/archive.json', 'w') as file:
                file.write(json.dumps(self.__archive__, indent=4, sort_keys=True))

        async def download(self, path=None, pngConvert=False, poppler=None):
            fileList = {}
            pdfExists = False
                
            if self.__archive__ is not None:
                path = self.__archive__['dir'] 

                try:
                    if self.__archive__[self.number]['attachments'] is None:
                        return {}

                except:
                    pass

                try:
                    if not os.path.exists(self.__archive__[self.number]['attachments']['1']['pdf']):
                        raise 'error'

                except:
                    pass

                else:
                    if not pngConvert:
                        return self.__archive__[self.number]['attachments']
                    
                    pdfExists = True

                    try:
                        if not os.path.exists(self.__archive__[self.number]['attachments']['1']['files'][0]):
                            raise 'error'

                    except:
                        pass

                    else:
                        return self.__archive__[self.number]['attachments']

            async with self.__session__.get(self.url) as response:
                dPage = await response.text()

            soup = bs4.BeautifulSoup(dPage, 'html.parser')
            
            for num, value in enumerate(soup.find_all(class_='post-attachment')):

                tmpFilesArray = {}
                dirpath = path + '/' + self.number + '/'

                if not pdfExists:
                    async with self.__session__.get(value.find('a')['href']) as response:
                        pdfFile = await response.content.read()
                    
                    if not os.path.isdir(path + '/' + self.number):
                        os.mkdir(path + '/' + self.number)

                    file = open(dirpath + self.number + '-' + str(num+1) + '.pdf', 'wb')
                    file.write(pdfFile)
                    file.close()
                    tmpFilesArray['name'] = value.find('a').text
                    tmpFilesArray['pdf'] = dirpath + self.number + '-' + str(num+1) + '.pdf'

                else:
                    tmpFilesArray['name'] = self.__archive__[self.number]['attachments'][str(num+1)]['name']
                    tmpFilesArray['pdf'] = self.__archive__[self.number]['attachments'][str(num+1)]['pdf']

                if pngConvert:
                    tmpFilesList = []

                    if poppler:
                        pages = pdf2image.convert_from_path(dirpath + self.number + '-' + str(num+1) + '.pdf', poppler_path=poppler)

                    pages = pdf2image.convert_from_path(dirpath + self.number + '-' + str(num+1) + '.pdf')

                    for page in range(len(pages)):
                        pages[page].save(dirpath + str(num+1) + '-' + str(page+1) + '.png', 'PNG')
                        tmpFilesList.append(dirpath + str(num+1) + '-' + str(page+1) + '.png')

                    tmpFilesArray['files'] = tmpFilesList
                
                fileList[str(num+1)] = tmpFilesArray
            
            if fileList == {}:
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

                if not 'attachments' in self.__archive__[self.number] or (not 'files' in self.__archive__[self.number]['attachments'] and pngConvert):
                    self.__archive__[self.number]['attachments'] = fileList

                self.__saveArchive__()

            self.__downloadInfo__ = fileList
            return fileList

        def delete(self, archive=True, files=True):
            filesExist = True

            if self.__archive__ is not None and self.__downloadInfo__ is None:
                try:
                    self.__downloadInfo__ = self.__archive__[self.number]['attachments']

                except:
                    filesExist = False

            if self.__downloadInfo__ is not None and filesExist:
                dirpath = os.path.dirname(self.__downloadInfo__['1']['pdf'])

                for value in self.__downloadInfo__:
                    
                    if files and self.__downloadInfo__ is not None:
                        pdfPath = self.__downloadInfo__[value]['pdf']
                        
                        if os.path.exists(pdfPath):
                            os.remove(pdfPath)
                        
                        for image in self.__downloadInfo__[value]['files']:
                            if os.path.exists(image):
                                os.remove(image)

                if len(os.listdir(dirpath)) == 0:
                    os.rmdir(dirpath)

                if self.__archive__ is not None:
                    del self.__archive__[self.number]['attachments']

            if archive and self.__archive__ is not None:
                del self.__archive__[self.number]

            if self.__archive__ is not None:
                self.__saveArchive__()