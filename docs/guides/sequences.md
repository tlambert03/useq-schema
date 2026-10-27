# Building Sequences

For most standard multi-dimensional experiments, you will want to use
[`useq.MDASequence`][] to construct your sequence of events. It allows you to
declare a "plan" for each axis in your experiment (channels, time, z, etc...)
along with the order in which the axes should be iterated.  Iterating over the
sequence yields [`useq.MDAEvent`][] objects (usually one per image), so
`list(sequence)` shows you which events an acquisition engine will be asked to
run.

A sequence is just data, so you can build and inspect the examples on this page
without a microscope.  To *run* a sequence, see [The Acquisition
Engine](../../pymmcore-plus/guides/mda_engine.md).

## Axes and plans

Each axis has a field on `MDASequence`, and a one-letter key that is used in
`axis_order` and in the `index` of each event:

| key | field | describes | reference |
| --- | --- | --- | --- |
| `t` | `time_plan` | time points (interval, duration, number of loops, or several phases) | [time plans](../schema/axes.md#time-plans) |
| `p` | `stage_positions` | a list of stage positions (or a well plate) | [`Position`][useq.Position], [well plates](../schema/axes.md#well-plates) |
| `g` | `grid_plan` | a grid (or random points) at each position | [grid plans](../schema/axes.md#grid-plans) |
| `c` | `channels` | a list of channel presets, each with an optional exposure | [`Channel`][useq.Channel] |
| `z` | `z_plan` | a z-stack | [z plans](../schema/axes.md#z-plans) |

`axis_order` (default `"tpgcz"`) says how the axes are nested (the "fastest"
axes come last).  There are also a few fields that aren't axes, such as
`autofocus_plan` ([hardware autofocus](../schema/hardware_autofocus.md)),
`keep_shutter_open_across`, `setup`, and `metadata`.  See the
[`MDASequence` reference](../schema/sequence.md) for all of them.

Let's look at how `MDASequence` can be used to create a few common experiments.

## A two-channel time series

```python
from useq import MDASequence

mda_sequence = MDASequence(
    time_plan={"interval": 2, "loops": 6},  # (1)!
    channels=[
        {"config": "DAPI", "exposure": 50},
        {"config": "FITC", "exposure": 80},
    ],
)
```

1. 6 time points, 2 seconds apart. See also, [additional time
   plans](../schema/axes.md#time-plans).

??? example "output of `list(mda_sequence)`"

    `min_start_time` is the time (in seconds) at which the event should start.
    `reset_event_timer=True` on the first event tells the engine to (re)start the
    clock that `min_start_time` is measured from.

    ```python
    [
        MDAEvent(
            index={"t": 0, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=0.0,
            reset_event_timer=True,
        ),
        MDAEvent(
            index={"t": 0, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=0.0,
        ),
        MDAEvent(
            index={"t": 1, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=2.0,
        ),
        MDAEvent(
            index={"t": 1, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=2.0,
        ),
        MDAEvent(
            index={"t": 2, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=4.0,
        ),
        MDAEvent(
            index={"t": 2, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=4.0,
        ),
        MDAEvent(
            index={"t": 3, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=6.0,
        ),
        MDAEvent(
            index={"t": 3, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=6.0,
        ),
        MDAEvent(
            index={"t": 4, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=8.0,
        ),
        MDAEvent(
            index={"t": 4, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=8.0,
        ),
        MDAEvent(
            index={"t": 5, "c": 0},
            channel=Channel(config="DAPI"),
            exposure=50.0,
            min_start_time=10.0,
        ),
        MDAEvent(
            index={"t": 5, "c": 1},
            channel=Channel(config="FITC"),
            exposure=80.0,
            min_start_time=10.0,
        ),
    ]
    ```

## A z-stack at three positions

```python
from useq import MDASequence, Position

mda_sequence = MDASequence(
    z_plan={"range": 4, "step": 0.5},  # (1)!
    stage_positions=[  # (2)!
        (10, 10, 20),
        {"x": 30, "y": 40, "z": 50},
        Position(x=60, y=70, z=80),
    ],
)
```

1. A 4-micron z-stack with 0.5 micron steps, centered on each position's `z`.
   See also, [additional z plans](../schema/axes.md#z-plans).
2. These are all valid ways to specify a [stage position][useq.Position].
   None of `x`, `y`, or `z` are required.

??? example "output of `list(mda_sequence)`"

    ```python
    [
        MDAEvent(index={"p": 0, "z": 0}, x_pos=10.0, y_pos=10.0, z_pos=18.0),
        MDAEvent(index={"p": 0, "z": 1}, x_pos=10.0, y_pos=10.0, z_pos=18.5),
        MDAEvent(index={"p": 0, "z": 2}, x_pos=10.0, y_pos=10.0, z_pos=19.0),
        MDAEvent(index={"p": 0, "z": 3}, x_pos=10.0, y_pos=10.0, z_pos=19.5),
        MDAEvent(index={"p": 0, "z": 4}, x_pos=10.0, y_pos=10.0, z_pos=20.0),
        MDAEvent(index={"p": 0, "z": 5}, x_pos=10.0, y_pos=10.0, z_pos=20.5),
        MDAEvent(index={"p": 0, "z": 6}, x_pos=10.0, y_pos=10.0, z_pos=21.0),
        MDAEvent(index={"p": 0, "z": 7}, x_pos=10.0, y_pos=10.0, z_pos=21.5),
        MDAEvent(index={"p": 0, "z": 8}, x_pos=10.0, y_pos=10.0, z_pos=22.0),
        MDAEvent(index={"p": 1, "z": 0}, x_pos=30.0, y_pos=40.0, z_pos=48.0),
        MDAEvent(index={"p": 1, "z": 1}, x_pos=30.0, y_pos=40.0, z_pos=48.5),
        MDAEvent(index={"p": 1, "z": 2}, x_pos=30.0, y_pos=40.0, z_pos=49.0),
        MDAEvent(index={"p": 1, "z": 3}, x_pos=30.0, y_pos=40.0, z_pos=49.5),
        MDAEvent(index={"p": 1, "z": 4}, x_pos=30.0, y_pos=40.0, z_pos=50.0),
        MDAEvent(index={"p": 1, "z": 5}, x_pos=30.0, y_pos=40.0, z_pos=50.5),
        MDAEvent(index={"p": 1, "z": 6}, x_pos=30.0, y_pos=40.0, z_pos=51.0),
        MDAEvent(index={"p": 1, "z": 7}, x_pos=30.0, y_pos=40.0, z_pos=51.5),
        MDAEvent(index={"p": 1, "z": 8}, x_pos=30.0, y_pos=40.0, z_pos=52.0),
        MDAEvent(index={"p": 2, "z": 0}, x_pos=60.0, y_pos=70.0, z_pos=78.0),
        MDAEvent(index={"p": 2, "z": 1}, x_pos=60.0, y_pos=70.0, z_pos=78.5),
        MDAEvent(index={"p": 2, "z": 2}, x_pos=60.0, y_pos=70.0, z_pos=79.0),
        MDAEvent(index={"p": 2, "z": 3}, x_pos=60.0, y_pos=70.0, z_pos=79.5),
        MDAEvent(index={"p": 2, "z": 4}, x_pos=60.0, y_pos=70.0, z_pos=80.0),
        MDAEvent(index={"p": 2, "z": 5}, x_pos=60.0, y_pos=70.0, z_pos=80.5),
        MDAEvent(index={"p": 2, "z": 6}, x_pos=60.0, y_pos=70.0, z_pos=81.0),
        MDAEvent(index={"p": 2, "z": 7}, x_pos=60.0, y_pos=70.0, z_pos=81.5),
        MDAEvent(index={"p": 2, "z": 8}, x_pos=60.0, y_pos=70.0, z_pos=82.0),
    ]
    ```

!!! warning "Relative to *what*?"

    Most z plans (`range`, `above`/`below`, relative positions) and grid plans
    (`rows`/`columns`, `width`/`height`, random points) are *relative*: they are
    added to the
    `z` (or `x`/`y`) of each stage position.  If a position doesn't specify `z`, or
    there are no `stage_positions` at all, a relative z plan is centered on
    **z = 0**, *not* on the current focus position:

    ```python
    >>> [e.z_pos for e in MDASequence(z_plan={"range": 4, "step": 1})]
    [-2.0, -1.0, 0.0, 1.0, 2.0]
    ```

    (A relative grid with no `x`/`y` is likewise centered on x = y = 0.)  On a real
    microscope, that may send the objective somewhere you didn't expect.  So when
    you want a z-stack "around where I am now", put the current position in the
    sequence, e.g. with pymmcore-plus:

    ```python
    MDASequence(
        z_plan={"range": 4, "step": 1},
        stage_positions=[Position(z=core.getZPosition())],
    )
    ```

    (Absolute plans, like `ZTopBottom` or `ZAbsolutePositions`, aren't affected.)

## A grid of z-stacks

Here we use `axis_order` to declare that we want the full z-stack
to happen at each `(row, col)` before moving to the next
position in the grid.

```python
from useq import MDASequence

mda_sequence = MDASequence(
    stage_positions=[{"x": 100, "y": 200, "z": 300}],
    grid_plan={"fov_width": 20, "fov_height": 10, "rows": 2, "columns": 2},
    z_plan={"range": 10, "step": 2.5},
    axis_order="pgz",  # (1)!
)
```

1. The "fastest" axes come last. By putting `z` after `g` in the `axis_order`,
    we're saying "at each `g`, do a full `z` iteration".

??? example "output of `list(mda_sequence)`"

    ```python
    [
        MDAEvent(index={"p": 0, "g": 0, "z": 0}, x_pos=90.0, y_pos=205.0, z_pos=295.0),
        MDAEvent(index={"p": 0, "g": 0, "z": 1}, x_pos=90.0, y_pos=205.0, z_pos=297.5),
        MDAEvent(index={"p": 0, "g": 0, "z": 2}, x_pos=90.0, y_pos=205.0, z_pos=300.0),
        MDAEvent(index={"p": 0, "g": 0, "z": 3}, x_pos=90.0, y_pos=205.0, z_pos=302.5),
        MDAEvent(index={"p": 0, "g": 0, "z": 4}, x_pos=90.0, y_pos=205.0, z_pos=305.0),
        MDAEvent(index={"p": 0, "g": 1, "z": 0}, x_pos=110.0, y_pos=205.0, z_pos=295.0),
        MDAEvent(index={"p": 0, "g": 1, "z": 1}, x_pos=110.0, y_pos=205.0, z_pos=297.5),
        MDAEvent(index={"p": 0, "g": 1, "z": 2}, x_pos=110.0, y_pos=205.0, z_pos=300.0),
        MDAEvent(index={"p": 0, "g": 1, "z": 3}, x_pos=110.0, y_pos=205.0, z_pos=302.5),
        MDAEvent(index={"p": 0, "g": 1, "z": 4}, x_pos=110.0, y_pos=205.0, z_pos=305.0),
        MDAEvent(index={"p": 0, "g": 2, "z": 0}, x_pos=110.0, y_pos=195.0, z_pos=295.0),
        MDAEvent(index={"p": 0, "g": 2, "z": 1}, x_pos=110.0, y_pos=195.0, z_pos=297.5),
        MDAEvent(index={"p": 0, "g": 2, "z": 2}, x_pos=110.0, y_pos=195.0, z_pos=300.0),
        MDAEvent(index={"p": 0, "g": 2, "z": 3}, x_pos=110.0, y_pos=195.0, z_pos=302.5),
        MDAEvent(index={"p": 0, "g": 2, "z": 4}, x_pos=110.0, y_pos=195.0, z_pos=305.0),
        MDAEvent(index={"p": 0, "g": 3, "z": 0}, x_pos=90.0, y_pos=195.0, z_pos=295.0),
        MDAEvent(index={"p": 0, "g": 3, "z": 1}, x_pos=90.0, y_pos=195.0, z_pos=297.5),
        MDAEvent(index={"p": 0, "g": 3, "z": 2}, x_pos=90.0, y_pos=195.0, z_pos=300.0),
        MDAEvent(index={"p": 0, "g": 3, "z": 3}, x_pos=90.0, y_pos=195.0, z_pos=302.5),
        MDAEvent(index={"p": 0, "g": 3, "z": 4}, x_pos=90.0, y_pos=195.0, z_pos=305.0),
    ]
    ```

!!! tip

    You can usually leave out `fov_width` and `fov_height`.  pymmcore-plus fills
    them in from the camera ROI and pixel size when the acquisition starts.

## Skipping timepoints or z-stacks

The [`Channel`][useq.Channel] field has a few tricks, such as skipping timepoints
or z-stacks for specific channels.  Here we take a fast z-stack (leaving the
shutter open) in the `FITC` channel only, and a single image in the `DIC`
channel every 3 timepoints:

```python
from useq import MDASequence

mda_sequence = MDASequence(
    z_plan={"range": 10, "step": 2.5},  # (1)!
    time_plan={"interval": 2, "loops": 6},
    channels=[
        "FITC",
        {"config": "DIC", "acquire_every": 3, "do_stack": False},
    ],
    keep_shutter_open_across=["z"],
)
```

1. There are no stage positions here, so the stack is centered on z = 0 (see
   [above](#a-z-stack-at-three-positions)).

??? example "output of `list(mda_sequence)` (first two timepoints)"

    ```python
    [
        MDAEvent(
            index={"t": 0, "c": 0, "z": 0},
            channel=Channel(config="FITC"),
            min_start_time=0.0,
            z_pos=-5.0,
            keep_shutter_open=True,
            reset_event_timer=True,
        ),
        MDAEvent(
            index={"t": 0, "c": 0, "z": 1},
            channel=Channel(config="FITC"),
            min_start_time=0.0,
            z_pos=-2.5,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 0, "c": 0, "z": 2},
            channel=Channel(config="FITC"),
            min_start_time=0.0,
            z_pos=0.0,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 0, "c": 0, "z": 3},
            channel=Channel(config="FITC"),
            min_start_time=0.0,
            z_pos=2.5,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 0, "c": 0, "z": 4},
            channel=Channel(config="FITC"),
            min_start_time=0.0,
            z_pos=5.0,
        ),
        MDAEvent(
            index={"t": 0, "c": 1, "z": 2},
            channel=Channel(config="DIC"),
            min_start_time=0.0,
            z_pos=0.0,
        ),
        MDAEvent(
            index={"t": 1, "c": 0, "z": 0},
            channel=Channel(config="FITC"),
            min_start_time=2.0,
            z_pos=-5.0,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 1, "c": 0, "z": 1},
            channel=Channel(config="FITC"),
            min_start_time=2.0,
            z_pos=-2.5,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 1, "c": 0, "z": 2},
            channel=Channel(config="FITC"),
            min_start_time=2.0,
            z_pos=0.0,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 1, "c": 0, "z": 3},
            channel=Channel(config="FITC"),
            min_start_time=2.0,
            z_pos=2.5,
            keep_shutter_open=True,
        ),
        MDAEvent(
            index={"t": 1, "c": 0, "z": 4},
            channel=Channel(config="FITC"),
            min_start_time=2.0,
            z_pos=5.0,
        ),
        # ... t=2 is like t=1, then t=3 has DIC again (like t=0), etc...
    ]
    ```

## Different plans at different positions

A stage position may carry its own `sequence`, whose plans replace the
global ones at that position (any plan it doesn't set comes from the main
sequence).  Here, the second position gets a different z-stack:

```python
from useq import MDASequence

mda_sequence = MDASequence(
    z_plan={"range": 4, "step": 1},
    stage_positions=[
        {"x": 0, "y": 0, "z": 10},
        {
            "name": "Cell 1",
            "x": 100,
            "y": 50,
            "z": 12,
            "sequence": {"z_plan": {"above": 2, "below": 0, "step": 0.5}},
        },
    ],
)

for event in mda_sequence:
    print(event.index, event.pos_name, event.z_pos)
```

??? example "output"

    ```
    {'p': 0, 'z': 0} None 8.0
    {'p': 0, 'z': 1} None 9.0
    {'p': 0, 'z': 2} None 10.0
    {'p': 0, 'z': 3} None 11.0
    {'p': 0, 'z': 4} None 12.0
    {'p': 1, 'z': 0} Cell 1 12.0
    {'p': 1, 'z': 1} Cell 1 12.5
    {'p': 1, 'z': 2} Cell 1 13.0
    {'p': 1, 'z': 3} Cell 1 13.5
    {'p': 1, 'z': 4} Cell 1 14.0
    ```

!!! note

    pymmcore-plus can't yet save a sequence like this one as a multi-dimensional
    array (the positions don't share one shape), so it writes the frames as a [flat
    stack](../../pymmcore-plus/guides/saving_data.md#lists-and-generators-are-saved-as-a-flat-stack).
    A sub-sequence that only adds a `grid_plan` is fine.

## A note on syntax

If you prefer, you can use `useq` objects rather than `dicts`
for all of these fields. This has the advantage of providing
type-checking and auto-completion in your IDE.

!!! example

    The following two sequences are equivalent:

    ```python
    import useq

    mda_sequence1 = useq.MDASequence(
        time_plan={"interval": 2, "loops": 10},
        z_plan={"range": 4, "step": 0.5},
        channels=[
            {"config": "DAPI", "exposure": 50},
            {"config": "FITC", "exposure": 80},
        ],
    )

    mda_sequence2 = useq.MDASequence(
        time_plan=useq.TIntervalLoops(interval=2, loops=10),
        z_plan=useq.ZRangeAround(range=4, step=0.5),
        channels=[
            useq.Channel(config="DAPI", exposure=50),
            useq.Channel(config="FITC", exposure=80),
        ],
    )

    assert mda_sequence1 == mda_sequence2
    ```

## Saving and loading sequences

`MDASequence` objects can be serialized and deserialized to and
from JSON or YAML, making it easy to save and load them from
file:

```python
from pathlib import Path

import useq

mda_sequence = useq.MDASequence(
    stage_positions=[(100, 100, 30)],
    time_plan={"interval": 2, "loops": 10},
    z_plan={"range": 4, "step": 0.5},
    channels=[
        {"config": "DAPI", "exposure": 50, "do_stack": False},
        {"config": "FITC", "exposure": 20},
    ],
    axis_order="tpcz",
)

Path("mda_sequence.yaml").write_text(mda_sequence.yaml())
```

... results in:

```yaml title="mda_sequence.yaml"
axis_order:
- t
- p
- c
- z
channels:
- config: DAPI
  do_stack: false
  exposure: 50.0
- config: FITC
  exposure: 20.0
stage_positions:
- x: 100.0
  y: 100.0
  z: 30.0
time_plan:
  interval: 2.0
  loops: 10
z_plan:
  range: 4.0
  step: 0.5
```

... which can be loaded back into an `MDASequence` object:

```python
mda_sequence = useq.MDASequence.from_file("mda_sequence.yaml")
```

For JSON, use `mda_sequence.model_dump_json(exclude_unset=True)` to write and the
same `from_file` (with a `.json` extension) to read.  Only the fields you set are
written, so the files stay short and readable.  The [overview](../index.md#serialization-and-deserialization)
has a larger example file, with multi-phase time plans and per-position z-stacks.

## Next steps

Once you have a sequence, you'll probably want to run it:

- [The Acquisition Engine](../../pymmcore-plus/guides/mda_engine.md) runs an
  `MDASequence` (or any iterable of `MDAEvent`) on a Micro-Manager-controlled
  microscope, and [Saving Data](../../pymmcore-plus/guides/saving_data.md) shows
  how to write the images to OME-Zarr or OME-TIFF.
- The [`MDASequence`](../schema/sequence.md), [`MDAEvent`](../schema/event.md) and
  [axes](../schema/axes.md) reference pages describe every field.
