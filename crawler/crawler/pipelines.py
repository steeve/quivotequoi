import json
import requests
from crawler.items import DeputyItem, ScrutinyItem


class AlchemyPipeline(object):
    ALCHEMY_GET_KW = "http://access.alchemyapi.com/calls/text/TextGetRankedKeywords"
    ALCHEMY_API_KEY = "78bc5b9c89be4e4fed36bb4ce01f3d7d9e836ee5"

    def process_item(self, item, spider):
        text = "%s\n%s\n%s\n%s" % (
            item["title"],
            item.get("summary", ""),
            item.get("info", ""),
            item.get("amendments", ""),
        )
        response = json.loads(requests.post(self.ALCHEMY_GET_KW, data={
                "apikey": self.ALCHEMY_API_KEY,
                "text": text,
                "keywordExtractMode": "normal",
                "maxRetrieve": 20,
                "showSourceText": 0,
                "outputMode": "json",
        }).content)
        item["keywords"] = [kw["text"] for kw in response["keywords"]]
        return item

class DeputyUuidPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, ScrutinyItem):
            return item
        new_votes = {}
        for group, votes in item["votes"].items():
            new_votes[group] = {}
            for vote_type, voters in votes.items():
                new_votes[group][vote_type] = []
                if voters:
                    for voter in voters:
                        if not voter:
                            new_votes[group][vote_type].append(None)
                            continue
                        query = {
                            "fields": [],
                            "size": 1,
                            "query": {
                                "query_string": {
                                    "fields": ["name"],
                                    "query": voter,
                                },
                            },
                        }
                        response = json.loads(requests.post("http://localhost:9200/levote/deputies/_search",
                            data=json.dumps(query)).content)
                        if response["hits"]["total"] > 0:
                            uuid = response["hits"]["hits"][0]["_id"]
                        else:
                            uuid = None
                        new_votes[group][vote_type].append(uuid)
        item["votes"] = new_votes
        return item


class ElasticSearchPipeline(object):
    def process_deputy_item(self, item, spider):
        requests.post("http://localhost:9200/levote/deputies/%s" % item["uuid"],
            data=json.dumps(item._values))
        return item

    def process_scrutiny_item(self, item, spider):
        es_item = {}
        for k in ["uuid", "title", "date", "url", "leg", "num", "keywords", "file_href", "info", "amendments"]:
            es_item[k] = item.get(k)
        es_item["votes"] = {}
        for vote_type in ["yea", "nay", "abs"]:
            es_item["votes"][vote_type] = []
            for votes in item["votes"].values():
                es_item["votes"][vote_type].extend(votes.get(vote_type, []))
        if item.get("law"):
            es_item["law_href"] = item["law"]["href"]
            es_item["file_href"] = item["law"]["file_href"]
        requests.post("http://localhost:9200/levote/scrutinies/%s" % item["uuid"], data=json.dumps(es_item))
        return item

    def process_item(self, item, spider):
        if isinstance(item, DeputyItem):
            return self.process_deputy_item(item, spider)
        elif isinstance(item, ScrutinyItem):
            return self.process_scrutiny_item(item, spider)
        return item
