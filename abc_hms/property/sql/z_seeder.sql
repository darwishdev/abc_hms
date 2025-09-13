INSERT INTO inventory_lookup (lookup_type, lookup_key, lookup_value) VALUES
  ('hk_status', 'Vacant', 0),
  ('hk_status', 'OCC', 1),
  ('service_status', 'No Status', 0),
  ('service_status', 'Make Up', 1),
  ('service_status', 'DND', 2),
  ('room_status', 'Dirty', 0),
  ('room_status', 'Clean', 1),
  ('room_status', 'Inspected', 2),
  ('ooo_status', 'In Order', 0),
  ('ooo_status', 'OOS', 1),
  ('ooo_status', 'OOO', 2),
  ('physical_status', 'Vacant', 0),
  ('physical_status', 'OCC', 1)
  ON DUPLICATE KEY UPDATE
  lookup_value = VALUES(lookup_value);
