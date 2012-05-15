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
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR')

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
    res = re.search(r"(MM\.|M\.|Mme[s]*)?\s*([^\(]+)\s*(\(.*\))?", name).groups()[1].strip()
    res = re.sub(r"\.$", "", res)
    return res


class AssembleeNationaleSpider(BaseSpider):
    name = 'assemblee_nationale'
    allowed_domains = ['assemblee-nationale.fr']

    def meta_as_dict(self, lxs):
        return dict(
            (meta.attrib("name").extract(), meta.attrib("content").extract())
            for meta in lxs.xpath("/html/head/meta[@name]")
        )

    def start_requests(self):
        for leg in [13]:
            yield Request(
                url="http://www.assemblee-nationale.fr/%d/documents/index-scrutins.asp" % leg,
                callback=self.parse_scrutin_page,
            )

    def parse_scrutin_page(self, response):
        lxs = LxmlSelector(response)
        for scrutin in lxs.xpath("//a[contains(@href, '/jo')]/../../../.."):
            title = scrutin.xpath("td[2]//text()")[0].extract()
            title = " - ".join(re.sub(r"\s+", " ", title).strip().split(" - ")[:-1])
            vote_href = urljoin(response.url, scrutin.xpath("td[1]//a/@href")[0].extract())
            if scrutin.xpath("td[2]//a/@href"):
                file_href = urljoin(response.url, scrutin.xpath("td[2]//a/@href")[0].extract())
            else:
                file_href = None
            vote_path = urlsplit(vote_href)[2].split("/")
            leg = vote_path[1]
            num = vote_path[-1].split(".")[0].replace("jo", "")
            #vote_href = "http://www.assemblee-nationale.fr/12/scrutins/jo0848.asp"
            yield Request(
                url=vote_href,
                callback=self.parse_vote_page,
                meta={
                    "item": ScrutinyItem(
                        uuid="%s-%s" % (leg, num),
                        title=title,
                        file_href=file_href,
                        leg=leg,
                        num=num,
                        url=vote_href,
                    ),
                }
            )
            #break

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
                    txt = txt.replace(" et ", ", ")
                    votes[group_name][vote] = [clean_name(name) for name in re.split(r",\s*", txt)]
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
                txt = "".join(node.text().extract())
                txt = txt.replace(u"\u00A0", " ")
                txt = txt.replace(" et ", ", ")
                votes[group_name][vote] = [clean_name(name) for name in re.split(r",\s*", txt)]
        return votes

    def parse_vote_page(self, response):
        lxs = LxmlSelector(response)
        item = response.meta["item"]
        etree.strip_tags(lxs.xmlNode, "b", "font", "i", "sup")
        meta = self.meta_as_dict(lxs)

        date_txt = lxs.xpath("//text()").re(r"[DUdu\s:]+(\d+/\d+/\d+)")
        if date_txt:
            item["date"] = datetime.strptime(date_txt[0], "%d/%m/%Y").isoformat()
        else:
            page_text = "".join(lxs.xpath("//text()").extract())
            page_text = page_text.replace(u"\u00A0", " ")
            page_text = page_text.encode("utf-8")
            date_txt = re.search(r"du[:\s]+(\d+)[er]*\s+(.+?)\s+(\d+)", page_text)
            if date_txt:
                date_txt = " ".join(date_txt.groups())
                item["date"] = datetime.strptime(date_txt, "%d %B %Y").isoformat()
            else:
                raise

        if lxs.css("#analyse p.nomgroupe"):
            item["votes"] = self.parse_vote_first_layout(lxs, response)
        else: # 2nd layout!
            item["votes"] = self.parse_vote_second_layout(lxs)

        if item.get("file_href"):
            yield Request(
                url=item["file_href"],
                callback=self.parse_info_page,
                meta={
                    "item": item,
                }
            )
        else:
            yield item

    def parse_info_page(self, response):
        def get_text_formatted(node):
            from lxml.html import fromstring
            etree.strip_tags(node.xmlNode, "a")
            txt = node.extract()
            txt = txt.replace("<br/>", "\n")
            txt = txt.replace(u"\u00A0", " ")
            txt = fromstring(txt).text_content()
            txt = re.sub(r"\n[ \t]+", "\n", txt)
            return txt.strip()

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
            txt = re.sub("^. ", "", txt)
            txt  = txt.strip()
            return txt

        lxs = LxmlSelector(response)
        item = response.meta["item"]
        meta = self.meta_as_dict(lxs)
        etree.strip_tags(lxs.xmlNode, "b", "font", "i")

        info_node = lxs.xpath("//a[@name = 'PDT']/ancestor::td[1]")
        if info_node:
            item["info"] = get_text_formatted(info_node[0])
        amendments_node = lxs.xpath("//a[@name = 'PAC']/ancestor::td[1]")
        if amendments_node:
            item["amendments"] = get_text_formatted(amendments_node[0])
        summary_node = lxs.xpath("//a[@name = 'ECRCM']/ancestor::td[1]")
        if summary_node:
            item["summary"] = get_text_formatted(summary_node[0])

        file_href = meta.get("URL_DOSSIER") or None
        if file_href:
            file_href = urljoin(response.url, file_href)
        item["law"] = LawItem(
            title=meta.get("LOI_PROMULGUEE", ""),
            href=meta.get("LIEN_LOI_PROMULGUEE", ""),
            file_href=file_href,
        )

        yield item
