# Usage Guide

`useq-schema` allows you to declaratively define complex multi-dimensional
microscopy acquisitions. This guide shows common patterns and recipes for
building sequences.

## Core Concepts

The [`MDASequence`][useq.MDASequence] object is the main container that describes your acquisition.
It combines multiple "plans" across different dimensions:

- **Channels** (`channels`): What channels/wavelengths to acquire
- **Z Stacks** (`z_plan`): How to move through depth
- **Timelapses** (`time_plan`): When to acquire over time
- **Grid/Tiles** (`grid_plan`): Multi-point spatial patterns
- **Stage Positions** (`stage_positions`): Discrete XYZ positions
- **Axis Order** (`axis_order`): The nesting order of dimensions (default:
  `"tpgcz"`)

The sequence itself is **iterable** - you can loop over it to get individual
[`MDAEvent`][useq.MDAEvent] objects:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI", "GFP"],
    z_plan={"range": 4, "step": 1}
)

for event in seq:
    print(f"Acquire {event.channel.config} at z={event.z_pos}")
```

## Channels

[`Channel`][useq.Channel] objects define what wavelengths/configurations to acquire and their settings.

### Simple Channels

Use strings for basic channel definitions:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI", "GFP", "Cy5"]
)
```

### Channels with Exposure

Add exposure times (in milliseconds) and other settings:

```python
import useq

seq = useq.MDASequence(
    channels=[
        useq.Channel(config="DAPI", exposure=100),
        useq.Channel(config="GFP", exposure=50),
        {"config": "Cy5", "exposure": 200}  # dict also works
    ]
)
```

### Advanced Channel Features

Channels support several advanced features:

```python
import useq

seq = useq.MDASequence(
    channels=[
        useq.Channel(
            config="DAPI",
            exposure=100,
            do_stack=True,          # Include in Z stacks (default: True)
            z_offset=2.0,           # Offset Z position by 2 microns
            acquire_every=2,        # Skip every other timepoint
            camera="Camera1"        # Specify which camera
        ),
        useq.Channel(
            config="GFP",
            exposure=50,
            do_stack=False          # Don't acquire Z stacks for this channel
        )
    ],
    z_plan={"range": 10, "step": 1}
)
```

**Key features:**

- `do_stack`: Set to `False` to skip Z stacks for a channel
- `z_offset`: Shift focal plane for chromatic aberration correction
- `acquire_every`: Acquire every Nth frame in timelapses (e.g., `2` = every
  other frame)

## Z Stacks

Control how the microscope moves through depth. All Z positions are in microns.

### Symmetric Range Around Current Position

Move symmetrically above and below the current Z position:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZRangeAround(
        range=10,      # Total range: 10 microns
        step=0.5       # Step size: 0.5 microns
    )
    # Equivalent shorthand:
    # z_plan={"range": 10, "step": 0.5}
)
# Visits: -5, -4.5, -4, ..., 4.5, 5 (relative to current position)
```

### Asymmetric Range (Above/Below)

Move different distances above and below:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZAboveBelow(
        above=6,       # 6 microns above
        below=4,       # 4 microns below
        step=1
    )
)
# Visits: -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6
```

### Absolute Z Positions

Define exact stage positions:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZTopBottom(
        bottom=100,    # Start at Z=100
        top=120,       # End at Z=120
        step=2
    )
)
# Visits: 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120
```

### Custom Z Positions

Specify exact positions as a list:

```python
import useq

# Relative positions
seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZRelativePositions(relative=[-2, -1, 0, 1, 3, 5])
)

# Absolute positions
seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZAbsolutePositions(absolute=[100, 105, 110, 120])
)
```

### Z Direction

All Z plans support `go_up` to control direction:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    z_plan=useq.ZRangeAround(range=10, step=1, go_up=False)  # Start high, go down
)
```

## Timelapses

Control when acquisitions happen over time.

### Fixed Interval with Loop Count

