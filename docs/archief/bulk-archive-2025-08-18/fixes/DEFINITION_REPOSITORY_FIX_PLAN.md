# DefinitionRepository Fix Plan

**Component**: `src/database/definitie_repository.py`
**Priority**: URGENT - Blokkeert voorbeelden functionaliteit
**Estimated Time**: 4-8 uur
**Risk**: LOW - Fixes zijn straightforward

## Problem Summary

9 instances van incorrect connection management in 4 methodes maken alle voorbeelden functionaliteit onbruikbaar.

## Fix Strategy

### Pattern to Fix

**FOUT (huidige code):**
```python
cursor = self.conn.cursor()  # self.conn bestaat niet!
# ... operations ...
self.conn.commit()
self.conn.rollback()
```

**CORRECT (nieuwe pattern):**
```python
with self._get_connection() as conn:
    cursor = conn.cursor()
    # ... operations ...
    conn.commit()  # Binnen try block
```

## Detailed Fix Plan

### 1. save_voorbeelden (Regels 924-1004)

**Huidige problemen:**
- Regel 948: `cursor = self.conn.cursor()`
- Regel 997: `self.conn.commit()`
- Regel 1002: `self.conn.rollback()`

**Fix:**
```python
def save_voorbeelden(
    self,
    definitie_id: int,
    voorbeelden_dict: Dict[str, List[str]],
    generation_model: str = "gpt-4",
    generation_params: Dict[str, Any] = None,
    gegenereerd_door: str = "system"
) -> List[int]:
    """Sla voorbeelden op voor een definitie."""
    logger.info(f"Saving voorbeelden voor definitie {definitie_id}")

    with self._get_connection() as conn:
        try:
            cursor = conn.cursor()
            saved_ids = []

            # Verwijder bestaande voorbeelden
            cursor.execute("""
                UPDATE definitie_voorbeelden
                SET actief = FALSE
                WHERE definitie_id = ? AND actief = TRUE
            """, (definitie_id,))

            # Voeg nieuwe voorbeelden toe
            for voorbeeld_type, examples in voorbeelden_dict.items():
                if not examples:
                    continue

                for idx, voorbeeld_tekst in enumerate(examples, 1):
                    if not voorbeeld_tekst.strip():
                        continue

                    record = VoorbeeldenRecord(
                        definitie_id=definitie_id,
                        voorbeeld_type=voorbeeld_type,
                        voorbeeld_tekst=voorbeeld_tekst.strip(),
                        voorbeeld_volgorde=idx,
                        gegenereerd_door=gegenereerd_door,
                        generation_model=generation_model,
                        actief=True
                    )

                    if generation_params:
                        record.set_generation_parameters(generation_params)

                    cursor.execute("""
                        INSERT INTO definitie_voorbeelden (
                            definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, generation_model, generation_parameters, actief
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.definitie_id, record.voorbeeld_type, record.voorbeeld_tekst,
                        record.voorbeeld_volgorde, record.gegenereerd_door,
                        record.generation_model, record.generation_parameters, record.actief
                    ))

                    saved_ids.append(cursor.lastrowid)
                    logger.debug(f"Saved {voorbeeld_type} voorbeeld {idx}: {voorbeeld_tekst[:50]}...")

            conn.commit()
            logger.info(f"Successfully saved {len(saved_ids)} voorbeelden")
            return saved_ids

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save voorbeelden: {e}")
            raise
```

### 2. get_voorbeelden (Regels 1006-1068)

**Huidige probleem:**
- Regel 1023: `cursor = self.conn.cursor()`

**Fix:**
```python
def get_voorbeelden(
    self,
    definitie_id: int,
    voorbeeld_type: str = None,
    actief_only: bool = True
) -> List[VoorbeeldenRecord]:
    """Haal voorbeelden op voor een definitie."""
    with self._get_connection() as conn:
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT * FROM definitie_voorbeelden
            WHERE definitie_id = ?
        """
        params = [definitie_id]

        if voorbeeld_type:
            query += " AND voorbeeld_type = ?"
            params.append(voorbeeld_type)

        if actief_only:
            query += " AND actief = TRUE"

        query += " ORDER BY voorbeeld_type, voorbeeld_volgorde"

        # Execute and fetch
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to VoorbeeldenRecord objects
        voorbeelden = []
        for row in rows:
            record = VoorbeeldenRecord(
                id=row['id'],
                definitie_id=row['definitie_id'],
                voorbeeld_type=row['voorbeeld_type'],
                voorbeeld_tekst=row['voorbeeld_tekst'],
                voorbeeld_volgorde=row['voorbeeld_volgorde'],
                gegenereerd_door=row['gegenereerd_door'],
                generation_model=row['generation_model'],
                generation_parameters=row['generation_parameters'],
                actief=bool(row['actief']),
                beoordeeld=bool(row['beoordeeld']),
                beoordeeling=row['beoordeeling'],
                beoordeeling_notities=row['beoordeeling_notities'],
                beoordeeld_door=row['beoordeeld_door']
            )

            # Parse timestamps
            if row['beoordeeld_op']:
                record.beoordeeld_op = datetime.fromisoformat(row['beoordeeld_op'])
            if row['aangemaakt_op']:
                record.aangemaakt_op = datetime.fromisoformat(row['aangemaakt_op'])
            if row['bijgewerkt_op']:
                record.bijgewerkt_op = datetime.fromisoformat(row['bijgewerkt_op'])

            voorbeelden.append(record)

        logger.info(f"Retrieved {len(voorbeelden)} voorbeelden for definitie {definitie_id}")
        return voorbeelden
```

