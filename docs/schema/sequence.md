# Sequence

An [`MDASequence`][useq.MDASequence] describes a whole experiment: a plan for each
axis (time, stage positions, grid, channels and z), and the order in which to
iterate them.  See [Building Sequences](../guides/sequences.md) for examples.

::: useq.MDASequence
    options:
        show_signature: true
        show_signature_annotations: true

## How sequences are iterated

Iterating an `MDASequence` yields [`MDAEvent`][useq.MDAEvent] objects.  The
logic lives in `iter_sequence`, an implementation detail (it isn't part of the
schema itself) that is shown here for reference:

::: useq._iter_sequence.iter_sequence
    options:
        heading_level: 3
        show_root_full_path: false
        show_source: true
        show_signature_annotations: false
