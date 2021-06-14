from dataclasses import dataclass, field
from itertools import product
from functools import partialmethod
from typing import Tuple, Iterable, Set, Union, List, Optional, Callable


def unravel(idx: int, shape: Tuple[int, ...]) -> Tuple[int, int]:
    _, cols = shape
    return idx // cols, idx % cols


def flatten(idx: Tuple[int, int], shape: Tuple[int, ...]) -> int:
    _, cols = shape
    return idx[0] * cols + idx[1]


@dataclass
class Cell:
    __alive: bool = field(default=False)

    def __repr__(self):
        return f'{type(self).__name__}(alive={self.alive})'

    @property
    def alive(self):
        return self.__alive

    @property
    def dead(self):
        return not self.alive

    def set_state(self, state: bool):
        self.__alive = state

    set_alive = partialmethod(set_state, True)  # type: Callable[..., None]

    set_dead = partialmethod(set_state, False)  # type: Callable[..., None]


class Board(List[Cell]):

    def __init__(self, shape: Tuple[int, int], *, initial: Optional[List[Cell]] = None):
        self.__shape = shape
        if initial is None:
            initial = [Cell() for _ in range(self.rows * self.cols)]
        assert len(initial) == self.rows * self.cols
        super(Board, self).__init__(initial)

    def __repr__(self):
        return f'{type(self).__name__}(shape={self.shape}, initial={super(Board, self).__repr__()})'

    __str__ = __repr__

    @classmethod
    def from_list(cls, shape: Tuple[int, int], list_: Union[List[int], List[bool]]) -> 'Board':
        return cls(shape, initial=[Cell(bool(state)) for state in list_])

    @classmethod
    def from_indices(cls, shape: Tuple[int, int], list_: Iterable[int]) -> 'Board':
        return cls(shape, initial=[Cell(idx in list_) for idx in range(shape[0] * shape[1])])

    @classmethod
    def from_2d_list(cls, list_: Union[List[List[int]], List[List[bool]]]) -> 'Board':
        shape = len(list_), len(list_[0])
        return cls(shape, initial=[Cell(bool(state)) for row in list_ for state in row])

    @classmethod
    def from_2d_indices(cls, shape: Tuple[int, int], list_: Iterable[Tuple[int, int]]) -> 'Board':
        return cls(shape, initial=[Cell(unravel(idx, shape) in list_) for idx in range(shape[0] * shape[1])])

    @property
    def rows(self) -> int:
        return self.shape[0]

    @property
    def cols(self) -> int:
        return self.shape[1]

    @property
    def shape(self) -> Tuple[int, int]:
        return self.__shape

    def __getitem__(self, idx: Union[int, Tuple[int, int]]) -> Cell:
        return super(Board, self).__getitem__(self.__validate_idx(idx))

    def __setitem__(self, idx: Union[int, Tuple[int, int]], value: Cell):
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

    generation: int

    def __init__(self, board: Board):
        self.board = board
        self.generation = 0

    @property
    def board(self) -> Board:
        return self.__board

    @board.setter
    def board(self, new_board: Board):
        self.__board = new_board
        self.__alive_cells = set(i for i, cell in enumerate(self.board) if cell.alive)

    @property
    def dead(self):
        return not self.__alive_cells

    @property
    def alive(self):
        return bool(self.__alive_cells)

    def __repr__(self):
        return f'{type(self).__name__}(generation={self.generation}, board={repr(self.board)})'

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
            self.board[idx].set_alive()
            self.__alive_cells.add(idx)

        for idx in to_set_dead:
            self.board[idx].set_dead()
            self.__alive_cells.discard(idx)

        self.generation += 1

    @property
    def __cells_to_check(self) -> Set[int]:
        return self.__alive_cells.union(*[self.__get_neighbours_idx(idx) for idx in self.__alive_cells])

    def __should_die(self, idx: int) -> bool:
        if self.board[idx].dead:
            return False

        n_alive_neighbours = len(self.__get_alive_neighbours(idx))
        return n_alive_neighbours > 3 or n_alive_neighbours < 2

    def __should_resurrect(self, idx: int) -> bool:
        if self.board[idx].alive:
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


class LifePrinter:

    @staticmethod
    def print(life: Life):
        board = life.board
        s = f'Generation №{life.generation}\n'
        s += '_' * (board.cols + 2) + '\n'
        for idx, cell in enumerate(board):
            row, col = unravel(idx, board.shape)
            s += '|' if col % board.cols == 0 else ''
            s += '#' if cell.alive else ' '
            s += '|\n' if col % board.cols == board.cols - 1 else ''
        s += '_' * (board.cols + 2)
        print(s)


def test():
    rows, cols = 30, 100
    seed = [1 if (_ % cols in (0, cols - 1)) or (_ // cols) in (0, rows - 1) else 0 for _ in range(rows * cols)]
    life = Life(Board.from_list((rows, cols), seed))

    print(life)
    while not life.dead:
        life.update()
        LifePrinter.print(life)


if __name__ == '__main__':
    test()
