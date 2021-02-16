import requests
import bs4

class Circolari:

    def __init__(self):
        self.__pageTemplate__ = 'https://www.itispaleocapa.edu.it/circolari/page/'

    def getPages(self, no, _range=True):
        circolariList = list()

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

                circolariList.append(self.Circolare(cNo, cTitle, cDate, cURL, cRestricted))

        return circolariList

    def get(self, no, _timeout=5):
        no = str(no)
        noN = int(no.split(' ')[0])

        if noN < 1:
            return 'Inesistente'

        cList = self.getPages(1, _range=False)
        cNos = [value.number for value in cList]

        if no in cNos:
            return [value for value in cList if value.number == no][0]

        iterations = 0
        page = 1

        while True:
            cNoN = [int(value) for value in cNos if value.isnumeric()]
            last = cNoN[0]
            first = cNoN[-1]

            if noN > last:
                return 'Inesistente'

            page = page + int((last - noN) / 10)
            cList = self.getPages(page, _range=False)
            cNos = [value.number for value in cList]

            if no in cNos:
                return [value for value in cList if value.number == no][0]

            iterations = iterations + 1

            if iterations == _timeout:
                return 'Timeout'

    class Circolare:

        def __init__(self, number, name, date, url, restricted):
            self.number = number
            self.name = name
            self.date = date
            self.url = url
            self.restricted = restricted

        def download(self, path, filename=None, formato='pdf'):
            dPage = requests.get(self.url).text
            soup = bs4.BeautifulSoup(dPage, 'html.parser')
            pdfFile = requests.get(soup.find('li', class_='post-attachment').find('a')['href'])

            if not filename:
                filename = self.number
            
            file = open(path + '/' + filename + '.pdf', 'wb')
            file.write(pdfFile.content)
            file.close()