import math
from typing import Any, List, Tuple, Union

from pydantic import BaseModel, ValidationError
from pydantic_core import core_schema

# Type alias for color input formats
ColorInput = Union[str, List[int], Tuple[int, ...], List[float], Tuple[float, ...]]

class RGBAColor:
    """
    A class to represent an RGBA color, supporting multiple input formats,
    conversions, color mixing, and Pydantic validation.

    The color is stored internally as four float values (r, g, b, a)
    ranging from 0.0 to 1.0.
    """

    __slots__ = ('_r', '_g', '_b', '_a')

    def __init__(self, value: ColorInput):
        """
        Initializes an RGBA color from various formats.

        :param value: The color value, which can be:
            - A hex string (e.g., '#FF0000', '#FF000080').
            - A list/tuple of 3 or 4 integers (0-255).
            - A list/tuple of 3 or 4 floats (0.0-1.0).
        :type value: ColorInput
        :raises ValueError: If the input format is invalid or values are out of range.
        :raises TypeError: If the input type is unsupported.
        """
        if isinstance(value, str):
            # Parse from hex string
            hex_val = value.lstrip('#')
            if len(hex_val) not in (6, 8):
                raise ValueError("Hex string must be 6 or 8 characters long (excluding '#')")
            
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            a = int(hex_val[6:8], 16) if len(hex_val) == 8 else 255
            
            self._r = r / 255.0
            self._g = g / 255.0
            self._b = b / 255.0
            self._a = a / 255.0

        elif isinstance(value, (list, tuple)):
            if not (3 <= len(value) <= 4):
                raise ValueError("Color lists/tuples must have 3 or 4 elements")

            if all(isinstance(x, int) for x in value):
                # Parse from byte values (0-255)
                if not all(0 <= x <= 255 for x in value):
                    raise ValueError("Integer color values must be between 0 and 255")
                self._r = value[0] / 255.0
                self._g = value[1] / 255.0
                self._b = value[2] / 255.0
                self._a = value[3] / 255.0 if len(value) == 4 else 1.0
            elif all(isinstance(x, (float, int)) for x in value):
                # Parse from float values (0.0-1.0)
                if not all(0.0 <= x <= 1.0 for x in value):
                    raise ValueError("Float color values must be between 0.0 and 1.0")
                self._r = float(value[0])
                self._g = float(value[1])
                self._b = float(value[2])
                self._a = float(value[3]) if len(value) == 4 else 1.0
            else:
                raise TypeError("Color list/tuple must contain either all ints or all floats.")
        else:
            raise TypeError(f"Unsupported type for color initialization: {type(value)}")

    @staticmethod
    def _clamp(value: float) -> float:
        """
        Clamps a float value between 0.0 and 1.0.

        :param value: The float value to clamp.
        :type value: float
        :return: The clamped float value.
        :rtype: float
        """
        return max(0.0, min(1.0, value))

    @property
    def r(self) -> float:
        """The red component of the color (0.0-1.0)."""
        return self._r

    @r.setter
    def r(self, value: float):
        self._r = self._clamp(value)

    @property
    def g(self) -> float:
        """The green component of the color (0.0-1.0)."""
        return self._g

    @g.setter
    def g(self, value: float):
        self._g = self._clamp(value)

    @property
    def b(self) -> float:
        """The blue component of the color (0.0-1.0)."""
        return self._b

    @b.setter
    def b(self, value: float):
        self._b = self._clamp(value)

    @property
    def a(self) -> float:
        """The alpha component of the color (0.0-1.0)."""
        return self._a

    @a.setter
    def a(self, value: float):
        self._a = self._clamp(value)

    def to_hex(self, include_alpha: bool = True) -> str:
        """
        Converts the color to a hex string.

        :param include_alpha: If True, includes the alpha channel in the hex string.
        :type include_alpha: bool
        :return: The hex string representation (e.g., '#RRGGBBAA').
        :rtype: str
        """
        r_hex = f"{int(self.r * 255):02x}"
        g_hex = f"{int(self.g * 255):02x}"
        b_hex = f"{int(self.b * 255):02x}"
        if include_alpha:
            a_hex = f"{int(self.a * 255):02x}"
            return f"#{r_hex}{g_hex}{b_hex}{a_hex}"
        return f"#{r_hex}{g_hex}{b_hex}"

    def to_bytes(self) -> Tuple[int, int, int, int]:
        """
        Converts the color to a tuple of byte values (0-255).

        :return: A tuple (r, g, b, a) where each component is an integer from 0 to 255.
        :rtype: Tuple[int, int, int, int]
        """
        return (
            int(self.r * 255),
            int(self.g * 255),
            int(self.b * 255),
            int(self.a * 255),
        )

    def to_floats(self) -> Tuple[float, float, float, float]:
        """
        Converts the color to a tuple of float values (0.0-1.0).

        :return: A tuple (r, g, b, a) where each component is a float from 0.0 to 1.0.
        :rtype: Tuple[float, float, float, float]
        """
        return (self.r, self.g, self.b, self.a)

    def mix(self, other: 'RGBAColor', weight: float = 0.5) -> 'RGBAColor':
        """
        Mixes this color with another color using linear interpolation.

        :param other: The other RGBA color to mix with.
        :type other: RGBAColor
        :param weight: The mixing weight. 0.0 gives this color, 1.0 gives the
                       other color, and 0.5 gives an even mix. Clamped between 0.0 and 1.0.
        :type weight: float
        :return: A new RGBAColor instance representing the mixed color.
        :rtype: RGBAColor
        :raises TypeError: If `other` is not an RGBAColor instance.
        """
        if not isinstance(other, RGBAColor):
            raise TypeError("Can only mix with another RGBA instance.")
        
        w = self._clamp(weight)
        
        mixed_r = self.r * (1 - w) + other.r * w
        mixed_g = self.g * (1 - w) + other.g * w
        mixed_b = self.b * (1 - w) + other.b * w
        mixed_a = self.a * (1 - w) + other.a * w
        
        return RGBAColor([mixed_r, mixed_g, mixed_b, mixed_a])
    
    def is_transparent(self):
        """
        Checks if the color is fully transparent (alpha=0.0).

        :return: True if the color is fully transparent, False otherwise.
        :rtype: bool
        """
        return self.a == 0.0

    def __repr__(self) -> str:
        """
        Returns a developer-friendly string representation of the RGBAColor object.
        """
        return f"RGBA(value='{self.to_hex()}')"

    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the RGBAColor object (its hex value).
        """
        return self.to_hex()

    def __len__(self) -> int:
        """
        Returns the number of color components (always 4 for RGBA).
        """
        return 4

    def __iter__(self):
        """
        Allows unpacking the color components like `r, g, b, a = my_color`.
        """
        yield self.r
        yield self.g
        yield self.b
        yield self.a

    def __getitem__(self, index: int) -> float:
        """
        Allows accessing color components by index (0=r, 1=g, 2=b, 3=a).

        :param index: The index of the component to retrieve.
        :type index: int
        :return: The float value of the specified component.
        :rtype: float
        """
        return self.to_floats()[index]
    
    def __eq__(self, other: Any) -> bool:
        """
        Checks for equality with another RGBAColor instance based on byte values.

        :param other: The object to compare with.
        :type other: Any
        :return: True if the colors are equal, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, RGBAColor):
            return NotImplemented
        return self.to_bytes() == other.to_bytes()

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """
        Defines how Pydantic should validate and serialize this class.

        :param source_type: The type being validated.
        :type source_type: Any
        :param handler: The Pydantic schema handler.
        :type handler: Any
        :return: A Pydantic CoreSchema for validation and serialization.
        :rtype: core_schema.CoreSchema
        """
        # This function will be called by Pydantic to validate input
        def validate(value: ColorInput) -> 'RGBAColor':
            try:
                return RGBAColor(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid color format: {e}") from e

        # Define the schema for validation
        from_input_schema = core_schema.no_info_plain_validator_function(validate)
        
        # Define how the class should be serialized (e.g., to JSON)
        # Here, we serialize to a hex string.
        to_hex_serializer = core_schema.plain_serializer_function_ser_schema(
            lambda c: c.to_hex(),
            when_used='json-unless-none'
        )

        return core_schema.json_or_python_schema(
            json_schema=from_input_schema,
            python_schema=from_input_schema,
            serialization=to_hex_serializer,
        )
