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
    law_number = Field()
    law_href = Field()
    info_href = Field()
    
    def __reduce__(self):
        return {
            "title": self["title"],
            "date": self["date"].isoformat(),
            "votes": self["votes"],
            "law_number": self["law_number"],
            "law_href": self["law_href"],
            "more_info_href": self["more_info_href"],
        }