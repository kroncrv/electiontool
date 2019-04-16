# electiontool.py
> Command line utility to convert data from Dutch elections in EML XML files to a CSV file that has data per party per stembureau. Written in Python 3.

## Installation
You'll need to have the packages `dataknead`, `xmltodict` and `dpath` installed.

## Examples
Parse all XML files in a directory called `data` and output as a CSV file called `ps2019.csv`:

    ./electiontool.py -i data -o ps2019.csv

Also add percentages aside from absolute votes

    ./electiontool.py -i data -o ps2019.csv --add-percentages

Parse one single XML file to a csv file

    ./electiontool.py -i terschelling.xml -o terschelling.csv

## Troubleshooting
* Before opening an issue, try running your command with the `-v` (verbose) switch, because this will give you more debug information.

## All options
You'll get this output when running `electiontool.py -h`.

```bash
usage: electiontool.py [-h] -i INPUT [-if {emlxml}] -o OUTPUT
                       [--add-percentages] [-v]

Convert data from Dutch elections in EML XML files to a CSV file that has data
per party per stembureau.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file or directory
  -if {emlxml}, --input-format {emlxml}
                        Input format
  -o OUTPUT, --output OUTPUT
                        Output CSV file (remember to add a CSV extension)
  --add-percentages     Add percentages per party apart from absolute votes
  -v, --verbose         Display debug information
```

## License
Licensed under the [MIT license](https://opensource.org/licenses/MIT).

## Credits
Written by Hay Kranen for Pointer(https://www.pointer.nl).