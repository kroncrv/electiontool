#!/usr/bin/env python3
from argparse import ArgumentParser
from electiontool.converter import Converter, INPUT_FORMATS, OUTPUT_STRUCTURES
import logging
import sys
logger = logging.getLogger(__name__)

def get_parser():
    parser = ArgumentParser(
        description = """
        Convert data from Dutch elections in EML XML files to a CSV file that
        has data per party per stembureau.
        """
    )

    parser.add_argument("--add-contestname", action = "store_true",
        help = "Add contestname to output",
        default = False
    )

    parser.add_argument(
        "--add-percentages", action = "store_true",
        help = "Add percentages per party apart from absolute votes",
        default = False
    )

    parser.add_argument("-i", "--input", type = str, required = True,
        help = "Input file or directory"
    )

    parser.add_argument(
        "-if", "--input-format", choices = INPUT_FORMATS,
        help = "Input format",
        default = "emlxml"
    )

    parser.add_argument("-o", "--output", type = str, required = True,
        help = "Output CSV file (remember to add a CSV extension)"
    )

    parser.add_argument("-os", "--output-structure",
        choices = OUTPUT_STRUCTURES,
        default = "parties",
        help = "Structure of the output file, per party (default) or per \
                candidate. Note that this will eliminate some columns to \
                reduce file size."
    )

    parser.add_argument("-v", "--verbose", action = "store_true",
        help = "Display debug information"
    )

    return parser

def main(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug(args)

    Converter(
        input_path = args.input,
        input_format = args.input_format,
        output_path = args.output,
        add_percentages = args.add_percentages,
        output_structure = args.output_structure,
        add_contestname = args.add_contestname
    )

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    try:
        main(args)
    except AssertionError as e:
        if args.verbose:
            raise(e)

        sys.exit("Assertion error, check your arguments (run with -v)")