# useq-schema v2 (Preview)

!!! warning "This is a preview"

    `useq.v2` is a preview of the next version of the useq-schema API, and it may
    still change.  `useq.MDASequence`, as described in the rest of these docs, is
    unchanged, and *nothing needs to migrate yet*.

    pymmcore-plus can already run a `useq.v2.MDASequence`, but (for now) it treats
    it like any other iterable of events.  The engine doesn't see the sequence
    itself, and [saved data](../pymmcore-plus/guides/saving_data.md#lists-and-generators-are-saved-as-a-flat-stack)
    is written as one flat stack of frames.

In `useq.MDASequence`, the axes are fixed: time, positions, grid, channels and z
(`"tpgcz"`), and the logic for combining them lives inside useq.  In `useq.v2`, a
sequence is a tuple of *axes*, and any object that follows the
`v2.AxisIterable` interface can be one (it has an `axis_key`, yields values, and
says what each value contributes to an event).  The familiar plans (time plans, z
plans, grids, channels, stage positions) are all v2 axes, so the same experiments
can still be described, but you can also add your own axes, decide per axis which
combinations to skip, give a single position its own plans, and post-process the
stream of events with *transforms*.

The examples below all run against the current preview.

## The old arguments still work

`v2.MDASequence` accepts the same keyword arguments as `useq.MDASequence`, and
converts them into `axes`:

```python
from useq import v2

seq = v2.MDASequence(
    time_plan={"interval": 1.0, "loops": 2},
    stage_positions=[(10, 20, 5)],
    channels=["DAPI", "FITC"],
    z_plan={"range": 2, "step": 1},
)
print([str(axis.axis_key) for axis in seq.axes])
# ['t', 'p', 'c', 'z']

# ... which is the same as:
seq2 = v2.MDASequence(
    axes=(
        v2.TIntervalLoops(interval=1.0, loops=2),
        v2.StagePositions(values=[v2.Position(x=10, y=20, z=5)]),
        v2.ChannelsPlan(values=[v2.Channel(config="DAPI"), v2.Channel(config="FITC")]),
        v2.ZRangeAround(range=2, step=1),
    ),
)
assert list(seq) == list(seq2)
```

An existing `useq.MDASequence` can be converted with
`v2.MDASequence.model_validate(old_sequence)`.  The events are the same as the
ones `useq.MDASequence` yields (except that v2 events don't carry a reference to
their `sequence`), with these exceptions in the current preview:

- The `Channel` options `acquire_every`, `do_stack` and `z_offset` are *not*
  applied yet, so every channel is acquired at every time point and z position.
- Giving a position its own sub-sequence with `Position(sequence=...)` emits a
  `DeprecationWarning`; see [below](#different-plans-for-one-position) for the v2
  way.

## Custom axes

An axis yields values, and its `contribute_to_mda_event` method says what each
value adds to the event.  For example, here's an axis that steps a laser power
(as a device property):

```python
from collections.abc import Mapping

from useq import v2


class LaserPowerAxis(v2.SimpleValueAxis[float]):
    axis_key: str = "laser"

    def contribute_to_mda_event(self, value: float, index: Mapping[str, int]) -> dict:
        return {"properties": [("Laser", "Power", value)]}  # (1)!


seq = v2.MDASequence(
    axes=(
        v2.ChannelsPlan(values=["DAPI", "FITC"]),
        LaserPowerAxis(values=[10, 50]),
    ),
)
for event in seq:
    print(event)
```

1. Whatever this returns is passed to `MDAEvent(...)`.  (For type checkers, the
   return type is `MDAEvent.Kwargs`, a `TypedDict` that only exists when type
   checking.)

```
index={'c': 0, 'laser': 0} channel=Channel(config='DAPI') properties=[PropertyTuple(device_name='Laser', property_name='Power', property_value=10.0)]
index={'c': 0, 'laser': 1} channel=Channel(config='DAPI') properties=[PropertyTuple(device_name='Laser', property_name='Power', property_value=50.0)]
index={'c': 1, 'laser': 0} channel=Channel(config='FITC') properties=[PropertyTuple(device_name='Laser', property_name='Power', property_value=10.0)]
index={'c': 1, 'laser': 1} channel=Channel(config='FITC') properties=[PropertyTuple(device_name='Laser', property_name='Power', property_value=50.0)]
```

`v2.SimpleValueAxis` iterates over a list of `values`.  For anything else,
subclass `v2.AxisIterable` and implement `__iter__` (see [Sequences that never
end](#sequences-that-never-end)).

## Skipping combinations

Any axis can veto a combination of values by overriding `should_skip`.  It
receives a dict that maps each axis key to an `(index, value, axis)` tuple.  Here
the second channel gets a single plane rather than a z-stack:

```python
from useq import v2


class SparseZ(v2.ZRangeAround):
    """Only take the full z-stack in the first channel."""

    def should_skip(self, prefix: dict) -> bool:
        c_index = prefix["c"][0]
        z_index = prefix["z"][0]
        return c_index > 0 and z_index != 1


seq = v2.MDASequence(
    axes=(
        v2.ChannelsPlan(values=["DAPI", "FITC"]),
        SparseZ(range=2, step=1),  # (1)!
    ),
)
for event in seq:
    print(event.index, event.channel.config, event.z_pos)
```

1. There's no stage position here, so (just as in v1) this relative z plan is
   centered on z = 0, not on the current focus.

```
{'c': 0, 'z': 0} DAPI -1.0
{'c': 0, 'z': 1} DAPI 0.0
{'c': 0, 'z': 2} DAPI 1.0
{'c': 1, 'z': 1} FITC 0.0
```

## Different plans for one position

A value yielded by an axis may itself be a sequence, whose `value` stands in for
the plain value, and whose axes replace (or add to) the parent's axes for that
branch.  Here, the second position gets a bigger z-stack:

```python
from useq import v2

cell_1 = v2.MDASequence(
    value=v2.Position(x=100, y=100, z=10),
    axes=(v2.ZRangeAround(range=4, step=2),),
)

seq = v2.MDASequence(
    axes=(
        v2.StagePositions(values=[v2.Position(x=0, y=0, z=10), cell_1]),
        v2.ChannelsPlan(values=["DAPI"]),
        v2.ZRangeAround(range=1, step=1),
    ),
)
for event in seq:
    print(event.index, event.x_pos, event.z_pos)
```

```
{'p': 0, 'c': 0, 'z': 0} 0.0 9.5
{'p': 0, 'c': 0, 'z': 1} 0.0 10.5
{'p': 1, 'c': 0, 'z': 0} 100.0 8.0
{'p': 1, 'c': 0, 'z': 1} 100.0 10.0
{'p': 1, 'c': 0, 'z': 2} 100.0 12.0
```

## Transforms

Transforms see each event after it has been built, and may change it, drop it, or
add more events, which makes it possible to insert events that don't belong to
any axis.  A transform is a callable that returns (or yields) events.  It also
gets the previous event, and a function that builds the next one, for look-ahead:

```python
from collections.abc import Callable, Iterable

from useq import v2


class SnapBrightfieldAfterStack:
    """After each z-stack, add a single brightfield image."""

    def __call__(
        self,
        event: v2.MDAEvent,
        *,
        prev_event: v2.MDAEvent | None,
        make_next_event: Callable[[], v2.MDAEvent | None],
    ) -> Iterable[v2.MDAEvent]:
        yield event
        next_event = make_next_event()
        if next_event is None or next_event.index.get("z", 0) == 0:
            yield event.model_copy(
                update={"channel": v2.EventChannel(config="BF"), "z_pos": None}
            )


seq = v2.MDASequence(
    channels=["DAPI"],
    stage_positions=[(0, 0, 10), (100, 100, 10)],
    z_plan={"range": 2, "step": 1},
    transforms=(SnapBrightfieldAfterStack(),),
)
for event in seq:
    print(event.index, event.channel.config, event.z_pos)
```

```
{'p': 0, 'c': 0, 'z': 0} DAPI 9.0
{'p': 0, 'c': 0, 'z': 1} DAPI 10.0
{'p': 0, 'c': 0, 'z': 2} DAPI 11.0
{'p': 0, 'c': 0, 'z': 2} BF None
{'p': 1, 'c': 0, 'z': 0} DAPI 9.0
{'p': 1, 'c': 0, 'z': 1} DAPI 10.0
{'p': 1, 'c': 0, 'z': 2} DAPI 11.0
{'p': 1, 'c': 0, 'z': 2} BF None
```

Some of v1's built-in behavior is implemented as transforms, which v2 adds for
you: `ResetEventTimerTransform` (when there is a time plan), and
`KeepShutterOpenTransform` and `AutoFocusTransform` (when you set
`keep_shutter_open_across` or `autofocus_plan`).

!!! warning

    Passing `transforms=` *replaces* the default transforms.  If your sequence has
    a time plan, add `v2.ResetEventTimerTransform()` to your own tuple, or the
    first event will no longer reset the event timer.

## Sequences that never end

v2 axes don't need a length, so a sequence can go on forever (or until the
acquisition is cancelled):

```python
import itertools
from collections.abc import Iterator, Mapping

from useq import v2


class Forever(v2.AxisIterable[int]):
    """A time axis with no end."""

    axis_key: str = "t"

    def __iter__(self) -> Iterator[int]:
        yield from itertools.count()

    def contribute_to_mda_event(self, value: int, index: Mapping[str, int]) -> dict:
        return {"min_start_time": value * 5.0}


seq = v2.MDASequence(axes=(Forever(), v2.ChannelsPlan(values=["DAPI", "FITC"])))
print(seq.is_finite())  # False
for event in itertools.islice(seq, 5):
    print(event.index, event.channel.config, event.min_start_time)
```

```
{'t': 0, 'c': 0} DAPI 0.0
{'t': 0, 'c': 1} FITC 0.0
{'t': 1, 'c': 0} DAPI 5.0
{'t': 1, 'c': 1} FITC 5.0
{'t': 2, 'c': 0} DAPI 10.0
```

## Other kinds of events

`v2.MDASequence` builds `MDAEvent` objects, but the class it is built on,
`v2.MultiAxisSequence`, can build anything.  Pass it an `event_builder`, which is
called with the axes index (and the chain of enclosing sequences) for each
combination:

```python
from useq import v2


class DictBuilder:
    def __call__(self, axes_index: dict, context: tuple) -> dict:
        return {key: value for key, (index, value, axis) in axes_index.items()}


seq = v2.MultiAxisSequence(
    axes=(
        v2.SimpleValueAxis(axis_key="a", values=[1, 2]),
        v2.SimpleValueAxis(axis_key="b", values=["x", "y"]),
    ),
    event_builder=DictBuilder(),
)
print(list(seq.iter_events()))
# [{'a': 1, 'b': 'x'}, {'a': 1, 'b': 'y'}, {'a': 2, 'b': 'x'}, {'a': 2, 'b': 'y'}]
```

## v1 and v2 side by side

| | `useq.MDASequence` | `useq.v2.MDASequence` |
| --- | --- | --- |
| axes | `time_plan`, `stage_positions`, `grid_plan`, `channels`, `z_plan` | `axes=(...)`, any `AxisIterable` (the v1 keywords are converted) |
| plan for one position | `Position(sequence=MDASequence(...))` | `MDASequence(value=Position(...), axes=(...))`, as an item in `StagePositions` |
| skipping | `Channel(acquire_every=..., do_stack=...)` | `should_skip()` on any axis (the `Channel` options aren't applied yet) |
| sizes | `seq.sizes`, `seq.shape` | `[len(axis) for axis in seq.axes]` and `seq.is_finite()` (`sizes` and `shape` still work, with a `FutureWarning`) |
| finding a plan | `seq.time_plan`, `seq.z_plan`, ... | the same properties, which return the axis with that key (or `None`) |
| z plan values | `float` | `Position` (with only `z` set) |
| extra events | build the list of events yourself | transforms |
| length | always finite | may be infinite |
| files | `seq.yaml()`, `MDASequence.from_file()` | no `yaml()` or `from_file()` yet |