Acquire a fixed number of frames at regular intervals:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    time_plan=useq.TIntervalLoops(
        interval=10,   # 10 seconds between acquisitions
        loops=100      # 100 total frames
    )
    # Equivalent shorthand:
    # time_plan={"interval": 10, "loops": 100}
)
# Duration: 990 seconds (interval * (loops - 1))
```

Intervals can be specified as:

- Seconds (float): `interval=1.5`
- ISO 8601 strings: `interval="00:01:30"`  (1 minute 30 seconds)
- Dict: `interval={"minutes": 5, "seconds": 30}`
- timedelta objects: `interval=timedelta(minutes=5)`

### Fixed Duration with Loop Count

Divide a total duration into equal intervals:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    time_plan=useq.TDurationLoops(
        duration=3600,  # 1 hour total (can also use "01:00:00")
        loops=120       # 120 frames
    )
)
# Interval: 30 seconds (duration / (loops - 1))
```

### Fixed Interval and Duration

Compute the number of loops from interval and duration:

!!! warning
    Avoid using `TIntervalDuration` with an interval of zero, in
    the current version of useq-schema.  If you want to acquire as fast
    as possible, please prefer using `TIntervalLoops` for now.

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    time_plan=useq.TIntervalDuration(
        interval=5,           # 5 seconds between frames
        duration=300,         # 5 minutes total
        prioritize_duration=True  # Ensure duration is met (default)
    )
)
# Loops: 61 (computed from duration and interval)
```

### Multi-Phase Timelapses

Combine different temporal phases:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    time_plan=useq.MultiPhaseTimePlan(phases=[
        {"interval": 1, "loops": 60},    # 1 min: every 1 sec
        {"interval": 5, "loops": 60},    # 5 min: every 5 sec
        {"interval": 30, "loops": 120}   # 60 min: every 30 sec
    ])
    # Shorthand (automatically creates MultiPhaseTimePlan):
    # time_plan=[
    #     {"interval": 1, "loops": 60},
    #     {"interval": 5, "loops": 60},
    #     {"interval": 30, "loops": 120}
    # ]
)
```

## Grid/Tile Sets

Acquire multiple positions arranged in patterns.

### Regular Grid (Rows × Columns)

Create a grid centered on the current position or stage positions:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.GridRowsColumns(
        rows=3,
        columns=4,
        overlap=(10, 10),      # 10% overlap in X and Y
        fov_width=512,         # Field of view: 512 microns
        fov_height=512,
        mode="row_wise_snake"  # Traversal pattern (default)
    )
    # Equivalent shorthand:
    # grid_plan={"rows": 3, "columns": 4}
)
```

**Traversal modes** (`mode` parameter):

- `"row_wise"`: Left→right, top→bottom
- `"row_wise_snake"`: Alternating direction per row (default, faster)
- `"column_wise"`: Top→bottom, left→right
- `"column_wise_snake"`: Alternating direction per column
- `"spiral"`: Outward spiral from center

### Grid from Bounding Box

Define a grid by its outer edges (absolute positions):

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.GridFromEdges(
        top=1000,      # Top edge at Y=1000
        bottom=0,      # Bottom edge at Y=0
        left=0,        # Left edge at X=0
        right=1000,    # Right edge at X=1000
        fov_width=200,
        fov_height=200,
        overlap=(5, 5)
    )
)
# Creates grid to cover the 1000×1000 region
```

### Grid from Total Dimensions

Specify minimum width and height, let the library calculate rows/columns:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.GridWidthHeight(
        width=2000,       # Minimum 2000 microns wide
        height=1500,      # Minimum 1500 microns tall
        fov_width=250,
        fov_height=250,
        overlap=10
    )
)
```

### Polygon Region

Cover an arbitrary polygonal region:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.GridFromPolygon(
        vertices=[
            (0, 0),
            (1000, 0),
            (1000, 800),
            (500, 1200),
            (0, 800)
        ],
        fov_width=200,
        fov_height=200,
        overlap=10,
        convex_hull=False,  # Use exact polygon (default)
        offset=50           # Expand polygon by 50 microns
    )
)
```

