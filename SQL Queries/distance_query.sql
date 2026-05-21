-- Distance Queries — radar_logs
-- RadarBot | Seif Makled & Antoni Mikhael

-- All readings where an object was detected within 30 cm
SELECT * FROM radar_logs
WHERE distance > 0 AND distance < 30;

-- All readings where an object was detected within 100 cm
SELECT * FROM radar_logs
WHERE distance > 0 AND distance < 100;

-- All out-of-range readings (no echo)
SELECT * FROM radar_logs
WHERE distance = -1;

-- Minimum, maximum and average detected distance
SELECT
    MIN(distance) AS min_cm,
    MAX(distance) AS max_cm,
    ROUND(AVG(distance), 1) AS avg_cm
FROM radar_logs
WHERE distance > 0;

-- Distribution: count of readings per 10 cm band
SELECT
    (distance / 10) * 10 AS band_start,
    (distance / 10) * 10 + 9 AS band_end,
    COUNT(*) AS count
FROM radar_logs
WHERE distance > 0
GROUP BY band_start
ORDER BY band_start;
