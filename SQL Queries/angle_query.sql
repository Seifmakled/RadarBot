-- Angle Queries — radar_logs
-- RadarBot | Seif Makled & Antoni Mikhael

-- All readings at a specific angle
SELECT * FROM radar_logs
WHERE angle = 90;

-- All readings in the left sweep zone (15–89°)
SELECT * FROM radar_logs
WHERE angle BETWEEN 15 AND 89;

-- All readings in the right sweep zone (91–165°)
SELECT * FROM radar_logs
WHERE angle BETWEEN 91 AND 165;

-- Average distance detected per angle (useful for mapping)
SELECT angle, ROUND(AVG(distance), 1) AS avg_distance, COUNT(*) AS readings
FROM radar_logs
WHERE distance > 0
GROUP BY angle
ORDER BY angle;
