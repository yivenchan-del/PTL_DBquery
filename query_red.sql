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



WITH target_chute AS (
    SELECT
        c.id          AS chute_id,
        c.name        AS chute_name,
        c.physicalIdx AS physical_idx,
        c.orderNo     AS order_no,
        c.orderNum    AS order_num,
        c.led         AS led
    FROM wcs_sow_wall_chute c
    WHERE c.led = :led
    ORDER BY c.id ASC
),
matched_pac AS (
    SELECT
        tc.chute_id,
        p.id            AS pac_id,
        p.chuteName     AS pac_chute_name,
        p.physicalChute AS physical_chute,
        p.status        AS pac_status,
        p.barcode       AS barcode,
        p.release       AS is_release,
        p.releaseAt     AS releaseAt,
        p.detail        AS detail,
        ROW_NUMBER() OVER (
            PARTITION BY tc.chute_id
            ORDER BY p.id ASC
        ) AS rn
    FROM target_chute tc
    JOIN wcs_pac_info p
        ON TRIM(COALESCE(tc.order_no, '')) != ''
       AND p.detail IS NOT NULL
       AND INSTR(p.detail, TRIM(CAST(tc.order_no AS TEXT))) > 0
)
SELECT
    tc.chute_id,
    tc.chute_name,
    tc.physical_idx,
    tc.order_no,
    tc.order_num,
    tc.led,
    mp.pac_id,
    mp.pac_chute_name,
    mp.physical_chute,
    mp.pac_status,
    mp.barcode,
    mp.is_release,
    mp.releaseAt,
    mp.detail
FROM target_chute tc
LEFT JOIN matched_pac mp
    ON tc.chute_id = mp.chute_id
   AND mp.rn = 1
ORDER BY tc.chute_id ASC;
