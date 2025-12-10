from src.frame_generator import FrameGenerator
import unittest

class TestFrameGenerator(unittest.TestCase):

    def setUp(self):
        self.frame_generator = FrameGenerator()

    def test_generate_frames(self):
        # Example test for frame generation
        frames = self.frame_generator.generate_frames(10, 0.5, 3.0)
        self.assertEqual(len(frames), 10)
        self.assertTrue(all(isinstance(frame, bool) for frame in frames))

    def test_edge_case_no_frames(self):
        frames = self.frame_generator.generate_frames(0, 0.5, 3.0)
        self.assertEqual(frames, [])

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.frame_generator.generate_frames(10, -0.1, 3.0)

if __name__ == '__main__':
    unittest.main()