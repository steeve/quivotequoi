# -*- encoding: utf-8 -*-

from scrapy.http import Request
from scrapy.spider import BaseSpider
from ..items import ScrutinyItem, LawItem
from urlparse import urljoin, urlsplit, urlunsplit
from datetime import datetime
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


class AssembleeNationaleSpider(BaseSpider):
    name = 'assemblee_nationale'
    allowed_domains = ['assemblee-nationale.fr']

    def start_requests(self):
        ## 13e legislature:
        yield Request(
            url="http://www.assemblee-nationale.fr/13/documents/index-scrutins.asp",
            callback=self.parse_scrutin_page,
        )

    def parse_scrutin_page(self, response):
        lxs = LxmlSelector(response)
        for scrutin in lxs.xpath("//a[contains(@href, '/jo')]/../../../.."):
            title = scrutin.xpath("td[2]//text()")[0].extract()
            title = " - ".join(re.sub(r"\s+", " ", title).strip().split(" - ")[:-1])
            vote_href = urljoin(response.url, scrutin.xpath("td[1]//a/@href")[0].extract())
            info_href = urljoin(response.url, scrutin.xpath("td[2]//a/@href")[0].extract())
            vote_href = "http://www.assemblee-nationale.fr/13/scrutins/jo0845.asp"
            yield Request(
                url=vote_href,
                callback=self.parse_vote_page,
                meta={
                    "item": ScrutinyItem(
                        title=title,
                        file_href=info_href,
                    ),
                }
            )

    def parse_vote_first_layout(self, lxs, response=None):
        votes = {}
        group_name = None
        vote = None
        assembly = None
        for node in lxs.css("#analyse p"):
            node_class = node.attrib("class").extract()
            if node_class  == 'nomassemblee':
                txt = "".join(node.text().extract())
                txt = txt.replace(u"\u00A0", " ")
                txt = latin1_to_ascii(txt)
                if re.search(r"assemblee", txt, re.IGNORECASE):
                    assembly = "assemblee"
                elif re.search(r"senat", txt, re.IGNORECASE):
                    assembly = "senat"
                group_name = None
            if assembly != "senat":
                if node_class  == 'nomgroupe':
                    group_name = node.re("([\w, ]+) \(\d+\)")[0].lower()
                    group_name = re.sub(r"groupe ", "", group_name).strip()
                    votes[group_name] = {}
                    vote = None
                elif node_class == 'typevote':
                    txt = "".join(node.text().extract())
                    txt = txt.replace(u"\u00A0", " ")
                    if txt and YAY_NAY_MATCH.match(txt):
                        token = YAY_NAY_MATCH.search(txt).groups()[0].lower().strip()
                        if token == "pour":
                            vote = "yea"
                        elif token == "contre":
                            vote = "nay"
                        else:
                            vote = "abs"
                        votes[group_name][vote] = None
                elif node_class == 'noms' and group_name and vote and not votes[group_name][vote]:
                    txt = "".join(node.text().extract())
                    txt = txt.replace(u"\u00A0", " ")
                    votes[group_name][vote] = [ clean_name(name2) for name1 in txt.split(", ") for name2 in name1.split(" et ") ]
        return votes

    def parse_vote_second_layout(self, lxs):
        votes = {}
        group_name = None
        vote = None
        for node in lxs.xpath("//p"):
            txt = re.sub("\s+", " ", " ".join(node.text().extract())).strip()
            txt = txt.replace(u"\u00A0", " ")
            if GROUP_MATCH.match(txt):
                group_name = latin1_to_ascii(GROUP_MATCH.search(txt).groups()[0].lower())
                votes[group_name] = {}
                vote = None
            elif INDEP_MATCH.search(txt):
                group_name = "indep"
                votes[group_name] = {}
                vote = None
            elif group_name and YAY_NAY_MATCH.match(txt):
                token = YAY_NAY_MATCH.search(txt).groups()[0].lower().strip()
                if token == "pour":
                    vote = "yea"
                elif token == "contre":
                    vote = "nay"
                else:
                    vote = "abs"
                votes[group_name][vote] = None
            elif group_name and vote and not votes[group_name][vote]:
                votes[group_name][vote] = [ clean_name(name2) for name1 in txt.split(", ") for name2 in name1.split(" et ") ]
        return votes

    def parse_vote_page(self, response):
        lxs = LxmlSelector(response)
        item = response.meta["item"]

        date_txt = lxs.xpath("//text()").re("[DUdu\s:]+(\d+/\d+/\d+)")
        date = datetime.strptime(date_txt[0], "%d/%m/%Y")

        etree.strip_tags(lxs.xmlNode, "b", "font", "i")
        if lxs.css("#analyse p.nomgroupe"):
            votes = self.parse_vote_first_layout(lxs, response)
        else: # 2nd layout!
            votes = self.parse_vote_second_layout(lxs)
        item["date"] = date.isoformat(),
        item["votes"] = votes
        yield Request(
            url=item["file_href"],
            callback=self.parse_info_page,
            meta={
                "item": item,
            }
        )


    def parse_info_page(self, response):
        lxs = LxmlSelector(response)
        item = response.meta["item"]
        etree.strip_tags(lxs.xmlNode, "b", "font", "i")

        def get_text(node, regexp=None, invert=False):
            etree.strip_tags(node.xmlNode, "a")
            txt = ""
            for line in node.xpath(".//text()").extract():
                line = line.replace(u"\u00A0", " ")
                line = line.strip()
                if not line:
                    continue
                match = True
                if regexp:
                    match = regexp.search(line) and True or False
                if (match and not invert) or (not match and invert):
                    if line[0] != line[0].lower():
                        txt += ". "
                    txt += " %s " % line
            txt = re.sub("(\s\.+\s)+", ".", txt)
            txt = re.sub("[\s]+", " ", txt)
            txt = re.sub("[\.]+", ".", txt)
            return txt

        info_node = lxs.xpath("//a[@name = 'PDT']/ancestor::td[1]")[0]
        item["info"] = get_text(info_node, re.compile(r"(article|principales dispositions du texte)", re.IGNORECASE), invert=True)
        amendments_node = lxs.xpath("//a[@name = 'PAC']/ancestor::td[1]")[0]
        item["amendments"] = get_text(amendments_node, re.compile(r"(article|principaux amendements|travaux de|voir le compte)", re.IGNORECASE), invert=True)
        item["law"] = LawItem(
            title=lxs.xpath("//meta[@name='LOI_PROMULGUEE']/@content")[0].extract(),
            href=lxs.xpath("//meta[@name='LIEN_LOI_PROMULGUEE']/@content")[0].extract(),
            file_href=urljoin(response.url, lxs.xpath("//meta[@name='URL_DOSSIER']/@content")[0].extract()),
        )
        yield item
