from __future__ import annotations

from collections.abc import Iterator, Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any, Union, cast, overload

import numpy as np
from pydantic import Field, field_validator

from useq._common import _plate
from useq._common._enums import Shape
from useq._grid import RandomPoints, RelativeMultiPointPlan
from useq.v1._position import Position, PositionBase, RelativePosition

if TYPE_CHECKING:
    from pydantic_core import core_schema

    Index = Union[int, list[int], slice]
    IndexExpression = Union[tuple[Index, ...], Index]


class WellPlatePlan(_plate.WellPlatePlan, Sequence[Position]):
    """A plan for acquiring images from a multi-well plate.

    Parameters
    ----------
    plate : WellPlate | str | int
        The well-plate definition. Minimally including rows, columns, and well spacing.
        If expressed as a string, it is assumed to be a key in
        `useq.registered_well_plate_keys`.
    a1_center_xy : tuple[float, float]
        The stage coordinates in µm of the center of well A1 (top-left corner).
    rotation : float | None
        The rotation angle in degrees (anti-clockwise) of the plate.
        If None, no rotation is applied.
        If expressed as a string, it is assumed to be an angle with units (e.g., "5°",
        "4 rad", "4.5deg").
        If expressed as an arraylike, it is assumed to be a 2x2 rotation matrix
        `[[cos, -sin], [sin, cos]]`, or a 4-tuple `(cos, -sin, sin, cos)`.
    selected_wells : IndexExpression | None
        Any <=2-dimensional index expression for selecting wells.
        for example:
        -   None -> No wells are selected.
        -   slice(0) -> (also) select no wells.
        -   slice(None) -> Selects all wells.
        -   0 -> Selects the first row.
        -   [0, 1, 2] -> Selects the first three rows.
        -   slice(1, 5) -> selects wells from row 1 to row 4.
        -   (2, slice(1, 4)) -> select wells in the second row and only columns 1 to 3.
        -   ([1, 2], [3, 4]) -> select wells in (row, column): (1, 3) and (2, 4)
    well_points_plan : GridRowsColumns | RandomPoints | Position
        A plan for acquiring images within each well. This can be a single position
        (for a single image per well), a GridRowsColumns (for a grid of images),
        or RandomPoints (for random points within each well).
    """

    well_points_plan: RelativeMultiPointPlan = Field(
        default_factory=RelativePosition, union_mode="left_to_right"
    )

    @field_validator("well_points_plan", mode="wrap")
    @classmethod
    def _validate_well_points_plan(
        cls,
        value: Any,
        handler: core_schema.ValidatorFunctionWrapHandler,
        info: core_schema.ValidationInfo,
    ) -> Any:
        value = handler(value)
        if plate := info.data.get("plate"):
            if isinstance(value, RandomPoints):
                plate = cast("_plate.WellPlate", plate)
                kwargs = value.model_dump(mode="python")
                if value.max_width == np.inf:
                    well_size_x = plate.well_size[0] * 1000  # convert to µm
                    kwargs["max_width"] = well_size_x - (value.fov_width or 0.1)
                if value.max_height == np.inf:
                    well_size_y = plate.well_size[1] * 1000  # convert to µm
                    kwargs["max_height"] = well_size_y - (value.fov_height or 0.1)
                if "shape" not in value.__pydantic_fields_set__:
                    kwargs["shape"] = (
                        Shape.ELLIPSE if plate.circular_wells else Shape.RECTANGLE
                    )
                value = RandomPoints(**kwargs)
        return value

    def __iter__(self) -> Iterator[Position]:  # type: ignore
        """Iterate over the selected positions."""
        yield from self.image_positions

    @overload
    def __getitem__(self, index: int) -> Position: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Position]: ...

    def __getitem__(self, index: int | slice) -> Position | Sequence[Position]:
        """Return the selected position(s) at the given index."""
        return self.image_positions[index]

    @property
    def num_points_per_well(self) -> int:
        """Return the number of points per well."""
        if isinstance(self.well_points_plan, PositionBase):
            return 1
        else:
            return self.well_points_plan.num_positions()

    @property
    def all_well_positions(self) -> Sequence[Position]:
        """Return all wells (centers) as Position objects."""
        return [
            Position(x=x * 1000, y=y * 1000, name=name)  # convert to µm
            for (y, x), name in zip(
                self.all_well_coordinates, self.all_well_names.reshape(-1)
            )
        ]

    @cached_property
    def selected_well_positions(self) -> Sequence[Position]:
        """Return selected wells (centers) as Position objects."""
        return [
            Position(x=x * 1000, y=y * 1000, name=name)  # convert to µm
            for (y, x), name in zip(
                self.selected_well_coordinates, self.selected_well_names
            )
        ]

    @cached_property
    def image_positions(self) -> Sequence[Position]:
        """All image positions.

        This includes *both* selected wells and the image positions within each well
        based on the `well_points_plan`.  This is the primary property that gets used
        when iterating over the plan.
        """
        wpp = self.well_points_plan
        offsets = [wpp] if isinstance(wpp, RelativePosition) else wpp
        pos: list[Position] = []
        for well in self.selected_well_positions:
            pos.extend(well + offset for offset in offsets)
        return pos
