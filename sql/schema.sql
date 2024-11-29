-- Schema for mReviews
CREATE TABLE IF NOT EXISTS mReviews (
    id INTEGER PRIMARY KEY,
    user TEXT,
    stars INTEGER,
    comment TEXT,
    movieID INTEGER,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
);

-- Schema for users
CREATE TABLE IF NOT EXISTS users (
    userID INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    dob DATE,
    password TEXT
);

-- Schema for movies
CREATE TABLE IF NOT EXISTS movies (
    movieID INTEGER PRIMARY KEY,
    movieName TEXT,
    genre TEXT,
    year INTEGER,
    rating TEXT
);

-- Schema for gReviews
CREATE TABLE IF NOT EXISTS gReviews (
    id INTEGER PRIMARY KEY,
    user TEXT,
    stars INTEGER,
    comment TEXT,
    gameID INTEGER,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
);

-- Schema for games
CREATE TABLE IF NOT EXISTS games (
    gameID INTEGER PRIMARY KEY,
    gameName TEXT,
    genre TEXT,
    year INTEGER,
    rating TEXT
);
