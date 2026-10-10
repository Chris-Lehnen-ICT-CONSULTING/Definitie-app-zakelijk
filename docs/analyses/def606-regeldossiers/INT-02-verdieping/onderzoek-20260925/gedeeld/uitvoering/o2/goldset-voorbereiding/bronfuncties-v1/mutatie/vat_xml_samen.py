"""Vat junit-xml's van de mutatieruns samen: gefaalde tests per testfunctie.

Gebruik: python vat_xml_samen.py resultaten/herstel2-<naam>.xml [...]
"""

import collections
import sys
import xml.etree.ElementTree as ET

for pad in sys.argv[1:]:
    boom = ET.parse(pad)
    suite = next(boom.iter("testsuite"))
    gefaald = collections.Counter(
        tc.get("name").split("[")[0]
        for tc in boom.iter("testcase")
        if tc.find("failure") is not None or tc.find("error") is not None
    )
    sys.stdout.write(f"{pad}: {suite.get('failures')} gefaald / {suite.get('tests')}\n")
    for naam, aantal in sorted(gefaald.items()):
        sys.stdout.write(f"    {aantal:3d}  {naam}\n")
