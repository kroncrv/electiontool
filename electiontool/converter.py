import glob
import re
import sys
import xmltodict
import logging
logger = logging.getLogger(__name__)

from dataknead import Knead
from dpath import util
from pathlib import Path

BUREAU_REGEX = re.compile("(.*)\(postcode: (.*)\)")
FIELDS = [
    "gemeente", "gemeente_id", "bureau_label", "bureau_zip",
    "total_counted", "cast", "votes_ongeldig", "votes_blanco"
]

def read_xml(path):
    with open(path) as f:
        data = f.read()

    return xmltodict.parse(data)

def yield_path(path, extension = None):
    if Path(path).is_dir():
        if not extension:
            raise ValueError(f"Extension is required for iterating over directory")

        for path in glob.glob(f"{path}/*.{extension}"):
            yield path
    else:
        yield path

class Converter:
    def __init__(self, input_path, input_format, output_path, add_percentages):
        self.fields = FIELDS.copy()
        self.input_path = input_path

        if input_format == "emlxml":
            results = self.parse_xmls()

        if add_percentages:
            results = self.add_percentages(results)

        Knead(results).write(output_path, fieldnames = self.fields)

    def add_percentages(self, rows):
        data = []

        for row in rows:
            total = row["total_counted"]

            if total == 0:
                continue

            newrow = row.copy()

            for k,v in row.items():
                if v and isinstance(v, int):
                    perc = "%s_percentage" % k

                    if perc not in self.fields:
                        self.fields.append(perc)

                    newrow[perc] = int(v) / total

            data.append(newrow)

        return data

    def parse(self, data):
        results = []
        contest = util.get(data, "/EML/Count/Election/Contests/Contest")
        gemeente = util.get(data, "/EML/ManagingAuthority/AuthorityIdentifier/#text")
        gemeente_id = util.get(data, "/EML/ManagingAuthority/AuthorityIdentifier/@Id")

        # Some place don't have *any* ReportingUnitVotes in their XML
        # (looking at you, Terschelling), so let's create something from the
        # TotalVotes
        if "ReportingUnitVotes" not in contest:
            units = [ contest["TotalVotes"] ]
        else:
            units = contest["ReportingUnitVotes"]

        # Some places only have *one* stembureau, in that case we're going to
        # get a dict instead of a list, so make sure that works
        if not isinstance(units, list):
            units = [ units ]

        for unit in units:
            if isinstance(unit, str):
                continue

            # Get label and zipcode for bureau
            if "ReportingUnitIdentifier" not in unit:
                bureau = {
                    "label" : "Unknown",
                    "zip" : None
                }
            else:
                bureau = self.parse_bureau(unit["ReportingUnitIdentifier"]["#text"])

            # Some general information
            bdata = {
                "gemeente" : gemeente,
                "gemeente_id" : gemeente_id,
                "bureau_label" : bureau["label"],
                "bureau_zip" : bureau["zip"]
            }

            # Get the total votes for every party
            for selection in unit["Selection"]:
                if "AffiliationIdentifier" in selection:
                    name = selection["AffiliationIdentifier"]["RegisteredName"]
                    votes = int(selection["ValidVotes"])

                    if name not in self.fields:
                        self.fields.append(name)

                    bdata[name] = votes

            # Also get some stats on other things
            bdata["cast"] = int(unit["Cast"])
            bdata["total_counted"] = int(unit["TotalCounted"])

            # Rejected votes with reasons
            for rejected in unit["RejectedVotes"]:
                code = "votes_" + rejected["@ReasonCode"]
                count = int(rejected["#text"])
                bdata[code] = count

            results.append(bdata)

        return results

    def parse_bureau(self, unit):
        results = BUREAU_REGEX.findall(unit)

        if len(results) == 0:
            # Some bureaus don't have zipcodes
            return {
                "label" : unit,
                "zip" : None
            }
        else:
            return {
                "label" : results[0][0].strip(),
                "zip" : results[0][1].strip()
            }

    def parse_xmls(self):
        results = []

        for path in yield_path(self.input_path, "xml"):
            logger.info(f"Parsing <{path}>")
            data = read_xml(path)

            if not data:
                raise Exception(f"Could not parse xml file {path}")

            data = self.parse(data)

            if data:
                results = results + data
            else:
                logger.info(f"Could not parse the data from <{path}>")

        return results