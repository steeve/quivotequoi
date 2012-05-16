from flask import Flask, render_template, request, url_for
import requests
import json
from datetime import datetime


app = Flask(__name__)


@app.route("/")
def index():
    query = {
        "size": 1,
        "query": {
            "custom_score" : {
                "query": {
                    "match_all": {},
                },
                "script" : "random() * 20",
            },
        },
    }
    response = json.loads(
        requests.post(
            "http://localhost:9200/levote/deputies/_search",
            data=json.dumps(query)
        ).content
    )
    deputy = response["hits"]["hits"][0]["_source"]
    deputy["image"] = url_for('static', filename='img/thumbs/%s.jpg' % deputy["uuid"])
    return render_template("index.html", deputy=deputy)


@app.route("/deputes/search")
def search_deputy():
    query = {
        "size": 1000,
        "query": {
            "query_string": {
                "default_field": "name",
                "default_operator": "AND",
                "query": "%s*" % request.args.get("q"),
            },
        },
        "highlight": {
            "number_of_fragments": 0,
            "order": "score",
            "fields": {
                "name": {
                    "pre_tags": ["<strong>"],
                    "post_tags": ["</strong>"],
                },
            },
        },
    }
    response = json.loads(
        requests.post(
            "http://localhost:9200/levote/deputies/_search",
            data=json.dumps(query)
        ).content
    )

    res = []
    for hit in response["hits"]["hits"]:
        entry = hit["_source"]
        entry["name_highlight"] = hit["highlight"]["name"][0]
        res.append(entry)
    return json.dumps(res)


@app.route("/deputes/<uuid>")
def show_deputy(uuid):
    deputy = json.loads(
        requests.get("http://localhost:9200/levote/deputies/%s" % uuid).content
    )["_source"]
    deputy["image"] = url_for('static', filename='img/thumbs/%s.jpg' % deputy["uuid"])
    queries = {}
    for vote_type in ["yea", "nay", "abs"]:
        query = {
            "sort": [{"date": {"order": "desc"}}],
            "size": 1000,
            "query": {
                "term": { ("votes.votes.%s" % vote_type): uuid }
            },
        }
        queries[vote_type] = json.loads(
            requests.post(
                "http://localhost:9200/levote/scrutinies/_search",
                data=json.dumps(query)
            ).content
        )["hits"]
    for hits in queries.values():
        for hit in hits["hits"]:
            hit["_source"].update({
                "yea": 0,
                "nay": 0,
                "abs": 0,
            })
            for group_votes in hit["_source"]["votes"]:
                for vote_type, votes in group_votes["votes"].items():
                    hit["_source"][vote_type] += len(votes)
            hit["_source"]["date"] = datetime.strptime(hit["_source"]["date"], "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y")
    return render_template("deputy.html", deputy=deputy, queries=queries)


if __name__ == "__main__":
    app.debug = True
    app.run()
