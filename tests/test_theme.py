import json

from ui.theme import Theme


def test_theme_defaults_when_file_missing(tmp_path) -> None:
    theme = Theme.load(tmp_path / "does_not_exist.json")
    assert theme == Theme()


def test_theme_loads_values_from_file(tmp_path) -> None:
    path = tmp_path / "theme.json"
    path.write_text(
        json.dumps(
            {
                "theme": {
                    "primaryColor": "#FF0000",
                    "backgroundOpacity": 0.5,
                    "glow": False,
                    "animations": False,
                }
            }
        )
    )
    theme = Theme.load(path)
    assert theme.primary_color == "#FF0000"
    assert theme.background_opacity == 0.5
    assert theme.glow is False
    assert theme.animations is False
    # Nicht angegebene Werte fallen auf die Standardwerte zurueck.
    assert theme.secondary_color == Theme().secondary_color


def test_theme_falls_back_to_defaults_on_invalid_json(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not valid json")
    theme = Theme.load(path)
    assert theme == Theme()


def test_theme_save_and_reload_roundtrip(tmp_path) -> None:
    path = tmp_path / "theme.json"
    original = Theme(primary_color="#123456", background_opacity=0.42, glow=False)
    original.save(path)

    reloaded = Theme.load(path)

    assert reloaded == original
