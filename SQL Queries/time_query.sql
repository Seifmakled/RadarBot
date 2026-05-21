-- Time Queries — radar_logs
-- RadarBot | Seif Makled & Antoni Mikhael

-- All readings from a specific date
SELECT * FROM radar_logs
WHERE DATE(timestamp) = '2026-05-21';

-- All readings within a time window today
SELECT * FROM radar_logs
WHERE TIME(timestamp) BETWEEN '14:00:00' AND '15:00:00';

-- All readings from the last hour
SELECT * FROM radar_logs
WHERE timestamp > datetime('now', '-1 hours');

-- All readings from the last 24 hours
SELECT * FROM radar_logs
WHERE timestamp > datetime('now', '-1 days');

-- Reading count per minute (activity over time)
SELECT
    strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
    COUNT(*) AS readings
FROM radar_logs
GROUP BY minute
ORDER BY minute DESC;

-- Most recent 50 readings
SELECT * FROM radar_logs
ORDER BY timestamp DESC
LIMIT 50;
