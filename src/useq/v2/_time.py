from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union

from pydantic import BeforeValidator, Field, PlainSerializer, model_validator
from typing_extensions import deprecated

from useq._common._enums import Axis
from useq.v2._axes_iterator import AxisIterable

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator, Mapping

    from useq._common._mda_event import MDAEvent


def _validate_delta(v: Any) -> timedelta:
    if isinstance(v, dict):
        v = timedelta(**v)
    elif isinstance(v, (str, int, float)):
        v = timedelta(seconds=float(v))  # assuming ISO 8601 or similar

    if not isinstance(v, timedelta):
        raise TypeError(f"Expected timedelta, str, int, or dict, got {type(v)}")
    if v.total_seconds() < 0:
        raise ValueError("Duration must be non-negative")
    return v


# slightly modified so that we can accept dict objects as input
# and serialize to total_seconds
NonNegativeTimeDelta = Annotated[
    timedelta,
    BeforeValidator(_validate_delta),
    PlainSerializer(lambda td: td.total_seconds()),
]


class TimePlan(AxisIterable[float]):
    axis_key: str = Field(default=Axis.TIME, frozen=True, init=False)
    # TODO: probably needs to be implemented by engine
    prioritize_duration: bool = False  # or prioritize num frames

    def __iter__(self) -> Iterator[float]:  # type: ignore
        for td in self.deltas():
            yield td.total_seconds()

    def __len__(self) -> int:
        return self.loops  # type: ignore  # TODO

    def deltas(self) -> Iterator[timedelta]:
        current = timedelta(0)
        for _ in range(self.loops):  # type: ignore  # TODO
            yield current
            current += self.interval  # type: ignore  # TODO

    def contribute_event_kwargs(
        self, value: float, index: Mapping[str, int]
    ) -> MDAEvent.Kwargs:
        """Contribute time data to the event being built.

        Parameters
        ----------
        value : float
            The time value for this iteration.
        index : Mapping[str, int]
            Current axis indices.

        Returns
        -------
        dict
            Event data to be merged into the MDAEvent.
        """
        return {"min_start_time": value}

    @deprecated(
        "num_timepoints() is deprecated, use len(time_plan) instead.",
        category=UserWarning,
        stacklevel=2,
    )
    def num_timepoints(self) -> int:
        """Return the number of time points in this plan.

        This is deprecated and will be removed in a future version.
        Use `len()` instead.
        """
        return len(self)


class TIntervalLoops(TimePlan):
    """Define temporal sequence using interval and number of loops.

    Attributes
    ----------
    interval : str | timedelta | float
        Time between frames. Scalars are interpreted as seconds.
        Strings are parsed according to ISO 8601.
    loops : int
        Number of frames.
    prioritize_duration : bool
        If `True`, instructs engine to prioritize duration over number of frames in case
        of conflict. By default, `False`.
    """

    interval: NonNegativeTimeDelta
    loops: int = Field(..., gt=0)

    @property
    def duration(self) -> timedelta:
        return self.interval * (self.loops - 1)


class TDurationLoops(TimePlan):
    """Define temporal sequence using duration and number of loops.

    Attributes
    ----------
    duration : str | timedelta
        Total duration of sequence. Scalars are interpreted as seconds.
        Strings are parsed according to ISO 8601.
    loops : int
        Number of frames.
    prioritize_duration : bool
        If `True`, instructs engine to prioritize duration over number of frames in case
        of conflict. By default, `False`.
    """

    duration: NonNegativeTimeDelta
    loops: int = Field(..., gt=0)

    @property
    def interval(self) -> timedelta:
        if self.loops == 1:
            # Special case: with only 1 loop, interval is meaningless
            # Return zero to indicate instant
            return timedelta(0)
        # -1 makes it so that the last loop will *occur* at duration, not *finish*
        return self.duration / (self.loops - 1)


class TIntervalDuration(TimePlan):
    """Define temporal sequence using interval and duration.

    Attributes
    ----------
    interval : str | timedelta
        Time between frames. Scalars are interpreted as seconds.
        Strings are parsed according to ISO 8601.
    duration : str | timedelta
        Total duration of sequence.
    prioritize_duration : bool
        If `True`, instructs engine to prioritize duration over number of frames in case
        of conflict. By default, `True`.
    """

    interval: NonNegativeTimeDelta
    duration: Optional[NonNegativeTimeDelta] = None
    prioritize_duration: bool = True

    def __iter__(self) -> Iterator[float]:  # type: ignore[override]
        duration_s = self.duration.total_seconds() if self.duration else None
        interval_s = self.interval.total_seconds()
        t = 0.0
        # when `duration_s` is None, the `or` makes it always True → infinite;
        # otherwise it stops once t > duration_s
        while duration_s is None or t <= duration_s:
            yield t
            t += interval_s

    @property
    def loops(self) -> int:
        return len(self)

    def __len__(self) -> int:
        """Return the number of time points in this plan."""
        if self.duration is None:
            raise ValueError("Cannot determine length of infinite time plan")
        return int(self.duration.total_seconds() / self.interval.total_seconds()) + 1


SinglePhaseTimePlan = Union[TIntervalDuration, TIntervalLoops, TDurationLoops]


class MultiPhaseTimePlan(TimePlan):
    """Time sequence composed of multiple phases.

    Attributes
    ----------
    phases : Sequence[TIntervalDuration | TIntervalLoops | TDurationLoops]
        Sequence of time plans.
    """

    phases: list[SinglePhaseTimePlan]  # pyright: ignore[reportIncompatibleVariableOverride]

    def deltas(self) -> Iterator[timedelta]:
        accum = timedelta(0)
        yield accum
        for phase in self.phases:
            td = None
            for i, td in enumerate(phase.deltas()):
                # skip the first timepoint of later phases
                if i == 0 and td == timedelta(0):
                    continue
                yield td + accum
            if td is not None:
                accum += td

    def __len__(self) -> int:
        """Return the number of time points in this plan."""
        phase_sum = sum(len(phase) for phase in self.phases)
        # subtract 1 for the first time point of each phase
        # except the first one
        return phase_sum - len(self.phases) + 1

    @model_validator(mode="before")
    @classmethod
    def _cast(cls, value: Any) -> Any:
        if isinstance(value, Sequence) and not isinstance(value, str):
            value = {"phases": value}
        return value

    def __iter__(self) -> Generator[float, bool | None, None]:  # type: ignore[override]
        """Yield the global elapsed time over multiple plans.

        and allow `.send(True)` to skip to the next phase.
        """
        offset = 0.0
        for ip, phase in enumerate(self.phases):
            last_t = 0.0
            phase_iter = iter(phase)
            if ip != 0:
                # skip the first time point of all the phases except the first
                next(phase_iter)
            while True:
                try:
                    t = next(phase_iter)
                except StopIteration:
                    break
                last_t = t
                # here `force = yield offset + t` allows the caller to do
                #    gen = iter(plan)
                #    next(gen)  # start
                #    gen.send(True)  # force the next phase
                force = yield offset + t
                if force:
                    break

            # advance our offset to the end of this phase
            if (duration_td := phase.duration) is not None:
                offset += duration_td.total_seconds()
            else:
                # infinite phase that we broke out of
                # leave offset where it was + last_t
                offset += last_t


AnyTimePlan = Union[MultiPhaseTimePlan, SinglePhaseTimePlan]
