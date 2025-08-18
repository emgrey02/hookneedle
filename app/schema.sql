DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS note;
DROP TABLE IF EXISTS profile;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER,
  username TEXT UNIQUE NOT NULL,
  hash TEXT NOT NULL,
  visibility INTEGER,
  FOREIGN KEY (profile_id) REFERENCES profile (id)
);

CREATE TABLE project (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  note_id INTEGER,
  link TEXT,
  image_filename TEXT,
  image_data TEXT,
  image_mimetype TEXT,
  name TEXT NOT NULL UNIQUE,
  which_craft TEXT NOT NULL,
  desc_small TEXT,
  hook_needle_size INTEGER,
  yarn_weight TEXT,
  status TEXT,
  progress INTEGER,
  start_date TEXT,
  completed INTEGER,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (note_id) REFERENCES note (id)
);

CREATE TABLE note (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  project_id INTEGER NOT NULL UNIQUE,
  the_note TEXT, 
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE profile (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  image_filename TEXT,
  image_data TEXT,
  image_mimetype TEXT,
  bio TEXT,
  friends TEXT,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE friendship (
  user1_id INTEGER,
  user2_id INTEGER,
  created TEXT NOT NULL,
  FOREIGN KEY (user1_id) REFERENCES user (id),
  FOREIGN KEY (user2_id) REFERENCES user (id)
);