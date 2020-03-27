# CoronaDataScraper

Elastic Search Corona Dashboard

![ES dashboard](https://i.ibb.co/0ZLBNM3/Screenshot-2020-03-22-at-16-58-18.png)


### Getting started
The spider stores all of its data in elastic search. Elastic search has been dockerized so all you have to do to download it is downloader docker desktop, and run "docker-compose up" in the root directory.

After this install requrements.txt (if you dont want to use a virtual enviroment, skip to next step). This should be done by creating a virtualenv using "virtualenv -p python3 env". Then activate the env with "source env/bin/activate". 

Install requirements. "pip3 install -r requirements.txt"

Now cd into "crawlers/crawlers/spiders" and run the spider "scrapy crawl worldMeter".

### If you dont want to use elastic search, comment out these lines in the spider  

``` 
def __init__(self):
        try:
            self.es = elasticSearchApi.es()
        except Exception as e:
            quit()
```
```
self.es.store_data(rowData, index = "corona_daily_worldometer_table", doc_id = dataHash)
```  
```  
self.es.store_data(data, index = "corona_country_worldometer_past", doc_id = dataHash)
```  

