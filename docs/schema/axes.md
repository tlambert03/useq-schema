# Axes

The following objects may be used to describe iteration over specific
types of dimensions.

::: useq.Position
    options:
        heading_level: 2
        members: []

::: useq.Channel
    options:
        heading_level: 2
        members: []

## Time Plans

Ways to describe a temporal acquisition sequence.

::: useq.TIntervalDuration
    options:
        members: []
::: useq.TIntervalLoops
    options:
        members: []
::: useq.TDurationLoops
    options:
        members: []
::: useq.MultiPhaseTimePlan
    options:
        members: []

## Z Plans

Ways to describe a z-stack acquisition sequence.

::: useq.ZTopBottom
    options:
        members: []
::: useq.ZAboveBelow
    options:
        members: []
::: useq.ZAbsolutePositions
    options:
        members: []
::: useq.ZRangeAround
    options:
        members: []
::: useq.ZRelativePositions
    options:
        members: []

## Grid Plans

Ways to describe a grid acquisition sequence.

::: useq.GridRowsColumns
    options:
        members: []
::: useq.GridWidthHeight
    options:
        members: []
::: useq.GridFromEdges
    options:
        members: []
::: useq.RandomPoints
    options:
        members: []
::: useq.GridFromPolygon
    options:
        members: []

### Grid options

::: useq.OrderMode
::: useq.Shape
::: useq.TraversalOrder

## Well plates

::: useq.WellPlatePlan
    options:
        members: []

::: useq.WellPlate
    options:
        members: []

::: useq.register_well_plates

::: useq.registered_well_plate_keys
