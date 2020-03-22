from elasticsearch import Elasticsearch, helpers
import logging
class es(Elasticsearch):
    connData = {
        "host": "http://localhost",
        "port": 9200,
        "username": "elastic",
        "password": "changeme",
        }

    def __init__(self):
        print("_____________________________")
        try:
            self.es = Elasticsearch(['{}:{}'.format(self.connData["host"], self.connData["port"])], verify_certs=True)
            if not self.es.ping():
                raise ValueError("Connection failed")
        except Exception as e:
            logging.error("Elasticsearch API: {}".format(e))
            quit()
        logging.info("Elasticsearch API: {}".format("ElasticSearch initiated"))
        es_logger = logging.getLogger('elasticsearch')
        es_logger.setLevel(logging.WARNING)

    def store_data(self, data_object, index = "index", doc_type='data', doc_id = None):
        try:
            if doc_id == None:
                self.es.index(index=index, doc_type=doc_type, body=data_object,
                                request_timeout=30)
            else:
                self.es.index(index=index, doc_type=doc_type, body=data_object,
                                request_timeout=30, id=doc_id)
            logging.info("Object stored.")
        except Exception as e:
            logging.error(e)
            pass
       

