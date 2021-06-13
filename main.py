from itertools import product
from more_itertools import collapse

from typing import Tuple, Iterable, Set, Union, List


def unravel(idx: int, shape: Tuple[int, ...]) -> Tuple[int, int]:
    _, cols = shape
    return idx // cols, idx % cols


def flatten(idx: Tuple[int, int], shape: Tuple[int, ...]) -> int:
    _, cols = shape
    return idx[0] * cols + idx[1]


class Board(List[bool]):

    def __init__(self, shape: Tuple[int, int], iterable: Iterable):
        self.__shape = shape
        list_ = list(collapse(iterable))
        assert len(list_) == self.rows * self.cols
        super(Board, self).__init__(list_)

    @property
    def rows(self) -> int:
        return self.shape[0]

    @property
    def cols(self) -> int:
        return self.shape[1]

    @property
    def shape(self) -> Tuple[int, int]:
        return self.__shape

    def __getitem__(self, idx: Union[int, Tuple[int, int]]) -> bool:
        return super(Board, self).__getitem__(self.__validate_idx(idx))

    def __setitem__(self, idx: Union[int, Tuple[int, int]], value):
        super(Board, self).__setitem__(self.__validate_idx(idx), value)

    def __validate_idx(self, idx: Union[int, Tuple[int, int]]) -> int:
        if isinstance(idx, tuple):
            assert len(idx) == 2  # 2D life
            idx = self.__flatten(idx)
        elif isinstance(idx, int):
            pass
        else:
            raise TypeError(f'{type(self).__name__} indices must be integers, not {type(idx).__name__}')

        if 0 > idx >= len(self):
            raise IndexError(f'{idx} index out of range for {type(self).__name__} of size {self.shape}')

        return idx

    def __flatten(self, idx: Tuple[int, int]) -> int:
        return flatten(idx, self.shape)

    def __unravel(self, idx: int) -> Tuple[int, int]:
        return unravel(idx, self.shape)


class Life:
    __board: Board
    __alive_cells: Set[int]

    def __init__(self, board: Board):
        self.board = board

    @property
    def board(self) -> Board:
        return self.__board

    @board.setter
    def board(self, new_board: Board):
        self.__board = new_board
        self.__alive_cells = set(i for i, val in enumerate(self.board) if val)

    @property
    def dead(self):
        return not self.__alive_cells

    @property
    def alive(self):
        return bool(self.__alive_cells)

    def __str__(self):
        s = '-' * (self.board.cols + 2) + '\n'
        for idx, val in enumerate(self.board):
            row, col = unravel(idx, self.board.shape)
            if col == 0:
                s += '|'
            s += '#' if val else ' '
            if col + 1 == self.board.cols:
                s += '|\n'
        s += '-' * (self.board.cols + 2) + '\n'
        return s

    def update(self):
        to_set_alive = list()
        to_set_dead = list()

        for idx in self.__cells_to_check:
            if self.__should_die(idx):
                to_set_dead.append(idx)
                continue
            if self.__should_resurrect(idx):
                to_set_alive.append(idx)
                continue

        for idx in to_set_alive:
            self.board[idx] = True
            self.__alive_cells.add(idx)

        for idx in to_set_dead:
            self.board[idx] = False
            self.__alive_cells.discard(idx)

    @property
    def __cells_to_check(self) -> Set[int]:
        return self.__alive_cells.union(*[self.__get_neighbours_idx(idx) for idx in self.__alive_cells])

    def __should_die(self, idx: int) -> bool:
        if not self.board[idx]:
            return False

        n_alive_neighbours = len(self.__get_alive_neighbours(idx))
        return n_alive_neighbours > 3 or n_alive_neighbours < 2

    def __should_resurrect(self, idx: int) -> bool:
        if self.board[idx]:
            return False

        n_alive_neighbours = len(self.__get_alive_neighbours(idx))
        return n_alive_neighbours == 3

    def __get_neighbours_idx(self, idx: int) -> Set[int]:
        row, col = unravel(idx, self.board.shape)
        neighbours = {
            flatten((row + r, col + c), self.board.shape) for r, c in product((-1, 0, 1), repeat=2)
            if 0 <= row + r < self.board.rows and 0 <= col + c < self.board.cols
        }
        neighbours.discard(idx)
        return neighbours

    def __get_alive_neighbours(self, idx):
        return self.__alive_cells.intersection(self.__get_neighbours_idx(idx))


def test():
    from random import randint

    # seed(666)
    rows, cols = 10, 100
    seed = [bool(randint(0, 1)) for _ in range(rows * cols)]
    life = Life(Board((rows, cols), seed))

    print(life)
    while not life.dead:
        life.update()
        print(life)


if __name__ == '__main__':
    test()
