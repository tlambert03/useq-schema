# Event

An [`MDAEvent`][useq.MDAEvent] describes one thing for the microscope to do
(usually: acquire an image), and the hardware state to do it in.  Fields that are
left as `None` mean "use the current setting".  Iterating over an
[`MDASequence`](sequence.md) yields events, but you can also create them yourself.

::: useq.MDAEvent
    options:
        members: []

::: useq.EventChannel
    options:
        members: []

::: useq.PropertyTuple
    options:
        members: []

## Event Actions

::: useq.Action
    options:
        members: []

::: useq.AcquireImage
    options:
        members: []

::: useq.HardwareAutofocus
    options:
        members: []

::: useq.CustomAction
    options:
        members: []
