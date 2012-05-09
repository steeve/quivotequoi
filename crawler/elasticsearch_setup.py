# -*- coding: utf-8 -*-

import json
import requests
from urlparse import urljoin
from datetime import datetime


def get_timestamp_split_pattern():
    import re
    import string
    delimiters = string.punctuation
    delimiters = re.sub(r"[%s]" % re.escape("{}"), "", delimiters)
    pattern = r"\{\d+\}|[%s\s]+" % re.escape(delimiters)
    return pattern


FRENCH_STOP_WORDS = (
    "a", "afin", "ai", "ainsi", "après", "attendu", "au", "aujourd", "auquel", "aussi",
    "autre", "autres", "aux", "auxquelles", "auxquels", "avait", "avant", "avec", "avoir",
    "c", "car", "ce", "ceci", "cela", "celle", "celles", "celui", "cependant", "certain",
    "certaine", "certaines", "certains", "ces", "cet", "cette", "ceux", "chez", "ci",
    "combien", "comme", "comment", "concernant", "contre", "d", "dans", "de", "debout",
    "dedans", "dehors", "delà", "depuis", "derrière", "des", "désormais", "desquelles",
    "desquels", "dessous", "dessus", "devant", "devers", "devra", "divers", "diverse",
    "diverses", "doit", "donc", "dont", "du", "duquel", "durant", "dès", "elle", "elles",
    "en", "entre", "environ", "est", "et", "etc", "etre", "eu", "eux", "excepté", "hormis",
    "hors", "hélas", "hui", "il", "ils", "j", "je", "jusqu", "jusque", "l", "la", "laquelle",
    "le", "lequel", "les", "lesquelles", "lesquels", "leur", "leurs", "lorsque", "lui", "là",
    "ma", "mais", "malgré", "me", "merci", "mes", "mien", "mienne", "miennes", "miens", "moi",
    "moins", "mon", "moyennant", "même", "mêmes", "n", "ne", "ni", "non", "nos", "notre",
    "nous", "néanmoins", "nôtre", "nôtres", "on", "ont", "ou", "outre", "où", "par", "parmi",
    "partant", "pas", "passé", "pendant", "plein", "plus", "plusieurs", "pour", "pourquoi",
    "proche", "près", "puisque", "qu", "quand", "que", "quel", "quelle", "quelles", "quels",
    "qui", "quoi", "quoique", "revoici", "revoilà", "s", "sa", "sans", "sauf", "se", "selon",
    "seront", "ses", "si", "sien", "sienne", "siennes", "siens", "sinon", "soi", "soit",
    "son", "sont", "sous", "suivant", "sur", "ta", "te", "tes", "tien", "tienne", "tiennes",
    "tiens", "toi", "ton", "tous", "tout", "toute", "toutes", "tu", "un", "une", "va", "vers",
    "voici", "voilà", "vos", "votre", "vous", "vu", "vôtre", "vôtres", "y", "à", "ça", "ès",
    "été", "être", "ô"
)


ENGLISH_STOP_WORDS = (
    "a", "and", "are", "as", "at", "be", "but", "by",
    "for", "if", "in", "into", "is", "it",
    "no", "not", "of", "on", "or", "s", "such",
    "t", "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with"
)


FILTER_PIPELINE = ["standard", "lowercase", "asciifolding", "refined_soundex"]
FRENCH_FILTER_PIPELINE = ["standard", "lowercase", "elision", "stop_fr", "asciifolding", "snowball_fr", "refined_soundex"]
ENGLISH_FILTER_PIPELINE = ["standard", "lowercase", "stop_en", "asciifolding", "snowball_en", "refined_soundex"]

INDEX_SETTINGS = {
    "index": {
        "number_of_shards" : 5,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "trend_analyzer": {
                    "tokenizer": "keyword",
                    "filter": ["lowercase", "unique"],
                },
                "general_analyzer": {
                    "tokenizer": "standard",
                    "filter": FILTER_PIPELINE,
                },
                "french_analyzer": {
                    "tokenizer": "standard",
                    "filter": FRENCH_FILTER_PIPELINE,
                },
                "timestamped_french_analyzer": {
                    "tokenizer": "timestamp_tokenizer",
                    "filter": FRENCH_FILTER_PIPELINE,
                },
                "english_analyzer": {
                    "tokenizer": "standard",
                    "filter": ENGLISH_FILTER_PIPELINE,
                },
                "timestamped_english_analyzer": {
                    "tokenizer": "timestamp_tokenizer",
                    "filter": ENGLISH_FILTER_PIPELINE,
                },
            },
            "tokenizer": {
                "timestamp_tokenizer": {
                    "type": "pattern",
                    "pattern": get_timestamp_split_pattern(),
                },
            },
            "filter": {
                "elision" : {
                    "type" : "elision",
                    "articles" : ["l", "m", "t", "qu", "n", "s", "j"]
                },
                "refined_soundex": {
                    "type": "phonetic",
                    "encoder": "refined_soundex",
                    "replace": "false",
                },
                "snowball_fr": {
                    "type": "snowball",
                    "language": "French",
                },
                "stop_fr": {
                    "type": "stop",
                    "stopwords": FRENCH_STOP_WORDS,
                },
                "snowball_en": {
                    "type": "snowball",
                    "language": "English",
                },
                "stop_en": {
                    "type": "stop",
                    "stopwords": ENGLISH_STOP_WORDS,
                },
            },
        },
    },
}


