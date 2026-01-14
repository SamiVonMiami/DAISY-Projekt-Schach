import numpy as np

class Piece:
    """
    Base class for pieces on the board.

    A piece holds a reference to the board, its color and its currently located cell.
    In this class, you need to implement two methods, the "evaluate()" method and the "get_valid_cells()" method.
    """
    def __init__(self, board, white):
        self.board = board
        self.white = white
        self.cell = None

    def is_white(self):
        return self.white

    def can_enter_cell(self, cell):
        return self.board.piece_can_enter_cell(self, cell)

    def can_hit_on_cell(self, cell):
        return self.board.piece_can_hit_on_cell(self, cell)

    def evaluate(self):
        """
        Meaningful numerical evaluation of this piece on the board (color independent).
        Combines:
          - base material value
          - mobility (reachable cells)
          - immediate tactical pressure (how many enemy pieces could be hit now)
        """
        # --- base material (color independent) ---
        base_values = {
            "Pawn": 1.0,
            "Knight": 3.0,
            "Bishop": 3.2,
            "Rook": 5.0,
            "Queen": 9.0,
            "King": 200.0,  # high to reflect importance in evaluation
        }
        cls_name = self.__class__.__name__
        base = base_values.get(cls_name, 0.0)

        # --- mobility (reachable cells) ---
        try:
            reachable = self.get_reachable_cells()
            mobility = 0.05 * len(reachable)
        except Exception:
            mobility = 0.0

        # --- pressure (how many reachable cells are captures) ---
        pressure = 0.0
        try:
            hit_count = 0
            for cell in reachable:
                if self.can_hit_on_cell(cell):
                    hit_count += 1
            pressure = 0.10 * hit_count
        except Exception:
            pressure = 0.0

        return float(base + mobility + pressure)

    def get_valid_cells(self):
        """
        Return a list of valid cells this piece can move into.
        A cell is valid if:
          a) it is reachable (get_reachable_cells), and
          b) after moving there, own king is NOT in check.
        """
        valid = []
        reachable = self.get_reachable_cells()

        old_cell = self.cell

        for target in reachable:
            # piece that might be captured on target
            captured = self.board.get_cell(target)

            # temporarily move self to target
            self.board.set_cell(target, self)

            in_check = self.board.is_king_check_cached(self.is_white())

            #wegen king, nur züge zurück geben wenn der nicht in gefahr ist danach
            # if not in_check:
            #     valid.append(target)

            
            # restore original board state
            self.board.set_cell(old_cell, self)
            self.board.set_cell(target, captured)

            if not in_check:
                valid.append(target)

        return valid


class Pawn(Piece):  # Bauer
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        r, c = self.cell
        reachable = []

        # In eurem Board: a2 -> a3 bedeutet WHITE geht in +row Richtung
        direction = 1 if self.is_white() else -1
        start_row = 1 if self.is_white() else 6

        # 1 Schritt vorwärts (nur wenn leer)
        one_step = (r + direction, c)
        if self.board.cell_is_valid_and_empty(one_step):
            reachable.append(one_step)

            # 2 Schritte vorwärts (nur von Startreihe und nur wenn frei)
            two_step = (r + 2 * direction, c)
            if r == start_row and self.board.cell_is_valid_and_empty(two_step):
                reachable.append(two_step)

        # diagonal schlagen (nur wenn Gegner)
        diag_left = (r + direction, c - 1)
        diag_right = (r + direction, c + 1)

        if self.can_hit_on_cell(diag_left):
            reachable.append(diag_left)
        if self.can_hit_on_cell(diag_right):
            reachable.append(diag_right)

        return reachable



class Rook(Piece):  # Turm
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        """
        Rooks move horizontally/vertically until blocked.
        """
        r, c = self.cell
        reachable = []

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while True:
                cell = (nr, nc)

                if self.board.cell_is_valid_and_empty(cell):
                    reachable.append(cell)
                elif self.can_hit_on_cell(cell):
                    reachable.append(cell)
                    break
                else:
                    break

                nr += dr
                nc += dc

        return reachable


class Knight(Piece):  # Springer
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        """
        Knights jump in L-shapes, not blocked by in-between pieces.
        """
        r, c = self.cell
        reachable = []

        jumps = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        for dr, dc in jumps:
            cell = (r + dr, c + dc)
            if self.can_enter_cell(cell) or self.can_hit_on_cell(cell):
                reachable.append(cell)

        return reachable


class Bishop(Piece):  # Läufer
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        """
        Bishops move diagonally until blocked.
        """
        r, c = self.cell
        reachable = []

        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while True:
                cell = (nr, nc)

                if self.board.cell_is_valid_and_empty(cell):
                    reachable.append(cell)
                elif self.can_hit_on_cell(cell):
                    reachable.append(cell)
                    break
                else:
                    break

                nr += dr
                nc += dc

        return reachable


class Queen(Piece):  # Königin
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        """
        Queen combines rook + bishop movement.
        """
        r, c = self.cell
        reachable = []

        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while True:
                cell = (nr, nc)

                if self.board.cell_is_valid_and_empty(cell):
                    reachable.append(cell)
                elif self.can_hit_on_cell(cell):
                    reachable.append(cell)
                    break
                else:
                    break

                nr += dr
                nc += dc

        return reachable


class King(Piece):  # König
    def __init__(self, board, white):
        super().__init__(board, white)

    def get_reachable_cells(self):
        """
        King moves 1 step in any direction.
        (No castling required here.)
        """
        r, c = self.cell
        reachable = []

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                cell = (r + dr, c + dc)
                if self.can_enter_cell(cell) or self.can_hit_on_cell(cell):
                    reachable.append(cell)

        return reachable
