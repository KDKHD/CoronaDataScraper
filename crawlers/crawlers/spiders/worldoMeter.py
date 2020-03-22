import scrapy
from scrapy.loader import ItemLoader
from scrapy import signals
from datetime import datetime
import json


class worldMeter(scrapy.Spider):
    name = "worldMeter"

    urls = [
        'https://www.worldometers.info/coronavirus/',
    ]

    graphDataContries = {}
    tableData = {}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(worldMeter, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        # do whatever with the data at the end, write to file
        currentTime = str(datetime.now()).split(".")[0]
        with open('graphDataContries_{}.json'.format(currentTime), 'w') as outfile:
            json.dump(self.graphDataContries, outfile)
        with open('tableData_{}.json'.format(currentTime), 'w') as outfile:
            json.dump(self.tableData, outfile)

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        rows = response.css("table[id='main_table_countries_today'] tbody tr")
        self.tableData = self.parseRows(rows)
        countryPages = self.getCountryUrls(self.tableData)
        for country in countryPages:
            yield scrapy.Request(response.url+country, callback=self.parseCountryPage)

    def parseRows(self, rows):
        tableData = []
        for row in rows:
            rowData = self.parseRow(row)
            tableData.append(rowData)
        return tableData

    def parseRow(self, row):
        rowData = []
        for col in row.css("td"):
            data, url = self.parseCol(col)
            rowData.append(dict(zip(["value", "url"], [data, url])))
        keys = ["country", "totalCases", "newCases", "totalDeaths",
                "newDeaths", "totalRecovered", "activeCases", "seriousCasesrows"]
        rowDict = dict(zip(keys, rowData))
        return rowDict

    def parseCol(self, col):
        dataRaw = col.css("::text").extract_first()
        urlRaw = col.css("a ::attr(href)").extract_first()
        url = urlRaw.strip() if urlRaw != None else ""
        data = dataRaw.strip() if dataRaw != None else ""
        return (["", url] if data == None else [data, url])

    def getCountryUrls(self, tableData):
        countryLinks = []
        for row in tableData:
            countryCol = row["country"]
            if countryCol["url"] != "":
                countryLinks.append(countryCol["url"])
        return countryLinks

    def parseCountryPage(self, response):
        country = response.url.strip("/").split("/")[-1]

        # extract script tag -> Highcharts containing the data
        scriptData = response.css(
            ".col-md-12")[0].css("script[type='text/javascript']").extract_first()
        start = "Highcharts.chart('coronavirus-cases-linear',"
        end = ";"
        graphScriptTag = scriptData[scriptData.find(
            start):scriptData.find(end)]

        # extract categories
        catStart = graphScriptTag[graphScriptTag.find("categories:"):]
        categories = catStart[:catStart.find("}")]
        categories = categories.replace("categories", '"categories"')
        categories = json.loads("{"+categories+"}")

        # extract data
        dataStart = graphScriptTag[graphScriptTag.find("data:"):]
        data = dataStart[:dataStart.find("}")]
        data = data.replace("data", '"data"')
        data = json.loads("{"+data+"}")

        # merge categories and data
        graphData = dict(zip(categories["categories"], data["data"]))
        self.graphDataContries[country] = graphData