**Key features:**

- `convex_hull=True`: Simplify to convex hull (faster, covers more area)
- `offset`: Positive = expand, negative = shrink, useful for margins
- Only positions whose FOV intersects the polygon are included

### Random Points

Generate random points, optionally optimized for efficient visiting:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.RandomPoints(
        num_points=50,
        max_width=2000,
        max_height=2000,
        shape=useq.Shape.ELLIPSE,          # or useq.Shape.RECTANGLE
        fov_width=100,
        fov_height=100,
        allow_overlap=False,          # Prevent FOV overlap (default: True)
        order=useq.TraversalOrder.TWO_OPT, # Optimize visit order
        random_seed=42                # For reproducibility
    )
)
```

**Traversal orders:**

- [`TraversalOrder.NEAREST_NEIGHBOR`][useq.TraversalOrder]: Greedy closest-point ordering (fast)
- [`TraversalOrder.TWO_OPT`][useq.TraversalOrder]: Iterative optimization (slower, better paths)
- [`TraversalOrder.RANDOM`][useq.TraversalOrder]: Random order (no optimization)
- `None`: Original order (default if not using random points)

## Stage Positions

Define discrete XYZ positions to visit.

### Basic Positions

Positions can be specified as tuples, dicts, or [`Position`][useq.Position] objects:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=[
        (100, 200, 50),                  # Tuple: (x, y, z)
        useq.Position(x=500, y=600, z=50),  # Position object
        {"x": 1000, "y": 1200}           # Dict (z is optional)
    ]
)
```

**Note:** Coordinates are in microns. `None` means "don't move that axis".

### Named Positions

Add names for easier identification:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=[
        useq.Position(x=0, y=0, name="Center"),
        useq.Position(x=1000, y=0, name="Right"),
        useq.Position(x=0, y=1000, name="Top")
    ]
)

for event in seq:
    print(f"At position: {event.pos_name}")
```

### Positions with Sub-Sequences

Each position can have its own acquisition sequence:

```python
import useq

seq = useq.MDASequence(
    channels=["Cy5"],  # Global channel
    stage_positions=[
        useq.Position(x=0, y=0),  # Simple position: one acquisition
        useq.Position(
            x=1000,
            y=1000,
            name="Sample",
            sequence=useq.MDASequence(
                channels=["DAPI", "GFP"],  # Override global channels
                z_plan={"range": 10, "step": 1}  # Z stack only here
            )
        )
    ]
)
```

**Pattern:** Sub-sequences **replace** the global settings for that position.

### Per-Position Grids

Apply a grid pattern at each position:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=[
        useq.Position(
            x=0, y=0, name="Region1",
            sequence=useq.MDASequence(
                grid_plan=useq.GridRowsColumns(rows=3, columns=3)
            )
        ),
        useq.Position(
            x=2000, y=2000, name="Region2",
            sequence=useq.MDASequence(
                grid_plan=useq.GridRowsColumns(rows=2, columns=2)
            )
        )
    ]
)
# Creates a 3×3 grid at (0,0) and a 2×2 grid at (2000,2000)
```

### Per-Position Timelapses

Run different timelapses at each position:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=[
        useq.Position(
            x=0, y=0, name="FastGrowing",
            sequence=useq.MDASequence(
                time_plan={"interval": 5, "loops": 100}
            )
        ),
        useq.Position(
            x=1000, y=1000, name="SlowGrowing",
            sequence=useq.MDASequence(
                time_plan={"interval": 30, "loops": 50}
            )
        )
    ]
)
```

**Note:** Per-position time plans run independently and may have different
lengths.

### Combining Global and Per-Position Plans

Position-specific settings override global ones:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI", "GFP"],          # Global channels
    z_plan={"range": 5, "step": 1},    # Global Z plan
    stage_positions=[
        useq.Position(x=0, y=0),             # Uses global plans
        useq.Position(
            x=1000, y=1000,
            sequence=useq.MDASequence(
                channels=["Cy5"],       # Override: different channels
                z_plan={"range": 10, "step": 0.5}  # Override: finer Z stack
            )
        )
    ]
)
```

