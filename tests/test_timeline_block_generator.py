import unittest
from src.timeline_block_generator import TimelineBlockGenerator

class TestTimelineBlockGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = TimelineBlockGenerator()

    def test_generate_blocks(self):
        # Example test for generating blocks
        frames = 10
        path_life = 0.5
        stability = 3.0
        blocks = self.generator.generate_blocks(frames, path_life, stability, mode='blocks')
        self.assertEqual(len(blocks), frames)
        self.assertTrue(all(isinstance(block, bool) for block in blocks))

    def test_generate_blocks_random(self):
        # Example test for generating random blocks
        frames = 10
        path_life = 0.5
        stability = 1.0
        blocks = self.generator.generate_blocks(frames, path_life, stability, mode='random')
        self.assertEqual(len(blocks), frames)
        self.assertTrue(all(isinstance(block, bool) for block in blocks))

if __name__ == '__main__':
    unittest.main()