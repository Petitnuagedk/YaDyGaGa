import unittest
from src.DynaGraph import DynamicGraph

class TestTimelineAssembler(unittest.TestCase):

    def setUp(self):
        self.assembler = TimelineAssembler()

    def test_assemble_timeline(self):
        # Example test for assembling a timeline
        blocks = [
            [True, True, False],
            [False, True, True],
        ]
        expected_timeline = [True, True, False, False, True, True]
        assembled_timeline = self.assembler.assemble_timeline(blocks)
        self.assertEqual(assembled_timeline, expected_timeline)

    def test_empty_blocks(self):
        # Test assembling with empty blocks
        blocks = []
        expected_timeline = []
        assembled_timeline = self.assembler.assemble_timeline(blocks)
        self.assertEqual(assembled_timeline, expected_timeline)

    def test_single_block(self):
        # Test assembling a single block
        blocks = [[True, False, True]]
        expected_timeline = [True, False, True]
        assembled_timeline = self.assembler.assemble_timeline(blocks)
        self.assertEqual(assembled_timeline, expected_timeline)

if __name__ == '__main__':
    unittest.main()