## Multi-well Plates

Define stage positions based on standard multi-well plate layouts using [`WellPlatePlan`][useq.WellPlatePlan].

### Basic Well Plate

```python
import useq
import numpy as np

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=useq.WellPlatePlan(
        plate="96-well",                # Or "384-well", etc.
        a1_center_xy=(100, 200),        # Stage position of well A1 center
        selected_wells=np.s_[0:2, 0:2]  # First 2 rows, first 2 columns (A1, A2, B1, B2)
    )
)
```

**Available plate types:**

- `"6-well"`, `"12-well"`, `"24-well"`, `"48-well"`
- `"96-well"`, `"384-well"`, `"1536-well"`

**Well selection** uses numerical indices (0-based):

- `selected_wells=np.s_[0:2, 0:3]` - rows 0-1 (A-B), columns 0-2 (1-3)
- `selected_wells=[(0, 0), (1, 1)]` - specific wells: A1, B2
- `selected_wells=slice(None)` - select all wells
- For 96-well plate: 8 rows (0-7 = A-H), 12 columns (0-11 = 1-12)

### Well Plate with Multi-Point Imaging

Add a grid or random points within each well:

```python
import useq
import numpy as np

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=useq.WellPlatePlan(
        plate="96-well",
        a1_center_xy=(0, 0),
        selected_wells=np.s_[0:2, 0:3],  # Wells A1-A3, B1-B3
        well_points_plan=useq.GridRowsColumns(rows=3, columns=3)  # 3x3 grid per well
    )
)
```

### Custom Well Plates

Register custom plate geometries:

```python
import useq

custom_plate = useq.WellPlate(
    name="custom-24",
    rows=4,
    columns=6,
    well_spacing=(19.3, 19.3),  # mm between well centers
    well_size=(15.6, 15.6)      # mm well dimensions
)

useq.register_well_plates({"custom-24": custom_plate})

# Now use it
seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=useq.WellPlatePlan(
        plate="custom-24",
        a1_center_xy=(0, 0),
        selected_wells=[(0, 0), (3, 5)]  # Wells A1 and D6
    )
)
```

## Defining Dimension Order

The `axis_order` parameter controls how dimensions are nested. Default is
`"tpgcz"`:

- **t**: Time
- **p**: Position (stage positions)
- **g**: Grid (tile positions)
- **c**: Channel
- **z**: Z stack

### Default Order (tpgcz)

```python
import useq

seq = useq.MDASequence(
    axis_order="tpgcz",  # Default
    time_plan={"interval": 60, "loops": 2},    # Outer loop
    stage_positions=[(0, 0), (100, 100)],
    channels=["DAPI", "GFP"],
    z_plan={"range": 4, "step": 1}             # Inner loop
)
```

**Iteration order:**

1. All positions, channels, and Z for time=0
2. All positions, channels, and Z for time=1

### Channel-First Order (cpz)

Acquire all channels before moving:

```python
import useq

seq = useq.MDASequence(
    axis_order="cpz",
    stage_positions=[(0, 0), (100, 100)],
    channels=["DAPI", "GFP"],
    z_plan={"range": 4, "step": 1}
)
```

**Iteration order:**

1. Position 0: DAPI (all Z), then GFP (all Z)
2. Position 1: DAPI (all Z), then GFP (all Z)

### Z-First Order (zcpt)

Complete Z stacks before changing channels:

