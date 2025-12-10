import unittest
from src.visualizer import TimelineVisualizer

class TestTimelineVisualizer(unittest.TestCase):

    def setUp(self):
        self.visualizer = TimelineVisualizer()

    def test_visualize_timeline(self):
        # Example timeline data
        timeline_data = [True, False, True, True, False]
        result = self.visualizer.visualize(timeline_data)
        self.assertIsNotNone(result)
        self.assertIn("Timeline Visualization", result)

    def test_render_format(self):
        timeline_data = [True, False, True]
        result = self.visualizer.render(timeline_data, format='text')
        self.assertIsInstance(result, str)

    def test_invalid_render_format(self):
        timeline_data = [True, False]
        with self.assertRaises(ValueError):
            self.visualizer.render(timeline_data, format='invalid_format')

if __name__ == '__main__':
    unittest.main()