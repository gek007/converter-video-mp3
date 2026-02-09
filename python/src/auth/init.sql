-- Create the database
CREATE DATABASE IF NOT EXISTS auth;

-- Use the database
USE auth;

GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';

-- Create the USER table
CREATE TABLE IF NOT EXISTS USER (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Insert the user (note: in production, you should hash passwords)
INSERT INTO USER (email, password) VALUES 
('kshilkrot@email.com', 'Admin123');