```python
import useq

seq = useq.MDASequence(
    axis_order="tpzc",  # Z before C
    time_plan={"interval": 60, "loops": 2},
    stage_positions=[(0, 0), (100, 100)],
    channels=["DAPI", "GFP"],
    z_plan={"range": 4, "step": 1}
)
```

**Useful when:** Minimizing Z motion is critical (e.g., piezo stage settling
time).

### Common Patterns

- `"tpgcz"` (default): Natural order, good for most applications
- `"tpgzc"`: Minimize channel switching (keeps shutter closed longer)
- `"tgpcz"`: Visit all grid positions before changing position (rare)
- `"cztp"`: Channels outer-most (acquire all timepoints per channel)

**Important constraints:**

- If using per-position Z plans, `"z"` must come after `"p"`
- When using `acquire_every > 1` on channels, `"c"` should come before `"t"`

## Advanced Features

### Hardware Autofocus

Perform autofocus when specific axes change:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI", "GFP"],
    stage_positions=[(0, 0), (100, 100), (200, 200)],
    z_plan={"range": 10, "step": 1},
    autofocus_plan=useq.AxesBasedAF(
        axes=("p",),                        # Autofocus when position changes
        autofocus_device_name="PFSOffset",  # Hardware autofocus device
        autofocus_motor_offset=100          # Optional offset in microns
    )
    # Equivalent shorthand:
    # autofocus_plan={"axes": ("p",)}
)
```

**Common patterns:**

- `axes=("p",)`: Autofocus at each position
- `axes=("t",)`: Autofocus at each timepoint
- `axes=("c",)`: Autofocus for each channel (chromatic correction)
- `axes=("p", "t")`: Autofocus when either position or time changes

**Per-position autofocus:**

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    stage_positions=[
        useq.Position(x=0, y=0),  # No autofocus
        useq.Position(
            x=1000, y=1000,
            sequence=useq.MDASequence(
                z_plan={"range": 10, "step": 1},
                autofocus_plan={"axes": ("c",)}  # AF for each channel here
            )
        )
    ]
)
```

### Keep Shutter Open

Reduce photobleaching by keeping the illumination shutter open between
acquisitions:

```python
import useq

seq = useq.MDASequence(
    axis_order="tcz",
    channels=["DAPI", "GFP"],
    time_plan={"interval": 60, "loops": 5},
    z_plan={"range": 10, "step": 1},
    keep_shutter_open_across=("z",)  # Keep open during Z stack
)
```

**Behavior:** Shutter stays open between events if **all** changing axes are in
this tuple.

**Examples:**

- `keep_shutter_open_across=("z",)`: Open during Z stacks
- `keep_shutter_open_across=("z", "c")`: Open during Z stacks and channel
  changes
- `keep_shutter_open_across=("z", "t")`: Open across Z and time

**Note:** Requires compatible `axis_order`. For example,
`keep_shutter_open_across=("z",)` won't work if `"z"` is not the
fastest-changing axis.

### Metadata

Attach custom metadata to sequences or events:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    metadata={
        "experiment": "cell_division",
        "researcher": "Jane Doe",
        "temperature": 37.0,
        "notes": "Control sample"
    }
)
```

Metadata propagates to events and can be accessed during iteration.

### Sequence Properties

Inspect sequence properties before running:

```python
import useq

seq = useq.MDASequence(
    time_plan={"interval": 10, "loops": 5},
    stage_positions=[(0, 0), (100, 100)],
    channels=["DAPI", "GFP"],
    z_plan={"range": 4, "step": 1}
)

print(seq.shape)       # (5, 2, 2, 5) - dimensions of the sequence
print(seq.sizes)       # {'t': 5, 'p': 2, 'g': 0, 'c': 2, 'z': 5}
print(seq.used_axes)   # "tpcz" - axes with size > 0
print(len(list(seq)))  # 100 - total number of events

# Estimate duration
estimate = seq.estimate_duration()
print(estimate.total_duration)        # ~40 seconds
print(estimate.per_t_duration)        # ~10 seconds per timepoint
print(estimate.time_interval_exceeded)  # False
```

### Unique Identifiers

Each sequence has a unique ID:

```python
import useq

