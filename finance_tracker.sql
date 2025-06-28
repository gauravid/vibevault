CREATE DATABASE IF NOT EXISTS finance_tracker;
USE finance_tracker;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10,2),
    category VARCHAR(50),
    date DATE,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS budgets;

CREATE TABLE budgets (
    user_id INT PRIMARY KEY,
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
