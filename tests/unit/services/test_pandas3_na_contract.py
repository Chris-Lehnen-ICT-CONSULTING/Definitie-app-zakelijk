#!/usr/bin/env python3
"""Regressie-vangnet voor de pandas 3.0 NA-aanname — DEF-411.

`services.definition_import_service._clean_text` (regel ~268) detecteert lege
CSV-cellen met:

    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""

Die check leunt erop dat een missing value uit `pd.read_csv` een *float* `NaN`
is (en geen `pd.NA`/`None`/literal-string). Pandas 3.0 introduceerde via
PDEP-14 een default string-dtype; die gebruikt bewust `np.nan` als NA-marker
(backward-compat), dus de aanname blijft gelden. Deze test borgt dat contract,
zodat een toekomstige pandas-wijziging die de NA-representatie verandert hier
zichtbaar faalt i.p.v. stil `"<NA>"` de import in te lekken.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest

pytestmark = [pytest.mark.unit]

_CSV_MET_LEGE_CEL = "begrip,definitie\nTest,Een definitie\nLeeg,\n"


def _read_missing_value():
    """Lees de lege cel (rij 'Leeg', kolom 'definitie') via read_csv."""
    df = pd.read_csv(io.StringIO(_CSV_MET_LEGE_CEL))
    return df["definitie"].iloc[1]


def test_read_csv_missing_value_is_float_nan():
    """Pandas 3.0: een lege CSV-cel komt als float NaN, detecteerbaar via isna."""
    value = _read_missing_value()
    assert isinstance(value, float)
    assert pd.isna(value)


def test_clean_text_predicate_geeft_lege_string_voor_na():
    """Repliceert de _clean_text-predicaat: NA → '' (geen literal '<NA>'/'nan')."""
    value = _read_missing_value()

    # Exact dezelfde guard als definition_import_service._clean_text
    if value is None or (isinstance(value, float) and pd.isna(value)):
        cleaned = ""
    else:
        cleaned = str(value).strip()

    assert cleaned == ""


def test_gevulde_cel_blijft_behouden():
    """Een gevulde cel passeert de NA-guard en behoudt zijn waarde."""
    df = pd.read_csv(io.StringIO(_CSV_MET_LEGE_CEL))
    value = df["definitie"].iloc[0]
    assert not (isinstance(value, float) and pd.isna(value))
    assert str(value).strip() == "Een definitie"
