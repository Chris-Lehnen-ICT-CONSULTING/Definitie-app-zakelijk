import pytest

from ai_toetser import Toetser

pytestmark = [pytest.mark.unit]


def test_toets_woord_verplicht():
    t = Toetser("config/verboden_woorden.json")
    assert t.is_verboden("ongewenst") in (True, False)
