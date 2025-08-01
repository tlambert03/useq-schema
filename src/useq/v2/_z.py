from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, Literal, Union

import numpy as np
from pydantic import Field, field_validator
from typing_extensions import deprecated

from useq._common._enums import Axis
from useq.v2._axes_iterator import AxisIterable
from useq.v2._position import Position

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from useq._common._mda_event import MDAEvent


def _list_cast(field: str) -> Callable:
    v = field_validator(field, mode="before", check_fields=False)
    return v(list)


class ZPlan(AxisIterable[Position]):
    axis_key: Literal[Axis.Z] = Field(default=Axis.Z, frozen=True, init=False)  # pyright: ignore[reportIncompatibleVariableOverride]
    go_up: bool = True

    def _start_stop_step(self) -> tuple[float, float, float]:
        raise NotImplementedError

    def positions(self) -> Sequence[float]:
        start, stop, step = self._start_stop_step()
        if step == 0:
            return [start]
        stop += step / 2  # make sure we include the last point
        return [float(x) for x in np.arange(start, stop, step)]

    def __len__(self) -> int:
        """Get the number of Z positions."""
        start, stop, step = self._start_stop_step()
        if step == 0:
            return 1
        nsteps = (stop + step - start) / step
        return math.ceil(round(nsteps, 6))

    @property
    def is_relative(self) -> bool:
        return True

    def __iter__(self) -> Iterator[Position]:  # type: ignore[override]
        """Iterate over Z positions."""
        positions = self.positions()
        if not self.go_up:
            positions = positions[::-1]
        for p in positions:
            yield Position(z=p, is_relative=self.is_relative)

    @deprecated(
        "num_positions() is deprecated, use len(z_plan) instead.",
        category=UserWarning,
        stacklevel=2,
    )
    def num_positions(self) -> int:
        """Get the number of Z positions."""
        return len(self)

    def contribute_event_kwargs(
        self, value: Position, index: Mapping[str, int]
    ) -> MDAEvent.Kwargs:
        """Contribute Z position to the MDA event."""
        if value.z is not None:
            if self.is_relative:
                return {"z_pos_rel": value.z}  # type: ignore [typeddict-unknown-key]
            else:
                return {"z_pos": value.z}
        return {}


class ZTopBottom(ZPlan):
    """Define Z using absolute top & bottom positions.

    Note that `bottom` will always be visited, regardless of `go_up`, while `top` will
    always be *encompassed* by the range, but may not be precisely visited if the step
    size does not divide evenly into the range.

    Attributes
    ----------
    top : float
        Top position in microns (inclusive).
    bottom : float
        Bottom position in microns (inclusive).
    step : float
        Step size in microns.
    go_up : bool
        If `True`, instructs engine to start at bottom and move towards top. By default,
        `True`.
    """

    top: float
    bottom: float
    step: float

    def _start_stop_step(self) -> tuple[float, float, float]:
        return self.bottom, self.top, self.step

    @property
    def is_relative(self) -> bool:
        return False


class ZRangeAround(ZPlan):
    """Define Z as a symmetric range around some reference position.

    Note that `-range / 2` will always be visited, regardless of `go_up`, while
    `+range / 2` will always be *encompassed* by the range, but may not be precisely
    visited if the step size does not divide evenly into the range.

    Attributes
    ----------
    range : float
        Range in microns (inclusive). For example, a range of 4 with a step size
        of 1 would visit [-2, -1, 0, 1, 2].
    step : float
        Step size in microns.
    go_up : bool
        If `True`, instructs engine to start at bottom and move towards top. By default,
        `True`.
    """

    range: float
    step: float

    def _start_stop_step(self) -> tuple[float, float, float]:
        return -self.range / 2, self.range / 2, self.step


class ZAboveBelow(ZPlan):
    """Define Z as asymmetric range above and below some reference position.

    Note that `below` will always be visited, regardless of `go_up`, while `above` will
    always be *encompassed* by the range, but may not be precisely visited if the step
    size does not divide evenly into the range.

    Attributes
    ----------
    above : float
        Range above reference position in microns (inclusive).
    below : float
        Range below reference position in microns (inclusive).
    step : float
        Step size in microns.
    go_up : bool
        If `True`, instructs engine to start at bottom and move towards top. By default,
        `True`.
    """

    above: float
    below: float
    step: float

    def _start_stop_step(self) -> tuple[float, float, float]:
        return -abs(self.below), +abs(self.above), self.step


class ZAbsolutePositions(ZPlan):
    """Define Z as a list of absolute positions.

    Attributes
    ----------
    relative : list[float]
        List of relative z positions.
    go_up : bool
        If `True` (the default), visits points in the order provided, otherwise in
        reverse.
    """

    absolute: list[float]

    _normabs = _list_cast("absolute")

    def positions(self) -> Sequence[float]:
        return self.absolute

    def __len__(self) -> int:
        return len(self.absolute)

    @property
    def is_relative(self) -> bool:
        return False


class ZRelativePositions(ZPlan):
    """Define Z as a list of positions relative to some reference.

    Typically, the "reference" will be whatever the current Z position is at the start
    of the sequence.

    Attributes
    ----------
    relative : list[float]
        List of relative z positions.
    go_up : bool
        If `True` (the default), visits points in the order provided, otherwise in
        reverse.
    """

    relative: list[float]

    _normrel = _list_cast("relative")

    def positions(self) -> Sequence[float]:
        return self.relative

    def __len__(self) -> int:
        return len(self.relative)


# order matters... this is the order in which pydantic will try to coerce input.
# should go from most specific to least specific
AnyZPlan = Union[
    ZTopBottom, ZAboveBelow, ZRangeAround, ZAbsolutePositions, ZRelativePositions
]
