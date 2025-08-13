DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  hash TEXT NOT NULL
);

CREATE TABLE project (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  link TEXT,
  image TEXT,
  name TEXT NOT NULL,
  which_craft TEXT NOT NULL,
  desc_small TEXT,
  notes TEXT,
  hook_needle_size INTEGER,
  yarn_weight TEXT,
  status TEXT,
  progress INTEGER,
  start_date TEXT,
  completed INTEGER,
  FOREIGN KEY (user_id) REFERENCES user (id)
);