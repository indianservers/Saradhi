"""Crop each labeled screen from the supplied Quickbuddy montage boards."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Target UI"
DESTINATION = ROOT / "docs" / "ui" / "reference-crops"

# Coordinates are approximate screen-panel bounds on the 1448 x 1086 source
# boards. They include each screen's local caption where space allows.
BOARDS = {
    "customer": (
        "quickbuddy_everything_delivered_happier.png",
        [
            (25, 100, 290, 630), (302, 100, 574, 630),
            (580, 100, 853, 630), (860, 100, 1155, 630),
            (1164, 100, 1444, 630), (25, 663, 290, 1083),
            (302, 663, 574, 1083), (580, 663, 853, 1083),
            (860, 663, 1155, 1083), (1164, 663, 1444, 1083),
        ],
    ),
    "pilot": (
        "quickbuddy_rider_app_showcase.png",
        [
            (25, 92, 296, 588), (306, 92, 585, 588),
            (585, 92, 864, 588), (864, 92, 1148, 588),
            (1148, 92, 1442, 588), (25, 625, 296, 1084),
            (306, 625, 585, 1084), (585, 625, 864, 1084),
            (864, 625, 1148, 1084), (1148, 625, 1442, 1084),
        ],
    ),
    "merchant": (
        "quickbuddy_restaurant_partner_app_showcase.png",
        [
            (15, 155, 300, 680), (300, 155, 585, 680),
            (585, 155, 870, 680), (870, 155, 1155, 680),
            (1155, 155, 1443, 680), (15, 685, 300, 1084),
            (300, 685, 585, 1084), (585, 685, 870, 1084),
            (870, 685, 1155, 1084), (1155, 685, 1443, 1084),
        ],
    ),
    "admin": (
        "quickbuddy_admin_control_center_showcase.png",
        [
            (5, 68, 516, 458), (516, 68, 1037, 458),
            (1037, 68, 1443, 458), (5, 458, 516, 840),
            (516, 458, 998, 840), (998, 458, 1443, 840),
            (5, 840, 407, 1084), (407, 840, 800, 1084),
            (800, 840, 1060, 1084), (1060, 840, 1443, 1084),
        ],
    ),
}


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for app, (filename, rectangles) in BOARDS.items():
        with Image.open(SOURCE / filename) as board:
            for index, bounds in enumerate(rectangles, 1):
                crop = board.crop(bounds)
                crop.save(DESTINATION / f"{app}-{index:02}.png", optimize=True)
                crop.close()


if __name__ == "__main__":
    main()
