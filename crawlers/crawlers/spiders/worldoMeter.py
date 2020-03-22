import scrapy
from scrapy.loader import ItemLoader
from scrapy import signals
from datetime import datetime
import time
import json
import hashlib
from ..connections.elasticSearch import elasticSearchApi
import pycountry
import countryCodes
class worldMeter(scrapy.Spider):
    name = "worldMeter"

    urls = [
        'https://www.worldometers.info/coronavirus/',
    ]

    graphDataContries = {}
    tableData = {}
    es = None

    def __init__(self):
        try:
            self.es = elasticSearchApi.es()
        except Exception as e:
            quit()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(worldMeter, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        return
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
            dataHash = hashlib.md5(json.dumps(rowData, sort_keys = True).encode("utf-8")).hexdigest()
            rowData["time"] = datetime.now()
            rowData["country"] = "{}".format(rowData["country"]["value"].lower().split(".")[-1].strip().replace(" ","-"))
            if "total" in rowData["country"]:
                continue
            try:
                if rowData["country"].upper() in countryCodes.countryDict:
                    rowData["alpha2"] = countryCodes.countryDict[rowData["country"].upper()]
                else:
                    rowData["alpha2"]= pycountry.countries.search_fuzzy(rowData["country"].replace("-", " "))[0].alpha_2
            except Exception as e:
                try:
                    rowData["alpha2"]= pycountry.countries.search_fuzzy(rowData["country"])[0].alpha_2
                except Exception as e:
                    print(rowData["country"].upper())
            self.es.store_data(rowData, index = "corona_daily_worldometer_table", doc_id = dataHash)
            tableData.append(rowData)
        return tableData

    def parseRow(self, row):
        rowData = []
        for col in row.css("td"):
            data, url = self.parseCol(col)
            if url != "":
                rowData.append(dict(zip(["value", "url"], [data, url])))
            else:
                rowData.append(dict(zip(["value"], [data])))
        keys = ["country", "totalCases", "newCases", "totalDeaths",
                "newDeaths", "totalRecovered", "activeCases", "seriousCasesrows"]
        rowDict = dict(zip(keys, rowData))
        return rowDict

    def parseCol(self, col):
        dataRaw = col.css("::text").extract_first()
        urlRaw = col.css("a ::attr(href)").extract_first()
        url = urlRaw.strip() if urlRaw != None else ""
        data = dataRaw.strip() if dataRaw != None else ""
        try:
            data = int(data.replace(",",""))
        except ValueError:
            pass
        return (["", url] if data == None else [data, url])

    def getCountryUrls(self, tableData):
        countryLinks = []
        for row in tableData:
            countryCol = row["country"]
            try:
                if countryCol["url"] != "":
                    countryLinks.append(countryCol["url"])
            except Exception as e:
                pass
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
