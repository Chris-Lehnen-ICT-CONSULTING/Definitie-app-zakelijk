"""Manual test script voor category refactoring."""

import streamlit as st

from database.definitie_repository import get_definitie_repository
from models.category_models import DefinitionCategory
from services.category_service import CategoryService
from services.category_state_manager import CategoryStateManager

st.title("🧪 Category Refactoring Test")

st.markdown("## Test 1: CategoryService v2")

# Initialize service
repo = get_definitie_repository()
service = CategoryService(repo)

# Test inputs
definition_id = st.number_input("Definition ID", min_value=1, value=1)
new_category = st.selectbox(
    "New Category", ["ENT", "REL", "ACT", "ATT", "AUT", "STA", "OTH"]
)
user = st.text_input("User", value="test_user")
reason = st.text_input("Reason", value="Manual test")

if st.button("Test Category Update"):
    # Test v2 method
    result = service.update_category_v2(definition_id, new_category, user, reason)

    if result.success:
        st.success(f"✅ {result.message}")
        st.json(
            {
                "success": result.success,
                "message": result.message,
                "previous_category": result.previous_category,
                "new_category": result.new_category,
                "timestamp": str(result.timestamp),
            }
        )
    else:
        st.error(f"❌ {result.message}")

st.markdown("---")

st.markdown("## Test 2: CategoryStateManager")

# Test generation result
test_result = {
    "begrip": "test_begrip",
    "determined_category": "ENT",
    "other_data": "preserved",
}

st.json(test_result)

if st.button("Update to REL"):
    updated = CategoryStateManager.update_generation_result_category(test_result, "REL")
    st.success("Updated!")
    st.json(updated)

if st.button("Get Current Category"):
    category = CategoryStateManager.get_current_category(test_result)
    if category:
        st.info(f"Current: {category.code} - {category.display_name}")
    else:
        st.warning("No category found")

st.markdown("---")

st.markdown("## Test 3: Domain Models")

# Test category creation
code = st.text_input("Category Code", value="ENT")
if st.button("Create Category"):
    category = DefinitionCategory.from_code(code)
    st.json(
        {
            "code": category.code,
            "display_name": category.display_name,
            "reasoning": category.reasoning,
            "confidence": category.confidence,
        }
    )

st.markdown("---")

st.markdown(
    """
## ✅ Test Checklist:

1. **CategoryService v2**:
   - [ ] Update succeeds for valid category
   - [ ] Update fails for invalid category
   - [ ] Update fails for non-existent definition
   - [ ] Audit info is captured (user, reason, timestamp)

2. **CategoryStateManager**:
   - [ ] Updates generation result correctly
   - [ ] Preserves other data
   - [ ] Returns correct category object

3. **Domain Models**:
   - [ ] All category codes map correctly
   - [ ] Unknown codes handled gracefully
"""
)
