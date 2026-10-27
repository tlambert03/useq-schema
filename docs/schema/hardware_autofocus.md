# Hardware Autofocus Plan

Ways to describe a hardware-based autofocus plan.  An `autofocus_plan` on an
[`MDASequence`](sequence.md) inserts events with a
[`HardwareAutofocus`][useq.HardwareAutofocus] action into the sequence (for
example, every time the stage position changes).

::: useq.AutoFocusPlan
    options:
        show_signature: true
        show_signature_annotations: true
        members:
            - as_action
            - event
            - should_autofocus

::: useq.AxesBasedAF
    options:
        show_source: true
        show_signature: true
        show_signature_annotations: true
        members:
            - should_autofocus
