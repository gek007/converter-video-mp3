-- Create the database
CREATE DATABASE IF NOT EXISTS auth;

-- Use the database
USE auth;

-- Create user if not exists
CREATE USER IF NOT EXISTS 'auth_user'@'%' IDENTIFIED BY 'Auth123';
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'%';
FLUSH PRIVILEGES;

-- Create the user table
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Insert default user (note: in production, passwords should be hashed)
INSERT INTO user (email, password) VALUES 
('kshilkrot@email.com', 'Admin123')
ON DUPLICATE KEY UPDATE password = 'Admin123';
