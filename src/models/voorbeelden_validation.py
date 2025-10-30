"""Pydantic validation schemas for voorbeelden data structures.

Created for DEF-74: Add input validation for voorbeelden to prevent type errors.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class VoorbeeldenDict(BaseModel):
    """Validates the voorbeelden dictionary structure.

    Expected structure:
    {
        "voorbeeldzinnen": ["zin 1", "zin 2", ...],
        "praktijkvoorbeelden": ["voorbeeld 1", ...],
        "tegenvoorbeelden": ["tegen 1", ...],
        ...
    }

    All keys must be strings, all values must be lists of strings.
    Empty strings are filtered out automatically.
    """

    data: dict[str, list[str]] = Field(
        ...,
        description="Dictionary mapping example type to list of example strings",
    )

    @field_validator("data")
    @classmethod
    def validate_structure(cls, v: Any) -> dict[str, list[str]]:
        """Validate that data is a dict with string keys and list[str] values."""
        if not isinstance(v, dict):
            msg = f"voorbeelden_dict must be a dictionary, got {type(v).__name__}"
            raise TypeError(msg)

        validated = {}
        for key, value in v.items():
            # Validate key is string
            if not isinstance(key, str):
                msg = f"Key must be string, got {type(key).__name__}: {key}"
                raise TypeError(msg)

            # Validate value is list
            if not isinstance(value, list):
                msg = (
                    f"Value for key '{key}' must be a list, got {type(value).__name__}"
                )
                raise TypeError(msg)

            # Filter and validate list items
            validated_items = []
            for item in value:
                if not isinstance(item, str):
                    msg = f"Items in '{key}' must be strings, got {type(item).__name__}: {item}"
                    raise TypeError(msg)
                # Only keep non-empty strings
                if item.strip():
                    validated_items.append(item)

            # Only include keys with at least one non-empty value
            if validated_items:
                validated[key] = validated_items

        return validated

    @model_validator(mode="after")
    def check_has_examples(self) -> VoorbeeldenDict:
        """Ensure at least one example type has at least one example."""
        total_examples = sum(len(examples) for examples in self.data.values())
        if total_examples == 0:
            msg = "voorbeelden_dict must contain at least one non-empty example"
            raise ValueError(msg)
        return self

    def to_dict(self) -> dict[str, list[str]]:
        """Return the validated dictionary."""
        return self.data


class SaveVoorbeeldenInput(BaseModel):
    """Validates all input parameters for save_voorbeelden() function.

    This ensures type safety before calling the repository method.
    """

    definitie_id: int = Field(..., gt=0, description="Definition ID (must be > 0)")
    voorbeelden_dict: dict[str, list[str]] = Field(
        ..., description="Dictionary mapping example type to list of examples"
    )
    generation_model: str | None = Field(
        None, description="Model used for generation (optional)"
    )
    generation_params: dict[str, Any] | None = Field(
        None, description="Parameters used for generation (optional)"
    )
    gegenereerd_door: str = Field(
        default="system",
        min_length=1,
        description="Who generated the examples",
    )
    voorkeursterm: str | None = Field(
        None, description="Optional preferred term (saved as synonym)"
    )

    @field_validator("definitie_id")
    @classmethod
    def validate_definitie_id(cls, v: int) -> int:
        """Ensure definitie_id is a positive integer."""
        if v <= 0:
            msg = f"definitie_id must be positive, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("voorbeelden_dict")
    @classmethod
    def validate_voorbeelden(cls, v: Any) -> dict[str, list[str]]:
        """Validate voorbeelden_dict using VoorbeeldenDict schema."""
        validated = VoorbeeldenDict(data=v)
        return validated.to_dict()

    @field_validator("gegenereerd_door")
    @classmethod
    def validate_gegenereerd_door(cls, v: str) -> str:
        """Ensure gegenereerd_door is not empty."""
        if not v or not v.strip():
            msg = "gegenereerd_door cannot be empty"
            raise ValueError(msg)
        return v.strip()


def validate_save_voorbeelden_input(
    definitie_id: int,
    voorbeelden_dict: dict[str, list[str]],
    generation_model: str | None = None,
    generation_params: dict[str, Any] | None = None,
    gegenereerd_door: str = "system",
    voorkeursterm: str | None = None,
) -> SaveVoorbeeldenInput:
    """Convenience function to validate save_voorbeelden() inputs.

    Args:
        definitie_id: ID of the definition
        voorbeelden_dict: Dictionary with examples per type
        generation_model: Model used for generation
        generation_params: Parameters used for generation
        gegenereerd_door: Who generated the examples
        voorkeursterm: Optional preferred term

    Returns:
        Validated SaveVoorbeeldenInput model

    Raises:
        ValidationError: If any input is invalid (contains detailed error info)

    Example:
        ```python
        try:
            validated = validate_save_voorbeelden_input(
                definitie_id=23,
                voorbeelden_dict={
                    "voorbeeldzinnen": ["zin 1", "zin 2"],
                    "praktijkvoorbeelden": ["voorbeeld 1"]
                }
            )
            repo.save_voorbeelden(**validated.model_dump())
        except ValidationError as e:
            logger.error(f"Invalid voorbeelden input: {e}")
            st.error("⚠️ Ongeldige voorbeelden - controleer invoer")
        ```
    """
    return SaveVoorbeeldenInput(
        definitie_id=definitie_id,
        voorbeelden_dict=voorbeelden_dict,
        generation_model=generation_model,
        generation_params=generation_params,
        gegenereerd_door=gegenereerd_door,
        voorkeursterm=voorkeursterm,
    )
