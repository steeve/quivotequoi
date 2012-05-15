# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class DeputyItem(Item):
    uuid = Field()
    name = Field()
    image = Field()
    url = Field()
    jurisdiction = Field()
    party = Field()


class ScrutinyItem(Item):
    uuid = Field()
    leg = Field()
    num = Field()
    title = Field()
    date = Field()
    votes = Field()
    url = Field()
    file_href = Field()
    law = Field()
    info = Field()
    amendments = Field()
    summary = Field()
    keywords = Field()

    def __reduce__(self):
        return {
            "title": self["title"],
            "date": self["date"].isoformat(),
            "votes": self["votes"],
            "law": self["law"].__reduce__(),
            "info": self["info"],
            "amendments": self["amendments"],
        }


class LawItem(Item):
    title = Field()
    href = Field()
    file_href = Field()

    def __reduce__(self):
        return {
            "title": self["title"],
            "href": self["law_href"],
            "law_href": self["law_href"],
        }