### 3. update_voorbeelden_status (Regels 1105-1134)

**Huidige problemen:**
- Regel 1114: `cursor = self.conn.cursor()`
- Regel 1122: `self.conn.commit()`
- Regel 1132: `self.conn.rollback()`

**Fix:**
```python
def update_voorbeelden_status(
    self,
    voorbeeld_id: int,
    actief: bool = None,
    beoordeeld: bool = None,
    beoordeeling: str = None,
    beoordeeling_notities: str = None,
    beoordeeld_door: str = None
) -> bool:
    """Update status van een voorbeeld."""
    with self._get_connection() as conn:
        try:
            cursor = conn.cursor()

            # Build update query dynamically
            updates = []
            params = []

            if actief is not None:
                updates.append("actief = ?")
                params.append(actief)

            if beoordeeld is not None:
                updates.append("beoordeeld = ?")
                params.append(beoordeeld)

                if beoordeeld:
                    updates.append("beoordeeld_op = ?")
                    params.append(datetime.now())

                    if beoordeeld_door:
                        updates.append("beoordeeld_door = ?")
                        params.append(beoordeeld_door)

            if beoordeeling:
                updates.append("beoordeeling = ?")
                params.append(beoordeeling)

            if beoordeeling_notities is not None:
                updates.append("beoordeeling_notities = ?")
                params.append(beoordeeling_notities)

            if not updates:
                return False

            # Always update timestamp
            updates.append("bijgewerkt_op = ?")
            params.append(datetime.now())

            # Add ID to params
            params.append(voorbeeld_id)

            # Execute update
            query = f"UPDATE definitie_voorbeelden SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            success = cursor.rowcount > 0
            conn.commit()

            logger.info(f"Updated voorbeeld {voorbeeld_id}: {success}")
            return success

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update voorbeeld status: {e}")
            raise
```

### 4. delete_voorbeelden (Regels 1136-1165)

**Huidige problemen:**
- Regel 1147: `cursor = self.conn.cursor()`
- Regel 1161: `self.conn.commit()`

**Fix:**
```python
def delete_voorbeelden(self, definitie_id: int, voorbeeld_type: str = None) -> int:
    """Verwijder voorbeelden voor een definitie."""
    with self._get_connection() as conn:
        cursor = conn.cursor()

        if voorbeeld_type:
            # Delete specific type
            cursor.execute("""
                DELETE FROM definitie_voorbeelden
                WHERE definitie_id = ? AND voorbeeld_type = ?
            """, (definitie_id, voorbeeld_type))
        else:
            # Delete all voorbeelden for definitie
            cursor.execute("""
                DELETE FROM definitie_voorbeelden
                WHERE definitie_id = ?
            """, (definitie_id,))

        deleted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Deleted {deleted_count} voorbeelden voor definitie {definitie_id}")
        return deleted_count
```

## Test Plan

### Unit Tests
```python
def test_save_voorbeelden_with_connection_fix():
    """Test dat save_voorbeelden werkt na connection fix."""
    repo = DefinitieRepository(":memory:")

    # Create test definitie
    record = DefinitieRecord(begrip="test", definitie="test def", ...)
    def_id = repo.create_definitie(record)

    # Test save voorbeelden
    voorbeelden = {
        'sentence': ['Voorbeeld zin 1', 'Voorbeeld zin 2'],
        'practical': ['Praktisch voorbeeld']
    }

    saved_ids = repo.save_voorbeelden(def_id, voorbeelden)
    assert len(saved_ids) == 3

    # Verify saved
    retrieved = repo.get_voorbeelden(def_id)
    assert len(retrieved) == 3

def test_concurrent_voorbeelden_operations():
    """Test concurrent access voor voorbeelden."""
    # Test met threading om database locks te checken
    pass
```

### Integration Test
```python
def test_complete_voorbeelden_workflow():
    """Test complete voorbeelden lifecycle."""
    repo = DefinitieRepository(":memory:")

    # 1. Create definitie
    # 2. Save voorbeelden
    # 3. Update status
    # 4. Delete some
    # 5. Verify final state
```

## Rollout Plan

1. **Backup current database** (voor zekerheid)
2. **Apply fixes** in volgorde:
   - save_voorbeelden
   - get_voorbeelden
   - update_voorbeelden_status
   - delete_voorbeelden
3. **Run unit tests** per methode
4. **Run integration tests**
5. **Test in staging** environment
6. **Deploy to production**

## Success Criteria

- [ ] Alle 9 connection bugs gefixt
- [ ] Unit tests voor alle 4 methodes
- [ ] Integration test voor complete workflow
- [ ] Geen AttributeError meer bij voorbeelden operations
- [ ] Performance vergelijkbaar met andere CRUD operations

## Risks & Mitigation

**Risk**: Database locks bij concurrent access
**Mitigation**: WAL mode al enabled, retry logic toevoegen

**Risk**: Data loss tijdens fix
**Mitigation**: Backup maken, fixes eerst in test environment

## Next Steps

Na deze fixes:
1. Implementeer connection pooling
2. Add query result caching
3. Monitor performance metrics
4. Consider async support
