from decimal import Decimal
import unittest

from app.services.anomaly_service import detect_price_anomaly
from app.services.location_utils import parse_lat_lon
from app.services.scoring import MatchScoreInputs, calculate_match_score


class Phase4PureServiceTests(unittest.TestCase):
    def test_authorized_nearby_pickup_recycler_scores_higher_than_far_unverified_recycler(self):
        strong = calculate_match_score(
            MatchScoreInputs(
                distance_km=2.0,
                offered_rate=160.0,
                authorization_status="authorized",
                pickup_available=True,
            )
        )
        weak = calculate_match_score(
            MatchScoreInputs(
                distance_km=40.0,
                offered_rate=80.0,
                authorization_status="unverified",
                pickup_available=False,
            )
        )
        self.assertGreater(strong, weak)


    def test_anomaly_detection_flags_large_price_gap(self):
        result = detect_price_anomaly(
            quoted_price=Decimal("50"),
            final_price=Decimal("50"),
            category_median_price=Decimal("100"),
        )
        self.assertTrue(result.is_anomaly)


    def test_parse_lat_lon_accepts_valid_location(self):
        self.assertEqual(parse_lat_lon("19.0760,72.8777"), (19.076, 72.8777))


if __name__ == "__main__":
    unittest.main()
