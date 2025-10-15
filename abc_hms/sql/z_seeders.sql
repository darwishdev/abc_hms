CALL seed_dim_date(20250807 , 20301231 , 'FRI_SAT' , '+00:03');

INSERT INTO room_date_lookup (lookup_type, lookup_key, lookup_value) VALUES
  ('house_keeping_status', 'Vacant', 0),
  ('house_keeping_status', 'OCC', 1),
  ('service_status', 'No Status', 0),
  ('service_status', 'Make Up', 1),
  ('service_status', 'DND', 2),
  ('room_status', 'Dirty', 0),
  ('room_status', 'Clean', 1),
  ('room_status', 'Inspected', 2),
  ('ooo_status', 'In Order', 0),
  ('ooo_status', 'OOS', 1),
  ('ooo_status', 'OOO', 2)
  ON DUPLICATE KEY UPDATE
  lookup_value = VALUES(lookup_value);