MAPPINGS = {
    "scrutinies": {
        "dynamic": False,
        "properties": {
            "uuid": {"type": "string", "index": "not_analyzed"},
            "title": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
            "date": {"type": "date"},
            "leg": {"type": "string", "index": "not_analyzed"},
            "num": {"type": "string", "index": "not_analyzed"},
            "votes": {
                "type": "object",
                "properties": {
                    "yea": {"type": "string", "index": "not_analyzed"},
                    "nay": {"type": "string", "index": "not_analyzed"},
                    "abs": {"type": "string", "index": "not_analyzed"},
                }
            },
            "url": {"type": "string", "index": "not_analyzed"},
            "summary": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
            "info": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
            "amendments": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
            "keywords": {"type": "string", "index": "analyzed", "analyzer": "trend_analyzer"},
            "law_href": {"type": "string", "index": "not_analyzed"},
            "file_href": {"type": "string", "index": "not_analyzed"},
        },
    },
    "deputies": {
        "dynamic": False,
        "properties": {
            "uuid": {"type": "string", "index": "not_analyzed"},
            "name": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
            "image": {"type": "string", "index": "not_analyzed"},
            "url": {"type": "string", "index": "not_analyzed"},
            "jurisdiction": {"type": "string", "index": "analyzed", "analyzer": "french_analyzer"},
        },
    },
}


def create_index(endpoint, index_name):
    # create (and open) the index
    print requests.put(urljoin(endpoint, index_name), data=json.dumps(INDEX_SETTINGS)).content


def delete_index(endpoint, index_name):
    # close the index
    requests.post(urljoin(endpoint, "%s/_close" % index_name))
    # delete the index
    requests.delete(urljoin(endpoint, index_name))


def push_mappings(endpoint, index_name):
    for type_, props in MAPPINGS.items():
        payload = {type_: props}
        print requests.put(urljoin(endpoint, "/%s/%s/_mapping?ignore_conflicts=true" % (index_name, type_)), data=json.dumps(payload)).content


def push_video(endpoint, index, type_, video_obj):
    requests.put(urljoin(endpoint, "/%s/%s/%s" % (index, type_, video_obj["uuid"])), data=json.dumps(video_obj))


def push_object(endpoint, index, obj):
    requests.put(urljoin(endpoint, "/%s/%s/%s" % (index, obj["_type"], obj["_id"])), data=json.dumps(obj["_source"]))


def get_real_index_name(endpoint, index):
    aliases_data = json.loads(requests.get(urljoin(endpoint, "%s/_aliases" % index)).content)
    for index_name, aliases in aliases_data.items():
        if index in aliases["aliases"]:
            return index_name
    return index


def add_alias(endpoint, index, alias):
    index = get_real_index_name(endpoint, index)
    payload = {
        "actions": { "add": { "index": index, "alias": alias } }
    }
    requests.post(urljoin(endpoint, "_aliases"), data=json.dumps(payload))


def remove_alias(endpoint, alias):
    index = get_real_index_name(endpoint, alias)
    payload = {
        "actions": { "remove": { "index": index, "alias": alias } }
    }
    requests.post(urljoin(endpoint, "_aliases"), data=json.dumps(payload))


def switch_alias(endpoint, alias, new_index):
    index = get_real_index_name(endpoint, alias)
    payload = {
        "actions": [
            { "remove": { "index": index, "alias": alias } },
            { "add": { "index": new_index, "alias": alias } },
        ],
    }
    requests.post(urljoin(endpoint, "_aliases"), data=json.dumps(payload))


def scroll_hits(endpoint, index):
    query = {
        "query": {
            "match_all": {},
        },
    }
    resp = json.loads(requests.post(urljoin(endpoint, "%s/_search?search_type=scan&scroll=10m&size=10" % index), data=json.dumps(query)).content)
    scroll_id = resp["_scroll_id"]
    while True:
        resp = json.loads(requests.post(urljoin(endpoint, "/_search/scroll?scroll=10m"), data=scroll_id).content)
        scroll_id = resp["_scroll_id"]
        hits = resp["hits"]["hits"]
        if len(hits) == 0:
            break
        for hit in hits:
            yield hit


def repush_index(endpoint, index, hit_cb=None):
    alias = index
    index = get_real_index_name(endpoint, alias)
    # create the new index
    new_index = "%s_%s" % (alias, datetime.now().strftime("%Y%m%d_%H%M%S"))
    print "Creating new index %s" % new_index
    create_index(endpoint, new_index)
    print "Pushing mappings to new index %s" % new_index
    push_mappings(endpoint, new_index)

    total = 0
    buffer = []
    for i, hit in enumerate(scroll_hits(endpoint, index)):
        if hit_cb:
            hit = hit_cb(hit)
        print "Adding %s" % hit["_id"]
        buffer.append(hit)
        if len(buffer) == 100:
            print "Pushing %d objects to index" % len(buffer)
            push_objects(endpoint, new_index, buffer)
            total += len(buffer)
            print "Pushed %d objects total" % total
            buffer = []
    print "Pushing %d objects to index" % len(buffer)
    push_objects(endpoint, new_index, buffer)
    total += len(buffer)
    print "Pushed %d objects total" % total

    print "Switching alias %s from %s to %s" % (alias, index, new_index)
    switch_alias(endpoint, alias, new_index)
    print "Deleting index %s" % index
    delete_index(endpoint, index)


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1]
    index_name = sys.argv[2]
    create_index(endpoint, index_name)
    push_mappings(endpoint, index_name)
