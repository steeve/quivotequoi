# -*- encoding: utf-8 -*-

from scrapy.http import Request
from scrapy.spider import BaseSpider
from ..items import DeputyItem
from urlparse import urljoin, urlsplit, urlunsplit
from lxmlselector import LxmlSelector
import re
import json
from lxml import etree

def latin1_to_ascii(unicrap):
    """This replaces UNICODE Latin-1 characters with
    something equivalent in 7-bit ASCII. All characters in the standard
    7-bit ASCII range are preserved. In the 8th bit range all the Latin-1
    accented letters are stripped of their accents. Most symbol characters
    are converted to something meaninful. Anything not converted is deleted.
    """
    xlate={0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
        0xc6:'Ae', 0xc7:'C',
        0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
        0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
        0xd0:'Th', 0xd1:'N',
        0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
        0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
        0xdd:'Y', 0xde:'th', 0xdf:'ss',
        0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
        0xe6:'ae', 0xe7:'c',
        0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
        0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
        0xf0:'th', 0xf1:'n',
        0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
        0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
        0xfd:'y', 0xfe:'th', 0xff:'y',
        0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
        0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
        0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
        0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
        0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
        0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
        0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>',
        0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
        0xd7:'*', 0xf7:'/'
        }

    r = ''
    for i in unicrap:
        if xlate.has_key(ord(i)):
            r += xlate[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += i
    return r

GROUP_MATCH = re.compile("groupe\s+([^\(\))]+) \(\d+\)", re.IGNORECASE)
INDEP_MATCH = re.compile("non[- ]+inscrit", re.IGNORECASE)
YAY_NAY_MATCH = re.compile(r"(\w+)\s*:\s+[\(\)\d]+", re.IGNORECASE)
PEOPLE_LIST_MATCH = re.compile(",\s+", re.IGNORECASE)

def clean_name(name):
    return re.search(r"(MM\.|M\.|Mme[s]*)?\s*([^\(]+)\s*(\(.*\))?", name).groups()[1].strip()


class AssembleeNationaleDeputesSpider(BaseSpider):
    name = 'deputes_assemblee_nationale'
    allowed_domains = ['assemblee-nationale.fr']

    def meta_as_dict(self, lxs):
        return dict([
            (meta.attrib("name"), meta.attrib("content"))
            for meta in lxs.xpath("/html/meta").extract()
        ])

    def start_requests(self):
        for leg in [13]:
            yield Request(
                url="http://www.assemblee-nationale.fr/qui/xml/liste_alpha.asp?legislature=%d" % leg,
                callback=self.parse_deputes_page,
                meta={
                    "leg": leg,
                }
            )

    def parse_deputes_page(self, response):
        lxs = LxmlSelector(response)
        leg_parsers = {
            11: self.parse_depute_page_leg11,
            12: self.parse_depute_page_leg12,
            13: self.parse_depute_page_leg13,
        }
        for depute_node in lxs.css(".dep2"):
            yield Request(
                url=urljoin(response.url, depute_node.attrib("href").extract()),
                callback=leg_parsers[response.meta["leg"]],
            )

    def parse_depute_page_leg11(self, response):
        lxs = LxmlSelector(response)
        etree.strip_tags(lxs.xmlNode, "b", "font", "i", "sup")
        uuid = urlsplit(response.url)[2].split("/")[-1].split(".")[0]
        jurisdiction_line = "".join(lxs.xpath("//*[contains(text(), 'Circonscription ')]//text()").extract()).encode("utf-8")
        if jurisdiction_line:
            jurisdiction = "%s (%s circonscription)" %\
                re.search(r"Circonscription d'élection : (.*?) \((.*)\)", jurisdiction_line).groups()
        else:
            jurisdiction = None
        yield DeputyItem(
            uuid=uuid,
            name=clean_name(lxs.xpath("//a[@name='P-1_0']/..//text()")[0].extract()),
            image="http://www.assemblee-nationale.fr/11/tribun/photos/%s.jpg" % uuid,
            url=response.url,
            jurisdiction=jurisdiction,
        )

    def parse_depute_page_leg12(self, response):
        lxs = LxmlSelector(response)
        etree.strip_tags(lxs.xmlNode, "u", "b", "font", "i", "sup")
        uuid = urlsplit(response.url)[2].split("/")[-1].split(".")[0]
        jurisdiction_line = lxs.xpath("//td[contains(text(), 'Circonscription ')]/following-sibling::td[1]/text()").extract()[0].encode("utf-8")
        jurisdiction = "%s (%s circonscription)" %\
            re.search(r"(.*?) \((.*)\)", jurisdiction_line).groups()
        yield DeputyItem(
            uuid=uuid,
            name=clean_name(lxs.css(".titre").text().extract()[0]),
            image="http://www.assemblee-nationale.fr/12/tribun/photos/%s.jpg" % uuid,
            url=response.url,
            jurisdiction=jurisdiction,
        )

    def parse_depute_page_leg13(self, response):
        lxs = LxmlSelector(response)
        yield DeputyItem(
            uuid=urlsplit(response.url)[2].split("/")[-1].split(".")[0],
            name=clean_name(lxs.css(".deputy-headline-title").text().extract()[0]),
            image=urljoin(response.url, lxs.css(".deputy-profile-picture")[0].attrib("src").extract()),
            url=response.url,
            jurisdiction=lxs.css(".deputy-healine-sub-title").text().extract()[0],
            party=lxs.css(".political-party").text().extract()[0],
        )