seq1 = useq.MDASequence(channels=["DAPI"])
seq2 = useq.MDASequence(channels=["DAPI"])

print(seq1.uid)  # UUID: e.g., "a1b2c3d4-..."
print(seq2.uid)  # Different UUID

# Compare sequences (ignoring UID)
print(seq1 == seq2)  # True - content is identical
print(seq1.uid == seq2.uid)  # False - different instances
```

## Common Recipes

### Time-lapse with Multi-Point

Capture multiple positions over time:

```python
import useq

seq = useq.MDASequence(
    axis_order="tpgcz",
    channels=["Phase", "GFP"],
    stage_positions=[(0, 0), (500, 500), (1000, 1000)],
    time_plan={"interval": "00:05:00", "loops": 50}  # Every 5 min, 50 frames
)
```

### Z-Stack with Chromatic Correction

Correct chromatic aberration with per-channel Z offsets:

```python
import useq

seq = useq.MDASequence(
    channels=[
        useq.Channel(config="DAPI", z_offset=-0.5),  # 0.5 µm below focal plane
        useq.Channel(config="GFP", z_offset=0.0),    # At focal plane
        useq.Channel(config="Cy5", z_offset=0.3)     # 0.3 µm above focal plane
    ],
    z_plan={"range": 10, "step": 0.5}
)
```

### Large Tiled Region with Time-lapse

Scan a large area at multiple timepoints:

```python
import useq

seq = useq.MDASequence(
    axis_order="tgcz",  # Time outer-most, grid before channels
    channels=["DAPI"],
    time_plan={"interval": "00:10:00", "loops": 20},
    grid_plan=useq.GridRowsColumns(
        rows=5,
        columns=5,
        fov_width=512,
        fov_height=512,
        overlap=10,
        mode="row_wise_snake"
    )
)
```

### Multi-Well Plate with Grids

Image multiple wells with a grid pattern in each:

```python
import useq
import numpy as np

seq = useq.MDASequence(
    channels=["DAPI", "GFP"],
    stage_positions=useq.WellPlatePlan(
        plate="96-well",
        a1_center_xy=(1000, 2000),
        selected_wells=np.s_[0:3, 0:2],  # Wells A1-A2, B1-B2, C1-C2
        well_points_plan=useq.GridRowsColumns(
            rows=3, columns=3, overlap=10
        )
    )
)
```

### Fast Time-lapse with Occasional High-Resolution

Combine fast low-res with slow high-res imaging:

```python
import useq

seq = useq.MDASequence(
    axis_order="tcz",
    channels=[
        useq.Channel(config="Phase", do_stack=False, acquire_every=1),  # Every frame
        useq.Channel(config="GFP", do_stack=True, acquire_every=10)     # Every 10th frame
    ],
    time_plan={"interval": 5, "loops": 100},
    z_plan={"range": 10, "step": 1}
)
# Phase: 100 frames (no Z)
# GFP: 10 frames (with Z stack)
```

### Sparse Sampling with Random Points

Sample sparse regions efficiently:

```python
import useq

seq = useq.MDASequence(
    channels=["DAPI"],
    grid_plan=useq.RandomPoints(
        num_points=100,
        max_width=5000,
        max_height=5000,
        shape="ellipse",
        fov_width=200,
        fov_height=200,
        allow_overlap=False,
        order=useq.TraversalOrder.TWO_OPT,  # Optimize path
        random_seed=42
    ),
    z_plan={"range": 5, "step": 1}
)
```

## Next Steps

- See the [API Reference](api.md) for complete class documentation
- Check out
  [examples](https://github.com/pymmcore-plus/useq-schema/tree/main/examples)
  for more complex use cases
- For hardware integration, see
  [pymmcore-plus](https://github.com/pymmcore-plus/pymmcore-plus)
