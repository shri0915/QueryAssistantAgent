-- Sample Library Management System Schema
-- This is an example schema for a library database

-- Authors table
CREATE TABLE authors (
    author_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    biography TEXT,
    birth_date DATE,
    nationality VARCHAR(50)
);

-- Books table
CREATE TABLE books (
    book_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    publication_year INT,
    publisher VARCHAR(100),
    genre VARCHAR(50),
    language VARCHAR(30),
    pages INT,
    description TEXT,
    available_copies INT DEFAULT 0,
    total_copies INT DEFAULT 0
);

-- Book Authors relationship (many-to-many)
CREATE TABLE book_authors (
    book_id INT,
    author_id INT,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

-- Members table
CREATE TABLE members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(255),
    membership_date DATE NOT NULL,
    membership_type VARCHAR(20) DEFAULT 'standard',
    status VARCHAR(20) DEFAULT 'active'
);

-- Loans table
CREATE TABLE loans (
    loan_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    loan_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    fine_amount DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- Reservations table
CREATE TABLE reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    reservation_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    expiry_date DATE,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- Staff table
CREATE TABLE staff (
    staff_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(50),
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2)
);
