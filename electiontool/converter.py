from dataknead import Knead
from dpath import util
from pathlib import Path
import glob
import logging
import re
import sys
import xmltodict

logger = logging.getLogger(__name__)

BUREAU_REGEX = re.compile("(.*)\(postcode: (.*)\)")
CANDIDATE_FIELDS = [
    "bureau_id", "bureau_zip", "count_type", "party", "candidate_id", "count"
]
INPUT_FORMATS = ["emlxml"]
OUTPUT_STRUCTURES = ["parties", "candidates"]
PARTIES_FIELDS = [
    "gemeente", "gemeente_id", "bureau_id", "bureau_label", "bureau_zip",
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
    def __init__(self,
        input_path,
        input_format,
        output_path,
        output_structure,
        add_percentages = False,
        add_contestname = False
    ):
        # Validation
        assert input_format in INPUT_FORMATS
        assert output_structure in OUTPUT_STRUCTURES
        assert Path(output_path).suffix == ".csv"

        self.add_contestname = add_contestname
        self.add_percentages = add_percentages
        self.input_format = input_format
        self.input_path = input_path
        self.output_path = output_path
        self.output_structure = output_structure

        if self.output_structure == "parties":
            self.fields = PARTIES_FIELDS.copy()
        elif self.output_structure == "candidates":
            self.fields = CANDIDATE_FIELDS.copy()

        if self.add_contestname:
            self.fields.insert(0, "contestname")

        self.run()

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
            logger.info(f"No ReportingUnitVotes for '{gemeente}', taking TotalVotes")
            units = [ contest["TotalVotes"] ]
        else:
            units = contest["ReportingUnitVotes"]

        # Some places only have *one* stembureau, in that case we're going to
        # get a dict instead of a list, so make sure that works
        if not isinstance(units, list):
            logger.info(f"Only one stembureau for '{gemeente}'")
            units = [ units ]

        for unit in units:
            if isinstance(unit, str):
                continue

            # Get label and zipcode for bureau
            if "ReportingUnitIdentifier" not in unit:
                logger.info(f"No ReportingUnitIdentifier for '{gemeente}', making something up")
                bureau = {
                    "id" : None,
                    "label" : "Unknown",
                    "zip" : None
                }
            else:
                bureau = self.parse_bureau(unit["ReportingUnitIdentifier"])

            # These two fields are in both output structures
            bdata = {
                "bureau_id" : bureau["id"],
                "bureau_zip" : bureau["zip"]
            }

            # Optional field
            if self.add_contestname:
                bdata["contestname"] = contest["ContestIdentifier"]["ContestName"]

            # And these two only appear in the 'parties' structure
            if self.output_structure == "parties":
                bdata.update({
                    "gemeente" : gemeente,
                    "gemeente_id" : gemeente_id,
                    "bureau_label" : bureau["label"],
                })

            if self.output_structure == "parties":
                # Parties always return *one* dict
                results += [ self.parse_as_party(bdata, unit) ]
            elif self.output_structure == "candidates":
                # Candidates always returns a *list* of dicts
                results += self.parse_as_candidate(bdata, unit)

        return results

    def parse_as_candidate(self, bdata, unit):
        results = []

        # Get the total votes for every party
        party = None

        for selection in unit["Selection"]:
            new_b = bdata.copy()

            if "AffiliationIdentifier" in selection:
                party = selection["AffiliationIdentifier"]["RegisteredName"]

            if "Candidate" in selection:
                candidate_id = selection["Candidate"]["CandidateIdentifier"]["@Id"]
                new_b["party"] = party
                new_b["candidate_id"] = candidate_id
                new_b["count_type"] = "candidate"
                new_b["count"] = int(selection["ValidVotes"])
                results.append(new_b)

        # Also get some stats on other things
        new_b = bdata.copy()
        new_b["count_type"] = "cast"
        new_b["count"] = int(unit["Cast"])
        results.append(new_b)

        new_b = bdata.copy()
        new_b["count_type"] = "total_counted"
        new_b["count"] = int(unit["TotalCounted"])
        results.append(new_b)

        # Rejected votes with reasons
        for rejected in unit["RejectedVotes"]:
            new_b = bdata.copy()
            code = "votes_" + rejected["@ReasonCode"]
            count = int(rejected["#text"])
            new_b["count_type"] = code
            new_b["count"] = count
            results.append(new_b)

        return results

    def parse_as_party(self, bdata, unit):
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

        return bdata

    def parse_bureau(self, unit):
        bureau_id = unit["@Id"]
        bureau = unit["#text"]
        results = BUREAU_REGEX.findall(bureau)

        if len(results) == 0:
            # Some bureaus don't have zipcodes
            return {
                "id" : bureau_id,
                "label" : bureau,
                "zip" : None
            }
        else:
            return {
                "id" : bureau_id,
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

    def run(self):
        if self.input_format == "emlxml":
            results = self.parse_xmls()

        if self.add_percentages:
            results = self.add_percentages(results)

        Knead(results).write(self.output_path, fieldnames = self.fields)