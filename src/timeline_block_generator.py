from typing import List, Tuple
import random

class TimelineBlockGenerator:
    """
    TimelineBlockGenerator is responsible for generating blocks of timelines
    based on specified criteria. It includes methods for creating and managing
    timeline blocks.
    """

    def __init__(self, frames: int, path_life: float, stability: float, mode: str = "blocks"):
        self.frames = frames
        self.path_life = path_life
        self.stability = stability
        self.mode = mode

    def generate_blocks(self) -> List[bool]:
        """
        Generate a sequence of booleans representing timeline blocks.
        True indicates "path up" and False indicates "path down".
        """
        if self.frames <= 0:
            return []

        up_count = int(round(self.frames * self.path_life))
        down_count = self.frames - up_count

        if self.mode == "random":
            timeline = [True] * up_count + [False] * down_count
            random.shuffle(timeline)
            return timeline

        # blocks mode: stability is average block length (>=1)
        stability = max(1.0, float(self.stability))
        approx_blocks = max(1, int(round(self.frames / stability)))
        blocks = []
        remaining_up = up_count
        remaining_down = down_count
        state = random.choice([True, False])

        for b in range(approx_blocks):
            remaining_frames = remaining_up + remaining_down
            if remaining_frames <= 0:
                break

            size = self._allocate_block_size(state, remaining_up, remaining_down, approx_blocks - b)
            if size > 0:
                blocks.append((state, size))
                if state:
                    remaining_up -= size
                else:
                    remaining_down -= size
            state = not state

        return self._build_timeline_from_blocks(blocks)

    def _allocate_block_size(self, state: bool, remaining_up: int, remaining_down: int, remaining_blocks: int) -> int:
        """
        Allocate block size based on the current state and remaining counts.
        """
        if state:
            max_alloc = remaining_up - max(0, remaining_blocks - 1) * 0
            target = max(1, int(round(remaining_up / remaining_blocks)))
            return min(max(1, target), remaining_up) if remaining_up > 0 else 0
        else:
            max_alloc = remaining_down - max(0, remaining_blocks - 1) * 0
            target = max(1, int(round(remaining_down / remaining_blocks)))
            return min(max(1, target), remaining_down) if remaining_down > 0 else 0

    def _build_timeline_from_blocks(self, blocks: List[Tuple[bool, int]]) -> List[bool]:
        """
        Build the timeline from the generated blocks.
        """
        timeline = []
        for st, size in blocks:
            timeline.extend([bool(st)] * size)

        # Final adjustment to ensure the timeline matches the specified frame count
        if len(timeline) > self.frames:
            return timeline[:self.frames]
        elif len(timeline) < self.frames:
            if timeline:
                timeline.extend([timeline[-1]] * (self.frames - len(timeline)))
            else:
                timeline = [False] * self.frames
        return timeline