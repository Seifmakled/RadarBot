-- Buzzer Queries — radar_logs
-- RadarBot | Seif Makled & Antoni Mikhael

-- All readings where buzzer was ON (object < 30 cm)
SELECT * FROM radar_logs
WHERE buzzer_active = 1;

-- All readings where buzzer was OFF
SELECT * FROM radar_logs
WHERE buzzer_active = 0;

-- Total number of alarm events
SELECT COUNT(*) AS total_alarms
FROM radar_logs
WHERE buzzer_active = 1;

-- Alarm events grouped by angle (which direction triggers most)
SELECT angle, COUNT(*) AS alarm_count
FROM radar_logs
WHERE buzzer_active = 1
GROUP BY angle
ORDER BY alarm_count DESC;

-- Closest recorded distance during an alarm
SELECT MIN(distance) AS closest_cm
FROM radar_logs
WHERE buzzer_active = 1 AND distance > 0;
