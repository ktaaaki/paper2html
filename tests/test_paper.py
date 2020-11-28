import pytest
from paper2html.paper import BBox


def test_bbox_collided():
    bbox0 = BBox((1, 1, 2, 2))
    bbox1 = BBox((2, 2, 3, 3))
    assert not BBox.collided(bbox0, bbox1)
