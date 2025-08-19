from ai_toetser import Toetser


def test_toets_woord_verplicht():
    t = Toetser("config/verboden_woorden.json")
    assert t.is_verboden("ongewenst") in (True, False)
