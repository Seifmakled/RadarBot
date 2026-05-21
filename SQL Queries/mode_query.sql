-- Mode Queries — radar_logs
-- RadarBot | Seif Makled & Antoni Mikhael

-- All readings in automatic sweep mode
SELECT * FROM radar_logs
WHERE mode = 0;

-- All readings in manual joystick mode
SELECT * FROM radar_logs
WHERE mode = 1;

-- How long each mode was used (reading count as proxy for time)
SELECT
    CASE mode WHEN 0 THEN 'Automatic' ELSE 'Manual' END AS mode_name,
    COUNT(*) AS reading_count
FROM radar_logs
GROUP BY mode;

-- Detections (buzzer ON) split by mode
SELECT
    CASE mode WHEN 0 THEN 'Automatic' ELSE 'Manual' END AS mode_name,
    COUNT(*) AS alarms
FROM radar_logs
WHERE buzzer_active = 1
GROUP BY mode;
