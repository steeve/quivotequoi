# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class VoteItem(Item):
    vote = Field()
    name = Field()
    group = Field()

    def __reduce__(self):
        return {
            "vote": self["vote"],
            "name": self["name"],
            "group": self["group"],
        }


class ScrutinyItem(Item):
    title = Field()
    date = Field()
    votes = Field()
    file_href = Field()
    law = Field()
    info = Field()
    amendments = Field()

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
    info = Field()
    amendments = Field()
    file_href = Field()

    def __reduce__(self):
        return {
            "title": self["title"],
            "href": self["law_href"],
            "law_href": self["law_href"],
        }
