# electiontool.py
> Command line utility to convert data from Dutch elections in EML XML files to a CSV file that has data per party per stembureau and/or per candidate. Written in Python 3.

## Installation
You'll need to have the packages `dataknead`, `xmltodict` and `dpath` installed.

You can also use [poetry](https://poetry.eustace.io/) to install dependencies and create a virtual environment

```bash
poetry install
poetry run ./electiontool.py
```

## Examples
Parse all XML files in a directory called `data` and output as a CSV file called `ps2019.csv`:

    ./electiontool.py -i data -o ps2019.csv

Also add percentages aside from absolute votes

    ./electiontool.py -i data -o ps2019.csv --add-percentages

Parse one single XML file to a csv file

    ./electiontool.py -i terschelling.xml -o terschelling.csv

Output results with votes per candidate (note that this might lead to large CSV files). A couple of columns are removed to reduce the file size.

    ./electiontool.py -i data -o ps2019.csv --output-structure candidates

## Troubleshooting
* Before opening an issue, try running your command with the `-v` (verbose) switch, because this will give you more debug information.

## All options
You'll get this output when running `electiontool.py -h`.

```bash
usage: electiontool.py [-h] [--add-percentages] -i INPUT [-if {emlxml}] -o
                       OUTPUT [-os {parties,candidates}] [-v]

Convert data from Dutch elections in EML XML files to a CSV file that has data
per party per stembureau.

optional arguments:
  -h, --help            show this help message and exit
  --add-percentages     Add percentages per party apart from absolute votes
  -i INPUT, --input INPUT
                        Input file or directory
  -if {emlxml}, --input-format {emlxml}
                        Input format
  -o OUTPUT, --output OUTPUT
                        Output CSV file (remember to add a CSV extension)
  -os {parties,candidates}, --output-structure {parties,candidates}
                        Structure of the output file, per party (default) or
                        per candidate. Note that this will eliminate some
                        columns to reduce file size.
  -v, --verbose         Display debug information
```

## License
Licensed under the [MIT license](https://opensource.org/licenses/MIT).

## Credits
Written by Hay Kranen for [Pointer](https://www.pointer.nl).