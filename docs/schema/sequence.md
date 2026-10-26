# Sequence

::: useq.MDASequence
    options:
        show_signature: true
        show_signature_annotations: true

## How sequences are iterated

Iterating an `MDASequence` yields [`MDAEvent`][useq.MDAEvent] objects.  The
logic lives in `iter_sequence`, which is shown here for reference:

::: useq._iter_sequence.iter_sequence
    options:
        heading_level: 3
        show_source: true
        show_signature_annotations: false
