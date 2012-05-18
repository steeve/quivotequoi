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
    def name_to_object(self, name):
        if not name:
            return
        query = {
            "size": 1,
            "query": {
                "query_string": {
                    "default_field": "name",
                    "default_operator": "AND",
                    "query": name,
                },
            },
        }
        response = json.loads(requests.post("http://localhost:9200/quivotequoi/deputies/_search",
            data=json.dumps(query)).content)
        if response["hits"]["total"] > 0:
            return response["hits"]["hits"][0]["_source"]["uuid"]


    def process_item(self, item, spider):
        if not isinstance(item, ScrutinyItem):
            return item
        new_votes = {}
        for group_name, group_votes in item["votes"].items():
            for vote_type, voters in group_votes.items():
                if not voters:
                    continue
                new_votes[group_name] = new_votes.get(group_name) or {}
                new_votes[group_name].update({
                    vote_type: map(self.name_to_object, voters)
                })
        item["votes"] = new_votes
        return item


class ElasticSearchPipeline(object):
    def process_deputy_item(self, item, spider):
        requests.post("http://localhost:9200/quivotequoi/deputies/%s" % item["uuid"],
            data=json.dumps(item._values))
        return item

    def process_scrutiny_item(self, item, spider):
        es_item = {}
        for k in ["uuid", "title", "date", "url", "leg", "num", "keywords", "file_href", "info", "amendments"]:
            es_item[k] = item.get(k)
        es_item["votes"] = []
        for group_name, group_votes in item["votes"].items():
            es_item["votes"].append({
                "name": group_name,
                "votes": group_votes
            })
        if item.get("law"):
            es_item["law_href"] = item["law"]["href"]
            es_item["file_href"] = item["law"]["file_href"]
        requests.post("http://localhost:9200/quivotequoi/scrutinies/%s" % item["uuid"], data=json.dumps(es_item))
        return item

    def process_item(self, item, spider):
        if isinstance(item, DeputyItem):
            return self.process_deputy_item(item, spider)
        elif isinstance(item, ScrutinyItem):
            return self.process_scrutiny_item(item, spider)
        return item
