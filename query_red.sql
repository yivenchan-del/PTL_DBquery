SELECT
    c.id              AS chute_id,
    c.name            AS chute_name,
    c.physicalIdx     AS physical_idx,
    c.orderNo         AS order_no,
    c.orderNum        AS order_num,
    c.led             AS led,
    (
        SELECT p.id
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS pac_id,
    (
        SELECT p.chuteName
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS pac_chute_name,
    (
        SELECT p.physicalChute
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS physical_chute,
    (
        SELECT p.status
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS pac_status,
    (
        SELECT p.barcode
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS barcode,
    (
        SELECT p.release
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS is_release,
    (
        SELECT p.releaseAt
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS releaseAt,
    (
        SELECT p.detail
        FROM wcs_pac_info p
        WHERE TRIM(COALESCE(c.orderNo, '')) != ''
          AND p.detail IS NOT NULL
          AND INSTR(p.detail, TRIM(CAST(c.orderNo AS TEXT))) > 0
        ORDER BY p.id ASC
        LIMIT 1
    )                 AS detail
FROM wcs_sow_wall_chute c
WHERE c.led = 'yellow'
ORDER BY c.id ASC;
