from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/deputy_search")
def search_deputy():
    query = {
        "size": 1000,
        "query": {
            "query_string": {
                "fields": ["name"],
                "query": "%s*" % request.args.get("q"),
            },
        },
    }
    response = json.loads(
        requests.post(
            "http://localhost:9200/levote/deputies/_search",
            data=json.dumps(query)
        ).content
    )
    return render_template("deputy_table.html", hits=response["hits"])

@app.route("/deputy/<uuid>")
def show_deputy(uuid):
    deputy = json.loads(
        requests.get("http://localhost:9200/levote/deputies/%s" % uuid).content
    )["_source"]
    queries = {}
    for vote_type in ["yea", "nay", "abs"]:
        query = {
            "sort": [{"date": {"order": "desc"}}],
            "fields": ["title", "date", "url", "law_href", "file_href", "law_href"],
            "size": 1000,
            "query": {
                "term": { ("votes.%s" % vote_type): uuid }
            },
        }
        queries[vote_type] = json.loads(
            requests.post(
                "http://localhost:9200/levote/scrutinies/_search",
                data=json.dumps(query)
            ).content
        )["hits"]
    return render_template("deputy.html", deputy=deputy, queries=queries)


if __name__ == "__main__":
    app.debug = True
    app.run()
